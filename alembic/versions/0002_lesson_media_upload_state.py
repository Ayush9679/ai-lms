"""Add lesson thumbnail and verified video upload state.

Revision ID: 0002
Revises: 0001
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("courses", sa.Column("thumbnail_upload_id", sa.String(length=36), nullable=True))
    op.add_column("courses", sa.Column("file_upload_id", sa.String(length=36), nullable=True))
    op.add_column("course_files", sa.Column("upload_id", sa.String(length=36), nullable=True))
    op.create_index("uq_course_files_upload_id", "course_files", ["upload_id"], unique=True)
    op.add_column("lessons", sa.Column("thumbnail", sa.String(length=500), nullable=True))
    op.add_column("lessons", sa.Column("thumbnail_upload_id", sa.String(length=36), nullable=True))
    op.add_column(
        "lessons",
        sa.Column(
            "video_status",
            sa.String(length=20),
            server_default="pending",
            nullable=False,
        ),
    )
    op.add_column("lessons", sa.Column("video_upload_id", sa.String(length=36), nullable=True))
    op.add_column("lessons", sa.Column("pdf_upload_id", sa.String(length=36), nullable=True))
    op.execute(
        "UPDATE lessons SET video_status = 'ready' "
        "WHERE video_url IS NOT NULL AND length(trim(video_url)) > 0"
    )


def downgrade() -> None:
    op.drop_index("uq_course_files_upload_id", table_name="course_files")
    op.drop_column("course_files", "upload_id")
    op.drop_column("lessons", "pdf_upload_id")
    op.drop_column("lessons", "video_upload_id")
    op.drop_column("lessons", "video_status")
    op.drop_column("lessons", "thumbnail_upload_id")
    op.drop_column("lessons", "thumbnail")
    op.drop_column("courses", "thumbnail_upload_id")
    op.drop_column("courses", "file_upload_id")
