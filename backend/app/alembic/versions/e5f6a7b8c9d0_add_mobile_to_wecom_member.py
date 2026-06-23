"""add mobile to wecom_member and user

Revision ID: e5f6a7b8c9d0
Revises: c7d8e9f0a1b2
Create Date: 2026-06-23 12:00:00.000000+00:00
"""

from alembic import op
import sqlalchemy as sa
import sqlmodel

revision = "e5f6a7b8c9d0"
down_revision = "c7d8e9f0a1b2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "wecom_member",
        sa.Column("mobile", sqlmodel.AutoString(length=32), nullable=True),
    )
    op.add_column(
        "user",
        sa.Column("mobile", sqlmodel.AutoString(length=32), nullable=True),
    )
    op.create_index("ix_user_mobile", "user", ["mobile"])


def downgrade() -> None:
    op.drop_index("ix_user_mobile", table_name="user")
    op.drop_column("user", "mobile")
    op.drop_column("wecom_member", "mobile")
