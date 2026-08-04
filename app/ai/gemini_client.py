"""
AI-LMS Gemini Client — async wrapper around google-genai with retry logic, timeouts, and fallback model auto-discovery.
"""
import asyncio
from typing import Any

from google import genai
from google.genai import types
from google.genai.errors import APIError
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.core.exceptions import AIServiceError
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

_client: genai.Client | None = None
_model_name: str | None = None


def _initialize_client() -> genai.Client:
    """Initialize Gemini client and auto-discover a compatible model if needed."""
    global _client, _model_name
    if _client is not None:
        return _client

    api_key = settings.GEMINI_API_KEY
    if not api_key or api_key.startswith("your-"):
        logger.warning("Gemini API key not configured — AI features will be unavailable")
        raise AIServiceError("AI service not configured. Set GEMINI_API_KEY in your .env")

    try:
        # Initialize the modern Client
        _client = genai.Client(api_key=api_key)

        # Retrieve configured model (e.g. gemini-1.5-flash)
        configured_model = settings.GEMINI_MODEL or "gemini-2.5-flash"
        model_short = configured_model.split("/")[-1] if "/" in configured_model else configured_model

        # Discover available models to check if configured one is supported
        available_models = []
        try:
            for m in _client.models.list():
                available_models.append(m.name)
        except Exception as list_exc:
            logger.warning(f"Failed to list models from Gemini API: {list_exc}")

        # Check if the configured model is supported in the listed models
        full_configured_name = f"models/{model_short}"
        if full_configured_name in available_models or model_short in available_models:
            _model_name = model_short
        else:
            # Auto-discover a compatible model
            discovered = None
            for m_name in available_models:
                if "flash" in m_name and "embed" not in m_name and "live" not in m_name:
                    discovered = m_name.split("/")[-1]
                    break

            if discovered:
                _model_name = discovered
                logger.info(f"Configured model {configured_model} is unavailable. Auto-discovered: {_model_name}")
            else:
                _model_name = "gemini-2.5-flash"
                logger.warning(f"Configured model {configured_model} is unavailable. Falling back to default: {_model_name}")

        return _client
    except Exception as exc:
        logger.error(f"Failed to initialize Gemini client: {exc}", exc_info=True)
        raise AIServiceError(f"AI service initialization failed: {exc}") from exc


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
async def generate_content(
    prompt: str,
    system_instruction: str | None = None,
    temperature: float = 0.7,
) -> str:
    """
    Generate content from a prompt using Gemini.
    Retries up to 3 times with exponential backoff.
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
        logger.error("Gemini generation timed out", exc_info=True)
        raise AIServiceError("AI generation request timed out. Please try again.") from exc
    except APIError as exc:
        logger.error(f"Gemini API error during generation: {exc.message}", exc_info=True)
        raise AIServiceError(f"AI generation failed: {exc.message}") from exc
    except Exception as exc:
        logger.error("Unhandled error during Gemini generation", exc_info=True)
        raise AIServiceError(f"AI generation failed: {exc}") from exc


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
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
                role=msg["role"],
                parts=[types.Part.from_text(text=part) for part in msg["parts"]]
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
        logger.error("Gemini chat timed out", exc_info=True)
        raise AIServiceError("AI chat request timed out. Please try again.") from exc
    except APIError as exc:
        logger.error(f"Gemini API error during chat: {exc.message}", exc_info=True)
        raise AIServiceError(f"AI chat failed: {exc.message}") from exc
    except Exception as exc:
        logger.error("Unhandled error during Gemini chat", exc_info=True)
        raise AIServiceError(f"AI chat failed: {exc}") from exc
