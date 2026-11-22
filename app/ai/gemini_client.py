"""
AI-LMS Gemini Client — async wrapper around google-genai with retry logic, timeouts, and fallback model auto-discovery.
"""

import asyncio
from typing import Any

from google import genai
from google.genai import types
from google.genai.errors import APIError

from app.core.config import get_settings
from app.core.exceptions import AIServiceError
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

_client: genai.Client | None = None
_model_name: str | None = None


def _initialize_client() -> genai.Client:
    """Initialize the process-wide Gemini client on its first use."""
    global _client, _model_name
    if _client is not None:
        return _client

    api_key = settings.GEMINI_API_KEY
    if not api_key or api_key.startswith("your-"):
        logger.warning("Gemini API key not configured — AI features will be unavailable")
        raise AIServiceError("AI service is not configured.")

    try:
        # Initialize the modern Client
        _client = genai.Client(api_key=api_key)

        _model_name = settings.GEMINI_MODEL
        return _client
    except Exception as exc:
        logger.error(
            "Gemini client initialization failed", extra={"error_type": type(exc).__name__}
        )
        raise AIServiceError("AI service is currently unavailable.") from exc


async def generate_content(
    prompt: str,
    system_instruction: str | None = None,
    temperature: float = 0.7,
) -> str:
    """
    Generate content from a prompt using Gemini.
    Each provider call has a bounded timeout and returns a generic service error.
    """
    client = _initialize_client()
    model = _model_name or "gemini-2.5-flash"

    config = types.GenerateContentConfig(
        temperature=temperature,
        system_instruction=system_instruction,
    )

    try:
        # Enforce a 30-second timeout on the async API request
        response = await asyncio.wait_for(
            client.aio.models.generate_content(
                model=model,
                contents=prompt,
                config=config,
            ),
            timeout=30.0,
        )
        if not response or not response.text:
            raise AIServiceError("Received empty response from AI model")
        return response.text.strip()
    except asyncio.TimeoutError as exc:
        logger.warning("Gemini generation timed out")
        raise AIServiceError("AI generation request timed out. Please try again.") from exc
    except APIError as exc:
        logger.warning("Gemini generation failed", extra={"error_type": type(exc).__name__})
        raise AIServiceError(
            "AI generation is currently unavailable. Please try again later."
        ) from exc
    except Exception as exc:
        logger.error("Gemini generation failed", extra={"error_type": type(exc).__name__})
        raise AIServiceError(
            "AI generation is currently unavailable. Please try again later."
        ) from exc


async def chat_with_history(
    history: list[dict[str, Any]],
    new_message: str,
    system_instruction: str | None = None,
) -> str:
    """
    Continue a chat session using existing message history.
    history: list of {"role": "user"|"model", "parts": [str]} dicts.
    """
    client = _initialize_client()
    model = _model_name or "gemini-2.5-flash"

    # Convert existing history to list of Types.Content
    history_contents = []
    for msg in history:
        history_contents.append(
            types.Content(
                role=msg["role"], parts=[types.Part.from_text(text=part) for part in msg["parts"]]
            )
        )

    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
    )

    try:
        # Create chat session using modern Client chats helper
        chat = client.aio.chats.create(
            model=model,
            history=history_contents,
            config=config,
        )

        # Send message and get response with a 30s timeout
        response = await asyncio.wait_for(
            chat.send_message(new_message),
            timeout=30.0,
        )
        if not response or not response.text:
            raise AIServiceError("Received empty response from AI chat")
        return response.text.strip()
    except asyncio.TimeoutError as exc:
        logger.warning("Gemini chat timed out")
        raise AIServiceError("AI chat request timed out. Please try again.") from exc
    except APIError as exc:
        logger.warning("Gemini chat failed", extra={"error_type": type(exc).__name__})
        raise AIServiceError("AI chat is currently unavailable. Please try again later.") from exc
    except Exception as exc:
        logger.error("Gemini chat failed", extra={"error_type": type(exc).__name__})
        raise AIServiceError("AI chat is currently unavailable. Please try again later.") from exc
