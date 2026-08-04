"""Initial database schema — all tables

Revision ID: 0001
Revises:
Create Date: 2026-08-04 00:00:00.000000

"""
from typing import Sequence, Union
import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ==========================================================================
    # Enums
    # ==========================================================================
    bind = op.get_bind()
    is_postgresql = bind.dialect.name == "postgresql"
    if is_postgresql:
        op.execute("CREATE TYPE user_role AS ENUM ('student', 'teacher', 'admin')")
        op.execute("CREATE TYPE course_level AS ENUM ('beginner', 'intermediate', 'advanced')")
        op.execute("CREATE TYPE course_status AS ENUM ('draft', 'published', 'archived')")
        op.execute("CREATE TYPE file_type AS ENUM ('image', 'video', 'document', 'assignment', 'other')")
        op.execute("CREATE TYPE enrollment_status AS ENUM ('active', 'completed', 'dropped', 'pending')")
        op.execute("CREATE TYPE question_type AS ENUM ('mcq', 'true_false', 'subjective')")
        op.execute("CREATE TYPE difficulty_level AS ENUM ('easy', 'medium', 'hard')")

    # ==========================================================================
    # users
    # ==========================================================================
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("email", sa.String(320), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(128), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("role", sa.Enum("student", "teacher", "admin", name="user_role"), nullable=False, server_default="student"),
        sa.Column("profile_image", sa.String(500), nullable=True),
        sa.Column("bio", sa.Text, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("is_verified", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_email", "users", ["email"])

    # ==========================================================================
    # email_verifications
    # ==========================================================================
    op.create_table(
        "email_verifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token", sa.String(512), nullable=False, unique=True),
        sa.Column("is_used", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_email_verifications_token", "email_verifications", ["token"])

    # ==========================================================================
    # password_resets
    # ==========================================================================
    op.create_table(
        "password_resets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token", sa.String(512), nullable=False, unique=True),
        sa.Column("is_used", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_password_resets_token", "password_resets", ["token"])

    # ==========================================================================
    # courses
    # ==========================================================================
    op.create_table(
        "courses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("slug", sa.String(600), nullable=False, unique=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("level", sa.Enum("beginner", "intermediate", "advanced", name="course_level"), nullable=False, server_default="beginner"),
        sa.Column("status", sa.Enum("draft", "published", "archived", name="course_status"), nullable=False, server_default="draft"),
        sa.Column("thumbnail", sa.String(500), nullable=True),
        sa.Column("price", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
        sa.Column("instructor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tags", sa.String(1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_courses_id", "courses", ["id"])
    op.create_index("ix_courses_title", "courses", ["title"])
    op.create_index("ix_courses_slug", "courses", ["slug"])
    op.create_index("ix_courses_status", "courses", ["status"])
    op.create_index("ix_courses_instructor_id", "courses", ["instructor_id"])
    op.create_index("ix_courses_category", "courses", ["category"])

    # ==========================================================================
    # course_files
    # ==========================================================================
    op.create_table(
        "course_files",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("file_name", sa.String(500), nullable=False),
        sa.Column("original_name", sa.String(500), nullable=False),
        sa.Column("file_path", sa.String(1000), nullable=False),
        sa.Column("file_type", sa.Enum("image", "video", "document", "assignment", "other", name="file_type"), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("size_bytes", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_course_files_course_id", "course_files", ["course_id"])

    # ==========================================================================
    # lessons
    # ==========================================================================
    op.create_table(
        "lessons",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("content", sa.Text, nullable=True),
        sa.Column("video_url", sa.String(1000), nullable=True),
        sa.Column("pdf_url", sa.String(1000), nullable=True),
        sa.Column("transcript", sa.Text, nullable=True),
        sa.Column("duration_minutes", sa.Integer, nullable=True),
        sa.Column("order_index", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_published", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_lessons_course_id", "lessons", ["course_id"])

    # ==========================================================================
    # lesson_progress
    # ==========================================================================
    op.create_table(
        "lesson_progress",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("lesson_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("is_completed", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("watch_time_seconds", sa.Integer, nullable=False, server_default="0"),
        sa.Column("completion_percentage", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_lesson_progress_lesson_id", "lesson_progress", ["lesson_id"])
    op.create_index("ix_lesson_progress_user_id", "lesson_progress", ["user_id"])

    # ==========================================================================
    # enrollments
    # ==========================================================================
    op.create_table(
        "enrollments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.Enum("active", "completed", "dropped", "pending", name="enrollment_status"), nullable=False, server_default="active"),
        sa.Column("progress", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("completed_lessons", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("student_id", "course_id", name="uq_enrollment_student_course"),
    )
    op.create_index("ix_enrollments_student_id", "enrollments", ["student_id"])
    op.create_index("ix_enrollments_course_id", "enrollments", ["course_id"])

    # ==========================================================================
    # quizzes
    # ==========================================================================
    op.create_table(
        "quizzes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("lesson_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("lessons.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("difficulty", sa.Enum("easy", "medium", "hard", name="difficulty_level"), nullable=False, server_default="medium"),
        sa.Column("passing_score", sa.Float, nullable=False, server_default="60.0"),
        sa.Column("negative_marking", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("negative_marks_per_wrong", sa.Float, nullable=False, server_default="0.25"),
        sa.Column("time_limit_minutes", sa.Integer, nullable=True),
        sa.Column("is_ai_generated", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("max_attempts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_quizzes_course_id", "quizzes", ["course_id"])

    # ==========================================================================
    # questions
    # ==========================================================================
    op.create_table(
        "questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("quiz_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_text", sa.Text, nullable=False),
        sa.Column("question_type", sa.Enum("mcq", "true_false", "subjective", name="question_type"), nullable=False),
        sa.Column("options", postgresql.JSON, nullable=True),
        sa.Column("correct_answer", sa.Text, nullable=True),
        sa.Column("explanation", sa.Text, nullable=True),
        sa.Column("marks", sa.Float, nullable=False, server_default="1.0"),
        sa.Column("order_index", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_questions_quiz_id", "questions", ["quiz_id"])

    # ==========================================================================
    # quiz_attempts
    # ==========================================================================
    op.create_table(
        "quiz_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("quiz_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("score", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("max_score", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("percentage", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("passed", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("time_taken_seconds", sa.Integer, nullable=True),
        sa.Column("attempt_number", sa.Integer, nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_quiz_attempts_quiz_id", "quiz_attempts", ["quiz_id"])
    op.create_index("ix_quiz_attempts_student_id", "quiz_attempts", ["student_id"])

    # ==========================================================================
    # quiz_answers
    # ==========================================================================
    op.create_table(
        "quiz_answers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("attempt_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("quiz_attempts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("questions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("given_answer", sa.Text, nullable=True),
        sa.Column("is_correct", sa.Boolean, nullable=True),
        sa.Column("marks_awarded", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_quiz_answers_attempt_id", "quiz_answers", ["attempt_id"])

    # ==========================================================================
    # assignments
    # ==========================================================================
    op.create_table(
        "assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("instructions", sa.Text, nullable=True),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("max_marks", sa.Float, nullable=False, server_default="100.0"),
        sa.Column("passing_marks", sa.Float, nullable=False, server_default="40.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_assignments_course_id", "assignments", ["course_id"])

    # ==========================================================================
    # assignment_submissions
    # ==========================================================================
    op.create_table(
        "assignment_submissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("assignment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_url", sa.String(1000), nullable=True),
        sa.Column("file_name", sa.String(500), nullable=True),
        sa.Column("text_content", sa.Text, nullable=True),
        sa.Column("marks_obtained", sa.Float, nullable=True),
        sa.Column("feedback", sa.Text, nullable=True),
        sa.Column("graded_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("graded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_assignment_submissions_assignment_id", "assignment_submissions", ["assignment_id"])
    op.create_index("ix_assignment_submissions_student_id", "assignment_submissions", ["student_id"])

    # ==========================================================================
    # ai_chat_sessions
    # ==========================================================================
    op.create_table(
        "ai_chat_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("courses.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(500), nullable=False, server_default="New Chat"),
        sa.Column("message_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_ai_chat_sessions_user_id", "ai_chat_sessions", ["user_id"])

    # ==========================================================================
    # ai_chat_messages
    # ==========================================================================
    op.create_table(
        "ai_chat_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ai_chat_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(10), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("token_count", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_ai_chat_messages_session_id", "ai_chat_messages", ["session_id"])

    # ==========================================================================
    # generated_notes
    # ==========================================================================
    op.create_table(
        "generated_notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("courses.id", ondelete="SET NULL"), nullable=True),
        sa.Column("lesson_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("lessons.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_generated_notes_user_id", "generated_notes", ["user_id"])

    # ==========================================================================
    # study_plans
    # ==========================================================================
    op.create_table(
        "study_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("courses.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("duration_weeks", sa.Integer, nullable=False, server_default="4"),
        sa.Column("plan_data", postgresql.JSON, nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_study_plans_user_id", "study_plans", ["user_id"])

    # ==========================================================================
    # flashcard_sets
    # ==========================================================================
    op.create_table(
        "flashcard_sets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("courses.id", ondelete="SET NULL"), nullable=True),
        sa.Column("lesson_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("lessons.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("cards", postgresql.JSON, nullable=False),
        sa.Column("card_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_flashcard_sets_user_id", "flashcard_sets", ["user_id"])

    # ==========================================================================
    # user_activities
    # ==========================================================================
    op.create_table(
        "user_activities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(50), nullable=True),
        sa.Column("resource_id", sa.String(100), nullable=True),
        sa.Column("metadata", postgresql.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_user_activities_user_id", "user_activities", ["user_id"])
    op.create_index("ix_user_activities_action", "user_activities", ["action"])

    # ==========================================================================
    # course_analytics
    # ==========================================================================
    op.create_table(
        "course_analytics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("total_enrollments", sa.Integer, nullable=False, server_default="0"),
        sa.Column("active_students", sa.Integer, nullable=False, server_default="0"),
        sa.Column("completed_students", sa.Integer, nullable=False, server_default="0"),
        sa.Column("average_progress", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("average_quiz_score", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("total_quiz_attempts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("total_assignments_submitted", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_course_analytics_course_id", "course_analytics", ["course_id"])


def downgrade() -> None:
    op.drop_table("course_analytics")
    op.drop_table("user_activities")
    op.drop_table("flashcard_sets")
    op.drop_table("study_plans")
    op.drop_table("generated_notes")
    op.drop_table("ai_chat_messages")
    op.drop_table("ai_chat_sessions")
    op.drop_table("assignment_submissions")
    op.drop_table("assignments")
    op.drop_table("quiz_answers")
    op.drop_table("quiz_attempts")
    op.drop_table("questions")
    op.drop_table("quizzes")
    op.drop_table("enrollments")
    op.drop_table("lesson_progress")
    op.drop_table("lessons")
    op.drop_table("course_files")
    op.drop_table("courses")
    op.drop_table("password_resets")
    op.drop_table("email_verifications")
    op.drop_table("users")

    bind = op.get_bind()
    is_postgresql = bind.dialect.name == "postgresql"
    if is_postgresql:
        op.execute("DROP TYPE IF EXISTS difficulty_level")
        op.execute("DROP TYPE IF EXISTS question_type")
        op.execute("DROP TYPE IF EXISTS enrollment_status")
        op.execute("DROP TYPE IF EXISTS file_type")
        op.execute("DROP TYPE IF EXISTS course_status")
        op.execute("DROP TYPE IF EXISTS course_level")
        op.execute("DROP TYPE IF EXISTS user_role")
