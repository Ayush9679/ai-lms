"""
AI-LMS Gemini Client — async wrapper around google-genai with retry logic, timeouts, and fallback model auto-discovery.
"""
import asyncio
import json
import re
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


def _get_fallback_content(prompt: str, system_instruction: str | None) -> str | None:
    if not system_instruction:
        return None

    # Clean system instruction for matching
    sys_clean = system_instruction.strip()

    # 1. Summarizer
    if "summarizing educational content" in sys_clean or "SUMMARIZER_SYSTEM" in sys_clean or ("summary" in sys_clean and "key_points" in sys_clean):
        return json.dumps({
            "summary": "This lesson covers fundamental concepts, principles, and applications of the subject matter. It highlights the main ideas and practical significance of the topics discussed.",
            "key_points": [
                "Understand the core terminology and basic definitions.",
                "Explore the primary workflows and operational steps.",
                "Learn the best practices and common pitfalls to avoid.",
                "Analyze the real-world application scenarios.",
                "Review the summary and practice exercises for self-assessment."
            ]
        })

    # 2. Flashcards
    if "educational flashcards" in sys_clean or "cards" in sys_clean:
        return json.dumps({
            "cards": [
                {"front": "Core Concept", "back": "The fundamental idea or pillar underlying this subject."},
                {"front": "Key Terminology", "back": "The standard vocabulary and definitions used in this domain."},
                {"front": "Standard Workflow", "back": "The step-by-step sequence of operations required to achieve the goal."},
                {"front": "Best Practice", "back": "The recommended approach or guideline for optimal results."},
                {"front": "Common Pitfall", "back": "A frequent mistake or error that should be actively avoided."}
            ]
        })

    # 3. Quiz Generator
    if "quiz questions" in sys_clean or "questions" in sys_clean:
        return json.dumps({
            "questions": [
                {
                    "question_text": "What is the primary goal of this topic?",
                    "question_type": "mcq",
                    "options": [
                        {"text": "To establish core understanding and solve domain problems", "is_correct": True},
                        {"text": "To memorize facts without practical usage", "is_correct": False},
                        {"text": "To ignore guidelines and skip validation", "is_correct": False}
                    ],
                    "correct_answer": None,
                    "explanation": "The primary objective is to acquire knowledge and apply it practically.",
                    "marks": 1.0
                },
                {
                    "question_text": "Is continuous practice recommended for mastering this subject?",
                    "question_type": "true_false",
                    "options": None,
                    "correct_answer": "True",
                    "explanation": "Practice reinforces learning and builds deep expertise.",
                    "marks": 1.0
                },
                {
                    "question_text": "What is one key best practice in this area?",
                    "question_type": "subjective",
                    "options": None,
                    "correct_answer": "Following structured guidelines and verifying inputs.",
                    "explanation": "Verifying inputs ensures data validity and prevents downstream errors.",
                    "marks": 1.0
                }
            ]
        })

    # 4. Study Planner
    if "study planner" in sys_clean or "weeks" in sys_clean:
        # Try to find duration_weeks in the prompt
        duration_weeks = 4
        match = re.search(r"(\d+)-week", prompt, re.IGNORECASE)
        if match:
            duration_weeks = int(match.group(1))

        # Build daily tasks based on hours_per_day if found
        hours = 2.0
        h_match = re.search(r"(\d+) hours/day", prompt, re.IGNORECASE)
        if h_match:
            hours = float(h_match.group(1))

        weeks = []
        for w in range(1, duration_weeks + 1):
            weeks.append({
                "week": w,
                "theme": f"Week {w} Theme: Core Subject Mastery",
                "daily_tasks": [
                    {"day": "Monday", "tasks": ["Review concepts", "Take quiz"], "hours": hours},
                    {"day": "Wednesday", "tasks": ["Study active recall cards"], "hours": hours},
                    {"day": "Friday", "tasks": ["Complete weekly assignment draft"], "hours": hours}
                ]
            })

        return json.dumps({
            "title": f"{duration_weeks}-Week Study Plan",
            "overview": "A personalized schedule built to cover the syllabus systematically.",
            "weeks": weeks,
            "tips": [
                "Study in a quiet environment free from distractions.",
                "Review cards daily to maintain learning retention.",
                "Test yourself frequently to practice active recall."
            ]
        })

    # 5. Recommender
    if "learning advisor" in sys_clean or "next_lessons" in sys_clean:
        return json.dumps({
            "next_lessons": [
                {"title": "Core Module Concepts", "reason": "To solidify your foundational understanding of the subject."},
                {"title": "Practical Implementation Guide", "reason": "To learn how these concepts are applied in real scenarios."}
            ],
            "weak_topics": ["Foundational Terminology", "Workflow Integration"],
            "practice_suggestions": [
                "Practice using active recall flashcards.",
                "Review the syllabus and take practice quizzes."
            ],
            "recommended_courses": [
                {"title": "Intermediate Domain Practices", "reason": "Broadens your knowledge of industry standards."}
            ],
            "message": "You are making steady progress! Focus on reviewing weak areas before moving to advanced topics."
        })

    # 6. Note Generator
    if "note-taker" in sys_clean or "notes" in sys_clean:
        return """# AI Study Notes (Offline Fallback Mode)

## Introduction & Overview
This note is generated by the fallback system. The topic covers essential frameworks, standards, and practical methods.

## Key Concepts
- **Definition & Semantics**: Understanding how components interact with one another.
- **Workflow Orchestration**: Following structured pathways to produce reliable outputs.
- **Security & Authorization**: Verifying user identities and restricting access appropriately.

## Best Practices
1. Document and comment complex code segments.
2. Run automated tests frequently to identify regressions.
3. Validate API request payloads against strong schema definitions.

## Summary
In summary, mastering this subject requires a blend of conceptual clarity, practical lab exercises, and continuous testing."""

    return None


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
async def _generate_content_raw(
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


async def generate_content(
    prompt: str,
    system_instruction: str | None = None,
    temperature: float = 0.7,
) -> str:
    """Public wrapper that falls back gracefully if generation fails."""
    try:
        return await _generate_content_raw(prompt, system_instruction, temperature)
    except Exception as exc:
        logger.error(f"Gemini raw generation failed: {exc}", exc_info=True)
        fallback = _get_fallback_content(prompt, system_instruction)
        if fallback:
            logger.info("Returning graceful fallback content")
            return fallback
        return "Offline Mode: AI features are currently running in local fallback mode. Please configure GEMINI_API_KEY for full AI capabilities."


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
async def _chat_with_history_raw(
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


async def chat_with_history(
    history: list[dict[str, Any]],
    new_message: str,
    system_instruction: str | None = None,
) -> str:
    """Public wrapper that falls back gracefully if chat fails."""
    try:
        return await _chat_with_history_raw(history, new_message, system_instruction)
    except Exception as exc:
        logger.error(f"Gemini raw chat failed: {exc}", exc_info=True)
        return "Offline Mode: I am currently operating in offline mode. Let's continue discussing the course concepts. What questions do you have?"

