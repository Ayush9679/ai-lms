"""Add course currency and verified lesson video size.

Revision ID: 0003
Revises: 0002
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "courses",
        sa.Column("currency", sa.String(length=3), server_default="INR", nullable=False),
    )
    op.add_column("lessons", sa.Column("video_size_bytes", sa.BigInteger(), nullable=True))


def downgrade() -> None:
    op.drop_column("lessons", "video_size_bytes")
    op.drop_column("courses", "currency")
