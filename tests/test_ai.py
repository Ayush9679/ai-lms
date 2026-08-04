"""
AI-LMS AI Feature Tests — chat, notes, summaries, flashcards, study plans.
Tests gracefully skip if Gemini is not configured.
"""
import pytest
from httpx import AsyncClient

from app.core.config import get_settings

settings = get_settings()
AI_AVAILABLE = bool(
    settings.GEMINI_API_KEY
    and not settings.GEMINI_API_KEY.startswith("your-")
)

skip_if_no_ai = pytest.mark.skipif(
    not AI_AVAILABLE,
    reason="GEMINI_API_KEY not configured — AI tests skipped",
)


async def _register_and_login(client, email, password):
    await client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "AI Test User",
            "email": email,
            "password": password,
            "role": "student",
        },
    )
    r = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    return r.json()["access_token"]


@pytest.mark.asyncio
@skip_if_no_ai
async def test_ai_chat_new_session(client: AsyncClient):
    """AI tutor creates a new chat session and returns a response."""
    token = await _register_and_login(client, "aichat@test.com", "AiChat123!")
    response = await client.post(
        "/api/v1/ai/chat",
        json={"message": "What is Python?"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "ai_response" in data
    assert "session_id" in data
    assert len(data["ai_response"]) > 10
    return data["session_id"]


@pytest.mark.asyncio
@skip_if_no_ai
async def test_ai_chat_continue_session(client: AsyncClient):
    """AI tutor continues an existing conversation."""
    token = await _register_and_login(client, "aichat2@test.com", "AiChat123!")
    headers = {"Authorization": f"Bearer {token}"}

    # Start session
    r1 = await client.post(
        "/api/v1/ai/chat",
        json={"message": "Explain what a variable is."},
        headers=headers,
    )
    assert r1.status_code == 200
    session_id = r1.json()["session_id"]

    # Continue session
    r2 = await client.post(
        "/api/v1/ai/chat",
        json={"message": "Give me an example.", "session_id": session_id},
        headers=headers,
    )
    assert r2.status_code == 200
    assert r2.json()["session_id"] == session_id
    assert r2.json()["message_count"] == 4  # 2 messages × 2 (user + model)


@pytest.mark.asyncio
@skip_if_no_ai
async def test_ai_generate_notes(client: AsyncClient):
    """AI generates structured notes from raw text."""
    token = await _register_and_login(client, "ainotes@test.com", "AiNotes123!")
    response = await client.post(
        "/api/v1/ai/notes/generate",
        json={
            "source_type": "text",
            "source_text": (
                "Python is a high-level, interpreted programming language known for its "
                "simplicity and readability. It supports multiple programming paradigms "
                "including procedural, object-oriented, and functional programming. "
                "Python has a large standard library and an active community."
            ),
            "title": "Python Overview Notes",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert "content" in data
    assert len(data["content"]) > 50
    assert data["title"] == "Python Overview Notes"


@pytest.mark.asyncio
@skip_if_no_ai
async def test_ai_summarize(client: AsyncClient):
    """AI summarizes text and returns key points."""
    token = await _register_and_login(client, "aisum@test.com", "AiSum123!")
    response = await client.post(
        "/api/v1/ai/summarize",
        json={
            "source_type": "text",
            "source_text": (
                "Machine learning is a subset of artificial intelligence that enables "
                "systems to learn from data. Supervised learning uses labeled data. "
                "Unsupervised learning finds patterns in unlabeled data. Reinforcement "
                "learning uses rewards and penalties to guide learning."
            ),
            "length": "short",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "key_points" in data
    assert isinstance(data["key_points"], list)


@pytest.mark.asyncio
@skip_if_no_ai
async def test_ai_generate_flashcards(client: AsyncClient):
    """AI generates flashcards from text."""
    token = await _register_and_login(client, "aiflash@test.com", "AiFlash123!")
    response = await client.post(
        "/api/v1/ai/flashcards/generate",
        json={
            "source_type": "text",
            "source_text": (
                "Photosynthesis is the process by which green plants use sunlight, "
                "water, and carbon dioxide to produce oxygen and energy in the form of sugar. "
                "Chlorophyll is the green pigment that absorbs light. The process occurs in "
                "the chloroplasts of plant cells."
            ),
            "num_cards": 5,
            "title": "Photosynthesis Flashcards",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert "cards" in data
    assert len(data["cards"]) >= 1
    assert "front" in data["cards"][0]
    assert "back" in data["cards"][0]


@pytest.mark.asyncio
@skip_if_no_ai
async def test_ai_study_plan(client: AsyncClient):
    """AI generates a study plan."""
    token = await _register_and_login(client, "aiplan@test.com", "AiPlan123!")
    response = await client.post(
        "/api/v1/ai/study-plan/generate",
        json={
            "topics": ["Python basics", "Functions", "OOP"],
            "duration_weeks": 2,
            "hours_per_day": 1,
            "goals": "Prepare for my first Python interview",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert "plan_data" in data
    assert "title" in data
    assert data["duration_weeks"] == 2


@pytest.mark.asyncio
async def test_ai_endpoints_require_auth(client: AsyncClient):
    """All AI endpoints return 401 without a token."""
    endpoints = [
        ("POST", "/api/v1/ai/chat", {"message": "test"}),
        ("POST", "/api/v1/ai/notes/generate", {"source_type": "text", "source_text": "test"}),
        ("POST", "/api/v1/ai/summarize", {"source_type": "text", "source_text": "test"}),
        ("POST", "/api/v1/ai/flashcards/generate", {"source_type": "text", "source_text": "test", "num_cards": 5}),
        ("GET", "/api/v1/ai/chat/sessions", None),
        ("GET", "/api/v1/ai/recommendations", None),
    ]
    for method, url, body in endpoints:
        if method == "GET":
            response = await client.get(url)
        else:
            response = await client.post(url, json=body)
        assert response.status_code == 401, f"Expected 401 for {method} {url}"


@pytest.mark.asyncio
async def test_chat_sessions_list(client: AsyncClient):
    """Student can list their chat sessions (empty list initially)."""
    token = await _register_and_login(client, "sessions@test.com", "Sessions123!")
    response = await client.get(
        "/api/v1/ai/chat/sessions",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)
