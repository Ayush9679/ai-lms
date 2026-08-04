from fastapi import HTTPException

try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None

from app.config import get_settings

settings = get_settings()


def _client():
    if AsyncOpenAI is None or not settings.OPENAI_API_KEY:
        raise HTTPException(status_code=503, detail="AI service not configured")
    return AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


async def generate_explanation(question: str) -> str:
    client = _client()
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful tutor. Explain concisely and clearly.",
                },
                {"role": "user", "content": question},
            ],
        )
        return response.choices[0].message.content or ""
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI request failed: {exc}") from exc


async def generate_quiz_questions(topic: str, count: int = 5) -> list[dict]:
    client = _client()
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You generate multiple-choice quiz questions in JSON. "
                        "Return an array of objects with keys: question, options (list of 4), "
                        "correct (index), and explanation."
                    ),
                },
                {"role": "user", "content": f"Create {count} questions about: {topic}"},
            ],
            response_format={"type": "json_object"},
        )
        import json

        data = json.loads(response.choices[0].message.content or "{}")
        questions = data.get("questions", [])
        if not questions and isinstance(data, list):
            questions = data
        return questions
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI request failed: {exc}") from exc


async def summarize_notes(text: str) -> str:
    client = _client()
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Summarize the following learning material into key points.",
                },
                {"role": "user", "content": text[:8000]},
            ],
        )
        return response.choices[0].message.content or ""
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI request failed: {exc}") from exc
