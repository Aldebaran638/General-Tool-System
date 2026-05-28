"""add data sync tables

Revision ID: c7d8e9f0a1b2
Revises: f3a9c2b1d4e5
Create Date: 2026-05-27 12:00:00.000000+00:00
"""

from alembic import op
import sqlalchemy as sa
import sqlmodel

revision = "c7d8e9f0a1b2"
down_revision = "f3a9c2b1d4e5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # wecom_department
    op.create_table(
        "wecom_department",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sqlmodel.AutoString(length=128), nullable=False),
        sa.Column("name_en", sqlmodel.AutoString(length=128), nullable=True),
        sa.Column("parentid", sa.Integer(), nullable=True),
        sa.Column("order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "synced_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_wecom_department_parentid", "wecom_department", ["parentid"])

    # wecom_member
    op.create_table(
        "wecom_member",
        sa.Column("userid", sqlmodel.AutoString(length=64), nullable=False),
        sa.Column("name", sqlmodel.AutoString(length=64), nullable=False),
        sa.Column("department", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("avatar", sqlmodel.AutoString(length=512), nullable=True),
        sa.Column("status", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "synced_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("removed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("userid"),
    )

    # sync_task
    op.create_table(
        "sync_task",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("entity_type", sqlmodel.AutoString(length=32), nullable=False),
        sa.Column("sync_mode", sqlmodel.AutoString(length=16), nullable=False),
        sa.Column("trigger_type", sqlmodel.AutoString(length=16), nullable=False),
        sa.Column(
            "status",
            sqlmodel.AutoString(length=16),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fetched_count", sa.Integer(), nullable=True),
        sa.Column("created_count", sa.Integer(), nullable=True),
        sa.Column("updated_count", sa.Integer(), nullable=True),
        sa.Column("deleted_count", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("triggered_by_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["triggered_by_id"],
            ["user.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sync_task_entity_type", "sync_task", ["entity_type"])
    op.create_index("ix_sync_task_started_at", "sync_task", ["started_at"])


def downgrade() -> None:
    op.drop_table("sync_task")
    op.drop_table("wecom_member")
    op.drop_index("ix_wecom_department_parentid", table_name="wecom_department")
    op.drop_table("wecom_department")
