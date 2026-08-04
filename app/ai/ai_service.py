"""
AI-LMS AI Service — all AI-powered features using Gemini.
Features: tutor chat, notes, summarization, quiz generation, flashcards, study planner, recommendations.
"""
import json
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.gemini_client import chat_with_history, generate_content
from app.core.exceptions import AIServiceError, NotFoundError
from app.core.logging import get_logger
from app.models.ai_chat import AIChatMessage, AIChatSession, FlashcardSet, GeneratedNote, StudyPlan
from app.models.quiz import DifficultyLevel, QuestionType
from app.repositories.ai_repo import (
    ChatMessageRepository,
    ChatSessionRepository,
    FlashcardSetRepository,
    GeneratedNoteRepository,
    StudyPlanRepository,
)
from app.repositories.course_repo import CourseRepository
from app.repositories.lesson_repo import LessonRepository
from app.repositories.quiz_repo import QuizRepository

logger = get_logger(__name__)

# =============================================================================
# System Instructions
# =============================================================================

AI_TUTOR_SYSTEM = """You are an expert AI tutor for an online learning platform called AI-LMS.
Your role is to:
- Answer student questions clearly and accurately
- Explain complex concepts in simple terms with examples
- Encourage deeper understanding, not just memorization
- Adapt your explanations to the student's apparent level
- Use structured formatting (headings, bullet points, code blocks where relevant)
- Be encouraging and supportive
Always be factual. If you don't know something, say so."""

NOTE_GENERATOR_SYSTEM = """You are an expert educator and note-taker.
Generate well-structured, comprehensive study notes from the provided content.
Format with:
- Clear headings and subheadings
- Key concepts highlighted
- Bullet points for lists
- Examples where helpful
- A brief summary at the end
Be thorough but concise."""

SUMMARIZER_SYSTEM = """You are an expert at summarizing educational content.
Create clear, accurate summaries that capture the essential ideas.
Format your response as JSON with keys: "summary" (string) and "key_points" (list of strings)."""

QUIZ_GENERATOR_SYSTEM = """You are an expert quiz creator for educational content.
Generate quiz questions in strict JSON format.
Return ONLY valid JSON, no markdown, no explanation.
Format: {"questions": [{"question_text": str, "question_type": "mcq"|"true_false"|"subjective", "options": [{"text": str, "is_correct": bool}]|null, "correct_answer": str|null, "explanation": str, "marks": float}]}"""

FLASHCARD_SYSTEM = """You are an expert at creating educational flashcards.
Create concise, memorable flashcards for studying.
Return ONLY valid JSON: {"cards": [{"front": str, "back": str}]}"""

STUDY_PLANNER_SYSTEM = """You are an expert academic coach and study planner.
Create personalized, realistic study plans.
Return ONLY valid JSON: {"title": str, "overview": str, "weeks": [{"week": int, "theme": str, "daily_tasks": [{"day": str, "tasks": [str], "hours": float}]}], "tips": [str]}"""

RECOMMENDER_SYSTEM = """You are an AI learning advisor.
Analyze student progress and provide actionable recommendations.
Return ONLY valid JSON: {"next_lessons": [{"title": str, "reason": str}], "weak_topics": [str], "practice_suggestions": [str], "recommended_courses": [{"title": str, "reason": str}], "message": str}"""


class AIService:
    """
    Central AI service. All methods are async.
    Dependencies (repositories) are injected via constructor.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.session_repo = ChatSessionRepository(db)
        self.message_repo = ChatMessageRepository(db)
        self.note_repo = GeneratedNoteRepository(db)
        self.plan_repo = StudyPlanRepository(db)
        self.flashcard_repo = FlashcardSetRepository(db)
        self.course_repo = CourseRepository(db)
        self.lesson_repo = LessonRepository(db)
        self.quiz_repo = QuizRepository(db)

    # =========================================================================
    # AI Tutor Chat
    # =========================================================================

    async def chat(
        self,
        user_id: uuid.UUID,
        message: str,
        session_id: uuid.UUID | None = None,
        course_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        """Send a message to the AI tutor and persist the conversation."""
        # Get or create chat session
        if session_id:
            session = await self.session_repo.get_by_id(session_id)
            if not session or session.user_id != user_id:
                raise NotFoundError("Chat session", str(session_id))
        else:
            session = await self.session_repo.create(
                user_id=user_id,
                course_id=course_id,
                title=message[:60] + ("..." if len(message) > 60 else ""),
                message_count=0,
            )

        # Build context for Gemini
        existing_messages = await self.message_repo.get_by_session(session.id)
        history = [
            {"role": msg.role, "parts": [msg.content]}
            for msg in existing_messages
        ]

        # Add course context to system instruction
        system = AI_TUTOR_SYSTEM
        if course_id:
            course = await self.course_repo.get_by_id(course_id)
            if course:
                system += f"\n\nCurrent course context: {course.title}. {course.description or ''}"

        # Generate AI response
        ai_response = await chat_with_history(history, message, system_instruction=system)

        # Persist user message
        await self.message_repo.create(
            session_id=session.id,
            role="user",
            content=message,
        )
        # Persist AI response
        await self.message_repo.create(
            session_id=session.id,
            role="model",
            content=ai_response,
        )

        # Update session message count
        new_count = session.message_count + 2
        await self.session_repo.update(session, message_count=new_count)

        return {
            "session_id": session.id,
            "session_title": session.title,
            "user_message": message,
            "ai_response": ai_response,
            "message_count": new_count,
        }

    async def get_chat_sessions(
        self, user_id: uuid.UUID, skip: int = 0, limit: int = 20
    ) -> list[AIChatSession]:
        return await self.session_repo.get_by_user(user_id, skip, limit)

    async def get_chat_history(
        self, user_id: uuid.UUID, session_id: uuid.UUID
    ) -> dict[str, Any]:
        session = await self.session_repo.get_by_id(session_id)
        if not session or session.user_id != user_id:
            raise NotFoundError("Chat session", str(session_id))
        messages = await self.message_repo.get_by_session(session_id)
        return {
            "id": session.id,
            "title": session.title,
            "message_count": session.message_count,
            "messages": [
                {"role": m.role, "content": m.content, "created_at": m.created_at.isoformat()}
                for m in messages
            ],
            "created_at": session.created_at,
        }

    async def delete_chat_session(self, user_id: uuid.UUID, session_id: uuid.UUID) -> None:
        session = await self.session_repo.get_by_id(session_id)
        if not session or session.user_id != user_id:
            raise NotFoundError("Chat session", str(session_id))
        await self.session_repo.soft_delete(session)

    # =========================================================================
    # Note Generation
    # =========================================================================

    async def generate_notes(
        self,
        user_id: uuid.UUID,
        source_type: str,
        source_id: uuid.UUID | None = None,
        source_text: str | None = None,
        title: str | None = None,
    ) -> GeneratedNote:
        """Generate structured notes from a lesson or raw text."""
        content_to_process = await self._resolve_source_content(
            source_type, source_id, source_text
        )
        if not title:
            title = await self._generate_title(content_to_process[:500])

        prompt = f"""Generate comprehensive, well-structured study notes for the following content:

---
{content_to_process[:15000]}
---

Include:
1. Main topics and subtopics
2. Key concepts with explanations
3. Important terms/definitions
4. Examples where relevant
5. A brief summary at the end"""

        notes_content = await generate_content(prompt, system_instruction=NOTE_GENERATOR_SYSTEM)

        # Generate a short summary separately
        summary_prompt = f"Summarize in 2-3 sentences: {content_to_process[:3000]}"
        summary = await generate_content(summary_prompt)

        course_id = source_id if source_type == "course" else None
        lesson_id = source_id if source_type == "lesson" else None

        note = await self.note_repo.create(
            user_id=user_id,
            source_type=source_type,
            course_id=course_id,
            lesson_id=lesson_id,
            title=title,
            content=notes_content,
            summary=summary[:500],
        )
        return note

    async def get_user_notes(
        self, user_id: uuid.UUID, skip: int = 0, limit: int = 20
    ) -> list[GeneratedNote]:
        return await self.note_repo.get_by_user(user_id, skip, limit)

    # =========================================================================
    # Summarization
    # =========================================================================

    async def summarize(
        self,
        source_type: str,
        source_id: uuid.UUID | None = None,
        source_text: str | None = None,
        length: str = "medium",
    ) -> dict[str, Any]:
        """Summarize content and return key points."""
        content = await self._resolve_source_content(source_type, source_id, source_text)

        length_map = {"short": "2-3 sentences", "medium": "1-2 paragraphs", "long": "3-4 paragraphs"}
        length_instruction = length_map.get(length, "1-2 paragraphs")

        prompt = f"""Summarize the following educational content in {length_instruction}.
Return JSON with "summary" (string) and "key_points" (list of 5-8 bullet points).

Content:
---
{content[:12000]}
---"""

        raw = await generate_content(prompt, system_instruction=SUMMARIZER_SYSTEM, temperature=0.3)
        try:
            cleaned = _extract_json(raw)
            data = json.loads(cleaned)
            return {
                "summary": data.get("summary", raw),
                "key_points": data.get("key_points", []),
                "source_type": source_type,
            }
        except (json.JSONDecodeError, KeyError):
            return {"summary": raw, "key_points": [], "source_type": source_type}

    # =========================================================================
    # Quiz Generation
    # =========================================================================

    async def generate_quiz_questions(
        self,
        source_type: str,
        source_id: uuid.UUID | None = None,
        source_text: str | None = None,
        num_questions: int = 10,
        difficulty: DifficultyLevel = DifficultyLevel.medium,
        question_types: list[QuestionType] | None = None,
    ) -> list[dict[str, Any]]:
        """Generate quiz questions from content. Returns raw question dicts."""
        if question_types is None:
            question_types = [QuestionType.mcq, QuestionType.true_false]

        content = await self._resolve_source_content(source_type, source_id, source_text)
        types_str = ", ".join((qt.value if hasattr(qt, "value") else qt) for qt in question_types)

        diff_val = difficulty.value if hasattr(difficulty, "value") else difficulty
        prompt = f"""Generate exactly {num_questions} quiz questions at {diff_val} difficulty level.
Question types to use: {types_str}.

For MCQ: provide options list with one is_correct=true.
For true_false: correct_answer must be "True" or "False", options=null.
For subjective: correct_answer is the expected answer, options=null.

Content to base questions on:
---
{content[:12000]}
---

Return ONLY valid JSON matching this schema:
{{"questions": [{{"question_text": "...", "question_type": "mcq|true_false|subjective", "options": [{{"text": "...", "is_correct": bool}}]|null, "correct_answer": "..."|null, "explanation": "...", "marks": 1.0}}]}}"""

        raw = await generate_content(prompt, system_instruction=QUIZ_GENERATOR_SYSTEM, temperature=0.5)
        try:
            cleaned = _extract_json(raw)
            data = json.loads(cleaned)
            questions = data.get("questions", [])
            # Validate and cap
            return questions[:num_questions]
        except (json.JSONDecodeError, KeyError) as exc:
            logger.error("Failed to parse quiz generation response", exc_info=True)
            raise AIServiceError("Failed to parse AI-generated quiz questions") from exc

    # =========================================================================
    # Flashcards
    # =========================================================================

    async def generate_flashcards(
        self,
        user_id: uuid.UUID,
        source_type: str,
        source_id: uuid.UUID | None = None,
        source_text: str | None = None,
        num_cards: int = 15,
        title: str | None = None,
        lesson_id: uuid.UUID | None = None,
        course_id: uuid.UUID | None = None,
    ) -> FlashcardSet:
        """Generate a flashcard set from content."""
        content = await self._resolve_source_content(source_type, source_id, source_text)
        if not title:
            title = await self._generate_title(content[:500], prefix="Flashcards: ")

        prompt = f"""Generate exactly {num_cards} study flashcards from this content.
Each card: front = concise question/term, back = answer/definition.
Return ONLY JSON: {{"cards": [{{"front": "...", "back": "..."}}]}}

Content:
---
{content[:10000]}
---"""

        raw = await generate_content(prompt, system_instruction=FLASHCARD_SYSTEM, temperature=0.6)
        try:
            cleaned = _extract_json(raw)
            data = json.loads(cleaned)
            cards = data.get("cards", [])[:num_cards]
        except (json.JSONDecodeError, KeyError) as exc:
            raise AIServiceError("Failed to parse AI-generated flashcards") from exc

        if lesson_id is None and source_type == "lesson":
            lesson_id = source_id
        if course_id is None and source_type == "course":
            course_id = source_id

        flashcard_set = await self.flashcard_repo.create(
            user_id=user_id,
            lesson_id=lesson_id,
            course_id=course_id,
            title=title,
            cards=cards,
            card_count=len(cards),
        )
        return flashcard_set

    async def get_user_flashcards(
        self, user_id: uuid.UUID, skip: int = 0, limit: int = 20
    ) -> list[FlashcardSet]:
        return await self.flashcard_repo.get_by_user(user_id, skip, limit)

    # =========================================================================
    # Study Planner
    # =========================================================================

    async def generate_study_plan(
        self,
        user_id: uuid.UUID,
        course_id: uuid.UUID | None = None,
        topics: list[str] | None = None,
        duration_weeks: int = 4,
        hours_per_day: int = 2,
        goals: str | None = None,
    ) -> StudyPlan:
        """Generate a personalized study plan."""
        context_parts = []

        if course_id:
            course = await self.course_repo.get_by_id(course_id)
            if course:
                lessons = await self.lesson_repo.get_by_course(course_id)
                lesson_titles = [l.title for l in lessons]
                context_parts.append(
                    f"Course: {course.title}\n"
                    f"Description: {course.description or 'N/A'}\n"
                    f"Lessons: {', '.join(lesson_titles[:20])}"
                )

        if topics:
            context_parts.append(f"Topics to cover: {', '.join(topics)}")
        if goals:
            context_parts.append(f"Student goals: {goals}")

        context = "\n\n".join(context_parts) or "General study plan"

        prompt = f"""Create a detailed {duration_weeks}-week study plan.
Student available: {hours_per_day} hours/day.
{context}

Return ONLY valid JSON:
{{"title": "...", "overview": "...", "weeks": [{{"week": 1, "theme": "...", "daily_tasks": [{{"day": "Monday", "tasks": ["..."], "hours": 2.0}}]}}], "tips": ["..."]}}"""

        raw = await generate_content(prompt, system_instruction=STUDY_PLANNER_SYSTEM, temperature=0.6)
        try:
            cleaned = _extract_json(raw)
            plan_data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise AIServiceError("Failed to parse AI-generated study plan") from exc

        plan_title = plan_data.get("title", f"{duration_weeks}-Week Study Plan")
        study_plan = await self.plan_repo.create(
            user_id=user_id,
            course_id=course_id,
            title=plan_title,
            duration_weeks=duration_weeks,
            plan_data=plan_data,
            is_active=True,
        )
        return study_plan

    async def get_study_plans(self, user_id: uuid.UUID) -> list[StudyPlan]:
        return await self.plan_repo.get_active_by_user(user_id)

    # =========================================================================
    # Learning Recommendations
    # =========================================================================

    async def get_recommendations(
        self,
        user_id: uuid.UUID,
        course_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        """Generate personalized learning recommendations for a student."""
        context_parts = [f"Student ID: {user_id}"]

        if course_id:
            course = await self.course_repo.get_by_id(course_id)
            if course:
                lessons = await self.lesson_repo.get_published_by_course(course_id)
                context_parts.append(
                    f"Current course: {course.title}\n"
                    f"Available lessons: {', '.join(l.title for l in lessons[:10])}"
                )

        prompt = f"""Based on student progress, provide learning recommendations.
{chr(10).join(context_parts)}

Return ONLY valid JSON:
{{"next_lessons": [{{"title": "...", "reason": "..."}}], "weak_topics": ["..."], "practice_suggestions": ["..."], "recommended_courses": [{{"title": "...", "reason": "..."}}], "message": "..."}}"""

        raw = await generate_content(prompt, system_instruction=RECOMMENDER_SYSTEM, temperature=0.7)
        try:
            cleaned = _extract_json(raw)
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return {
                "next_lessons": [],
                "weak_topics": [],
                "practice_suggestions": ["Keep practicing regularly", "Review completed lessons"],
                "recommended_courses": [],
                "message": "Keep up the great work! Consistency is key to learning.",
            }

    # =========================================================================
    # Private Helpers
    # =========================================================================

    async def _resolve_source_content(
        self,
        source_type: str,
        source_id: uuid.UUID | None,
        source_text: str | None,
    ) -> str:
        """Resolve content from various sources."""
        if source_type == "lesson" and source_id:
            lesson = await self.lesson_repo.get_by_id(source_id)
            if not lesson:
                raise NotFoundError("Lesson", str(source_id))
            parts = []
            if lesson.title:
                parts.append(f"# {lesson.title}")
            if lesson.content:
                parts.append(lesson.content)
            if lesson.transcript:
                parts.append(f"\n## Video Transcript\n{lesson.transcript}")
            if not parts:
                raise AIServiceError("Lesson has no content to process")
            return "\n\n".join(parts)

        elif source_type == "course" and source_id:
            course = await self.course_repo.get_by_id(source_id)
            if not course:
                raise NotFoundError("Course", str(source_id))
            lessons = await self.lesson_repo.get_published_by_course(source_id)
            parts = [f"# {course.title}", course.description or ""]
            for lesson in lessons[:5]:  # limit to first 5 lessons
                if lesson.content:
                    parts.append(f"## {lesson.title}\n{lesson.content[:2000]}")
            return "\n\n".join(parts)

        elif source_text:
            return source_text

        else:
            raise AIServiceError(
                "You must provide either source_id (for lesson/course) or source_text"
            )

    async def _generate_title(self, content_snippet: str, prefix: str = "") -> str:
        """Generate a short descriptive title from a content snippet."""
        try:
            prompt = f"Generate a short (5-8 word) descriptive title for: {content_snippet}"
            title = await generate_content(prompt, temperature=0.8)
            return f"{prefix}{title.strip().strip('\"')}"
        except Exception:
            return f"{prefix}Generated Content"


def _extract_json(text: str) -> str:
    """
    Extract JSON from a text response that may contain markdown code fences.
    Handles ```json ... ``` and plain JSON responses.
    """
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first line (```json or ```) and last line (```)
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text
