from fastapi import APIRouter, Body

from app.dependencies import current_user
from app.models import User
from app.services import ai_service

router = APIRouter()


@router.post("/explain")
async def explain(
    question: str = Body(..., embed=True),
    user: current_user = None,
):
    return {"explanation": await ai_service.generate_explanation(question)}


@router.post("/quiz-generator")
async def quiz_generator(
    topic: str = Body(..., embed=True),
    count: int = Body(5, ge=1, le=20),
    user: current_user = None,
):
    return {"questions": await ai_service.generate_quiz_questions(topic, count)}


@router.post("/summarize")
async def summarize(
    text: str = Body(..., embed=True),
    user: current_user = None,
):
    return {"summary": await ai_service.summarize_notes(text)}
