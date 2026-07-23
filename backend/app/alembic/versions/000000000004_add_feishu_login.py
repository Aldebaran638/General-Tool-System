"""add feishu login

Revision ID: 000000000004
Revises: 000000000003
Create Date: 2026-07-22 00:00:00.000000

"""

import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from alembic import op

revision = "000000000004"
down_revision = "000000000003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "user",
        sa.Column(
            "feishu_user_id",
            sqlmodel.sql.sqltypes.AutoString(length=128),
            nullable=True,
        ),
    )
    op.create_index(
        op.f("ix_user_feishu_user_id"),
        "user",
        ["feishu_user_id"],
        unique=True,
    )
    op.alter_column(
        "user",
        "hashed_password",
        existing_type=sqlmodel.sql.sqltypes.AutoString(),
        nullable=True,
    )
    op.create_table(
        "feishu_login_ticket",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "token_hash",
            sqlmodel.sql.sqltypes.AutoString(length=64),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_feishu_login_ticket_user_id"),
        "feishu_login_ticket",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_feishu_login_ticket_token_hash"),
        "feishu_login_ticket",
        ["token_hash"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_feishu_login_ticket_token_hash"),
        table_name="feishu_login_ticket",
    )
    op.drop_index(
        op.f("ix_feishu_login_ticket_user_id"),
        table_name="feishu_login_ticket",
    )
    op.drop_table("feishu_login_ticket")
    op.execute(sa.text('DELETE FROM "user" WHERE hashed_password IS NULL'))
    op.alter_column(
        "user",
        "hashed_password",
        existing_type=sqlmodel.sql.sqltypes.AutoString(),
        nullable=False,
    )
    op.drop_index(op.f("ix_user_feishu_user_id"), table_name="user")
    op.drop_column("user", "feishu_user_id")
