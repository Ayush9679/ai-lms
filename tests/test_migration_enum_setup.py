"""Focused checks for the initial migration's PostgreSQL enum lifecycle."""

import importlib.util
import io
import os
import sqlite3
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy.engine import URL
from sqlalchemy.dialects.postgresql.named_types import CreateEnumType
from sqlalchemy.dialects.postgresql import dialect as postgresql_dialect


ROOT = Path(__file__).resolve().parents[1]
MIGRATION_PATH = ROOT / "alembic" / "versions" / "0001_initial_schema.py"
SPEC = importlib.util.spec_from_file_location("initial_schema_migration", MIGRATION_PATH)
assert SPEC is not None and SPEC.loader is not None
migration = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(migration)


class FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows

    def scalar_one(self):
        return self._rows


class FakeBind:
    dialect = SimpleNamespace(name="postgresql")

    def __init__(self, rows, current_schema="public"):
        self.rows = rows
        self.current_schema = current_schema
        self.statement = None
        self.parameters = None

    def execute(self, statement, parameters=None):
        self.statement = statement
        self.parameters = parameters
        if "current_schema()" in str(statement):
            return FakeResult(self.current_schema)
        return FakeResult(self.rows)


@pytest.mark.parametrize("enum_name", [enum_type.name for enum_type in migration.POSTGRES_ENUMS])
def test_missing_enum_is_created(monkeypatch, enum_name):
    enum_type = next(enum for enum in migration.POSTGRES_ENUMS if enum.name == enum_name)
    bind = FakeBind([])
    created = []
    monkeypatch.setattr(
        enum_type,
        "create",
        lambda actual_bind, checkfirst: created.append((actual_bind, checkfirst)),
    )

    assert migration._ensure_postgresql_enum(bind, enum_type) is True
    assert created == [(bind, False)]
    assert bind.parameters == {"schema": "public", "type_name": enum_name}
    assert "pg_catalog.pg_namespace" in str(bind.statement)
    create_sql = str(CreateEnumType(enum_type).compile(dialect=postgresql_dialect()))
    assert create_sql.startswith(f"CREATE TYPE public.{enum_name} AS ENUM")


@pytest.mark.parametrize("enum_type", migration.POSTGRES_ENUMS, ids=lambda enum: enum.name)
def test_existing_enum_with_exact_labels_is_reused(enum_type):
    bind = FakeBind([("e", label) for label in enum_type.enums])
    create = patch.object(enum_type, "create")

    with create as create_enum:
        assert migration._ensure_postgresql_enum(bind, enum_type) is False

    create_enum.assert_not_called()


@pytest.mark.parametrize("enum_type", migration.POSTGRES_ENUMS, ids=lambda enum: enum.name)
def test_existing_enum_with_different_labels_fails_without_mutation(enum_type):
    labels = list(enum_type.enums)
    labels[1] = "unexpected_label"
    bind = FakeBind([("e", label) for label in labels])
    create = patch.object(enum_type, "create")

    with create as create_enum:
        with pytest.raises(RuntimeError, match=rf"public\.{enum_type.name}.*expected"):
            migration._ensure_postgresql_enum(bind, enum_type)

    create_enum.assert_not_called()


def test_all_seven_shared_enums_are_schema_qualified_and_disable_auto_create():
    assert len(migration.POSTGRES_ENUMS) == 7
    expected_labels = {
        "user_role": ["student", "teacher", "admin"],
        "course_level": ["beginner", "intermediate", "advanced"],
        "course_status": ["draft", "published", "archived"],
        "file_type": ["image", "video", "document", "assignment", "other"],
        "enrollment_status": ["active", "completed", "dropped", "pending"],
        "question_type": ["mcq", "true_false", "subjective"],
        "difficulty_level": ["easy", "medium", "hard"],
    }
    assert {
        enum_type.name: list(enum_type.enums) for enum_type in migration.POSTGRES_ENUMS
    } == expected_labels
    assert all(enum_type.schema == "public" for enum_type in migration.POSTGRES_ENUMS)
    assert all(enum_type.create_type is False for enum_type in migration.POSTGRES_ENUMS)


def test_migration_refuses_to_create_tables_outside_public():
    with pytest.raises(RuntimeError, match="expected 'public'"):
        migration._require_public_schema(FakeBind([], current_schema="tenant"))


def test_postgresql_table_creation_does_not_recreate_enum_types(monkeypatch):
    output = io.StringIO()
    context = MigrationContext.configure(
        url="postgresql+asyncpg://",
        opts={"as_sql": True, "output_buffer": output},
    )
    checked = []
    monkeypatch.setattr(migration, "_require_public_schema", lambda bind: None)
    monkeypatch.setattr(
        migration,
        "_ensure_postgresql_enum",
        lambda bind, enum_type: checked.append(enum_type.name) or False,
    )

    with Operations.context(context):
        migration.upgrade()

    sql = output.getvalue().upper()
    assert len(checked) == 7
    assert sql.count("CREATE TABLE") == 21
    assert "CREATE TYPE" not in sql


def test_upgrade_contains_no_inline_enum_constructions():
    import ast

    tree = ast.parse(MIGRATION_PATH.read_text(encoding="utf-8"))
    upgrade = next(
        node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "upgrade"
    )
    enum_constructors = [
        node
        for node in ast.walk(upgrade)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr.lower() == "enum"
    ]
    assert enum_constructors == []

    enum_columns = {}
    for create_table in ast.walk(upgrade):
        if not (
            isinstance(create_table, ast.Call)
            and isinstance(create_table.func, ast.Attribute)
            and isinstance(create_table.func.value, ast.Name)
            and create_table.func.value.id == "op"
            and create_table.func.attr == "create_table"
        ):
            continue
        table_name = ast.literal_eval(create_table.args[0])
        for column in create_table.args[1:]:
            if not (
                isinstance(column, ast.Call)
                and isinstance(column.func, ast.Attribute)
                and isinstance(column.func.value, ast.Name)
                and column.func.value.id == "sa"
                and column.func.attr == "Column"
                and len(column.args) >= 2
                and isinstance(column.args[1], ast.Name)
            ):
                continue
            enum_columns[(table_name, ast.literal_eval(column.args[0]))] = column.args[1].id

    expected_enum_columns = {
        ("users", "role"): "USER_ROLE_ENUM",
        ("courses", "level"): "COURSE_LEVEL_ENUM",
        ("courses", "status"): "COURSE_STATUS_ENUM",
        ("course_files", "file_type"): "FILE_TYPE_ENUM",
        ("enrollments", "status"): "ENROLLMENT_STATUS_ENUM",
        ("quizzes", "difficulty"): "DIFFICULTY_LEVEL_ENUM",
        ("questions", "question_type"): "QUESTION_TYPE_ENUM",
    }
    assert {key: enum_columns.get(key) for key in expected_enum_columns} == expected_enum_columns


def test_sqlite_upgrade_creates_all_expected_tables(tmp_path):
    database_path = tmp_path / "migration.sqlite3"
    database_url = URL.create("sqlite+aiosqlite", database=str(database_path)).render_as_string(
        hide_password=False
    )
    env = {
        **os.environ,
        "DATABASE_URL": database_url,
        "DATABASE_SSL": "false",
        "DEBUG": "false",
    }
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    expected_tables = {
        "users",
        "email_verifications",
        "password_resets",
        "courses",
        "course_files",
        "lessons",
        "lesson_progress",
        "enrollments",
        "quizzes",
        "questions",
        "quiz_attempts",
        "quiz_answers",
        "assignments",
        "assignment_submissions",
        "ai_chat_sessions",
        "ai_chat_messages",
        "generated_notes",
        "study_plans",
        "flashcard_sets",
        "user_activities",
        "course_analytics",
        "payment_orders",
        "payments",
        "webhook_events",
        "alembic_version",
    }
    with sqlite3.connect(database_path) as connection:
        actual_tables = {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
    assert actual_tables == expected_tables
    with sqlite3.connect(database_path) as connection:
        explicit_indexes = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'index' AND name LIKE 'ix_%'"
            )
        }
        foreign_key_count = sum(
            len(connection.execute(f'PRAGMA foreign_key_list("{table}")').fetchall())
            for table in expected_tables
            if table != "alembic_version"
        )
    assert len(explicit_indexes) == 33
    assert foreign_key_count == 39
