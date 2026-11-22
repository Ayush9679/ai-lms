"""
AI-LMS Quiz Service — quiz CRUD, AI generation, and attempt evaluation.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.core.logging import get_logger
from app.models.course import CourseStatus
from app.models.enrollment import EnrollmentStatus
from app.models.quiz import Quiz, QuizAttempt, QuestionType
from app.models.user import UserRole
from app.repositories.course_repo import CourseRepository
from app.repositories.enrollment_repo import EnrollmentRepository
from app.repositories.quiz_repo import (
    QuestionRepository,
    QuizAnswerRepository,
    QuizAttemptRepository,
    QuizRepository,
)
from app.schemas.quiz import (
    CreateQuizRequest,
    GenerateQuizRequest,
    SubmitAttemptRequest,
    UpdateQuizRequest,
)

logger = get_logger(__name__)


class QuizService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = QuizRepository(db)
        self.question_repo = QuestionRepository(db)
        self.attempt_repo = QuizAttemptRepository(db)
        self.answer_repo = QuizAnswerRepository(db)
        self.course_repo = CourseRepository(db)
        self.enrollment_repo = EnrollmentRepository(db)

    async def _verify_course_access(
        self,
        course_id: uuid.UUID,
        requester_id: uuid.UUID,
        requester_role: UserRole,
    ):
        course = await self.course_repo.get_by_id(course_id)
        if not course:
            raise NotFoundError("Course", str(course_id))
        if requester_role not in (UserRole.admin,) and course.instructor_id != requester_id:
            raise ForbiddenError("You can only manage quizzes in your own courses")
        return course

    async def create_quiz(
        self,
        course_id: uuid.UUID,
        requester_id: uuid.UUID,
        requester_role: UserRole,
        request: CreateQuizRequest,
    ) -> Quiz:
        await self._verify_course_access(course_id, requester_id, requester_role)

        quiz = await self.repo.create(
            course_id=course_id,
            created_by=requester_id,
            title=request.title,
            description=request.description,
            difficulty=request.difficulty,
            passing_score=request.passing_score,
            negative_marking=request.negative_marking,
            negative_marks_per_wrong=request.negative_marks_per_wrong,
            time_limit_minutes=request.time_limit_minutes,
            max_attempts=request.max_attempts,
            is_ai_generated=False,
        )

        for i, q in enumerate(request.questions):
            await self.question_repo.create(
                quiz_id=quiz.id,
                question_text=q.question_text,
                question_type=q.question_type,
                options=[opt.model_dump() for opt in q.options] if q.options else None,
                correct_answer=q.correct_answer,
                explanation=q.explanation,
                marks=q.marks,
                order_index=q.order_index if q.order_index else i,
            )

        await self.repo.db.refresh(quiz, ["questions"])
        logger.info("Quiz created", extra={"quiz_id": str(quiz.id)})
        return quiz

    async def create_ai_quiz(
        self,
        course_id: uuid.UUID,
        requester_id: uuid.UUID,
        requester_role: UserRole,
        request: GenerateQuizRequest,
    ) -> Quiz:
        """Generate a quiz using AI and save it."""
        await self._verify_course_access(course_id, requester_id, requester_role)

        from app.ai.ai_service import AIService

        ai = AIService(self.repo.db)
        questions_data = await ai.generate_quiz_questions(
            source_type=request.source_type,
            source_id=request.source_id,
            source_text=request.source_text,
            num_questions=request.num_questions,
            difficulty=request.difficulty,
            question_types=request.question_types,
        )

        title = (
            request.title
            or f"AI Quiz - {request.difficulty.value.title()} ({len(questions_data)} questions)"
        )

        quiz = await self.repo.create(
            course_id=course_id,
            created_by=requester_id,
            title=title,
            difficulty=request.difficulty,
            passing_score=60.0,
            negative_marking=False,
            is_ai_generated=True,
        )

        for i, q_data in enumerate(questions_data):
            await self.question_repo.create(
                quiz_id=quiz.id,
                question_text=q_data.get("question_text", ""),
                question_type=q_data.get("question_type", "mcq"),
                options=q_data.get("options"),
                correct_answer=q_data.get("correct_answer"),
                explanation=q_data.get("explanation"),
                marks=float(q_data.get("marks", 1.0)),
                order_index=i,
            )

        await self.repo.db.refresh(quiz, ["questions"])
        return quiz

    async def get_quiz(self, quiz_id: uuid.UUID) -> Quiz:
        quiz = await self.repo.get_by_id(quiz_id)
        if not quiz:
            raise NotFoundError("Quiz", str(quiz_id))
        return quiz

    async def list_course_quizzes(self, course_id: uuid.UUID) -> list[Quiz]:
        return await self.repo.get_by_course(course_id)

    async def update_quiz(
        self,
        quiz_id: uuid.UUID,
        requester_id: uuid.UUID,
        requester_role: UserRole,
        request: UpdateQuizRequest,
    ) -> Quiz:
        quiz = await self.get_quiz(quiz_id)
        if requester_role != UserRole.admin and quiz.created_by != requester_id:
            raise ForbiddenError("You can only edit your own quizzes")
        update_data = request.model_dump(exclude_unset=True, exclude_none=True)
        return await self.repo.update(quiz, **update_data)

    async def delete_quiz(
        self,
        quiz_id: uuid.UUID,
        requester_id: uuid.UUID,
        requester_role: UserRole,
    ) -> None:
        quiz = await self.get_quiz(quiz_id)
        if requester_role != UserRole.admin and quiz.created_by != requester_id:
            raise ForbiddenError("You can only delete your own quizzes")
        await self.repo.soft_delete(quiz)

    async def submit_attempt(
        self,
        quiz_id: uuid.UUID,
        student_id: uuid.UUID,
        request: SubmitAttemptRequest,
    ) -> QuizAttempt:
        """Evaluate a quiz submission and return the graded attempt."""
        quiz = await self.get_quiz(quiz_id)

        course = await self.course_repo.get_by_id(quiz.course_id)
        enrollment = await self.enrollment_repo.get_by_student_and_course(
            student_id, quiz.course_id
        )
        if (
            not course
            or course.status != CourseStatus.published
            or not enrollment
            or enrollment.status not in {EnrollmentStatus.active, EnrollmentStatus.completed}
        ):
            raise ForbiddenError("You must be enrolled in this published course to take its quiz")

        # Check attempt limit
        if quiz.max_attempts > 0:
            attempt_count = await self.attempt_repo.count_by_student_and_quiz(student_id, quiz_id)
            if attempt_count >= quiz.max_attempts:
                raise ValidationError(
                    f"Maximum {quiz.max_attempts} attempt(s) allowed for this quiz"
                )

        attempt_number = await self.attempt_repo.count_by_student_and_quiz(student_id, quiz_id) + 1
        questions = await self.question_repo.get_by_quiz(quiz_id)

        # Build question lookup
        q_map = {q.id: q for q in questions}
        max_score = sum(q.marks for q in questions)

        # Grade each answer
        score = 0.0
        answer_records = []

        for submitted in request.answers:
            question = q_map.get(submitted.question_id)
            if not question:
                continue

            is_correct = None
            marks_awarded = 0.0

            if question.question_type in (QuestionType.mcq, QuestionType.true_false):
                correct_ans = question.correct_answer
                if (
                    not correct_ans
                    and question.question_type == QuestionType.mcq
                    and question.options
                ):
                    for opt in question.options:
                        if opt.get("is_correct") is True:
                            correct_ans = opt.get("text")
                            break

                is_correct = (
                    submitted.given_answer is not None
                    and submitted.given_answer.strip().lower()
                    == str(correct_ans or "").strip().lower()
                )
                if is_correct:
                    marks_awarded = question.marks
                    score += marks_awarded
                elif submitted.given_answer and quiz.negative_marking:
                    deduction = question.marks * quiz.negative_marks_per_wrong
                    score -= deduction
                    marks_awarded = -deduction

            elif question.question_type == QuestionType.subjective:
                # Subjective answers are not auto-graded
                is_correct = None
                marks_awarded = 0.0

            answer_records.append(
                {
                    "question_id": question.id,
                    "correct_answer": question.correct_answer,
                    "explanation": question.explanation,
                    "given_answer": submitted.given_answer,
                    "is_correct": is_correct,
                    "marks_awarded": marks_awarded,
                }
            )

        score = max(0.0, score)  # No negative total
        percentage = (score / max_score * 100.0) if max_score > 0 else 0.0
        passed = percentage >= quiz.passing_score

        # Create attempt record
        attempt = await self.attempt_repo.create(
            quiz_id=quiz_id,
            student_id=student_id,
            score=score,
            max_score=max_score,
            percentage=round(percentage, 2),
            passed=passed,
            time_taken_seconds=request.time_taken_seconds,
            attempt_number=attempt_number,
        )

        # Store answers
        for a in answer_records:
            await self.answer_repo.create(
                attempt_id=attempt.id,
                question_id=a["question_id"],
                given_answer=a["given_answer"],
                is_correct=a["is_correct"],
                marks_awarded=a["marks_awarded"],
            )

        # Build response-friendly answers with extra context
        attempt._answer_details = answer_records
        return attempt

    async def get_attempt_history(
        self, student_id: uuid.UUID, quiz_id: uuid.UUID
    ) -> list[QuizAttempt]:
        return await self.attempt_repo.get_by_student_and_quiz(student_id, quiz_id)

    async def get_student_attempts(
        self, student_id: uuid.UUID, skip: int = 0, limit: int = 20
    ) -> list[QuizAttempt]:
        return await self.attempt_repo.get_by_student(student_id, skip, limit)
