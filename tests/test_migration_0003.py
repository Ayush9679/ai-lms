import importlib.util
from pathlib import Path

from sqlalchemy import BigInteger, String


MIGRATION_PATH = Path(__file__).parents[1] / "alembic" / "versions" / "0003_course_currency.py"
SPEC = importlib.util.spec_from_file_location("course_currency_migration", MIGRATION_PATH)
assert SPEC and SPEC.loader
migration = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(migration)


def test_revision_follows_lesson_media_migration():
    assert migration.revision == "0003"
    assert migration.down_revision == "0002"


def test_migration_adds_compatible_defaults_and_wide_video_size(monkeypatch):
    columns = {}
    monkeypatch.setattr(
        migration.op,
        "add_column",
        lambda table, column: columns.__setitem__((table, column.name), column),
    )

    migration.upgrade()

    currency = columns["courses", "currency"]
    assert isinstance(currency.type, String)
    assert currency.type.length == 3
    assert currency.server_default.arg == "INR"
    assert not currency.nullable

    video_size = columns["lessons", "video_size_bytes"]
    assert isinstance(video_size.type, BigInteger)
    assert video_size.nullable
