"""add work report reminders

Revision ID: 000000000007
Revises: 000000000006
Create Date: 2026-07-23 00:00:00.000000

"""

import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from alembic import op

revision = "000000000007"
down_revision = "000000000006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "work_report_reminder_rule",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "report_type",
            sqlmodel.sql.sqltypes.AutoString(length=16),
            nullable=False,
        ),
        sa.Column("weekday", sa.Integer(), nullable=True),
        sa.Column("month_day", sa.Integer(), nullable=True),
        sa.Column("is_last_day", sa.Boolean(), nullable=False),
        sa.Column("local_time", sa.Time(), nullable=False),
        sa.Column(
            "timezone",
            sqlmodel.sql.sqltypes.AutoString(length=64),
            nullable=False,
        ),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column(
            "schedule_signature",
            sqlmodel.sql.sqltypes.AutoString(length=160),
            nullable=False,
        ),
        sa.Column("created_by_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "report_type IN ('weekly', 'monthly')",
            name="ck_work_report_reminder_rule_type",
        ),
        sa.CheckConstraint(
            "weekday IS NULL OR weekday BETWEEN 1 AND 7",
            name="ck_work_report_reminder_rule_weekday",
        ),
        sa.CheckConstraint(
            "month_day IS NULL OR month_day BETWEEN 1 AND 31",
            name="ck_work_report_reminder_rule_month_day",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_id"], ["user.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "schedule_signature",
            name="uq_work_report_reminder_rule_signature",
        ),
    )
    op.create_index(
        op.f("ix_work_report_reminder_rule_report_type"),
        "work_report_reminder_rule",
        ["report_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_work_report_reminder_rule_schedule_signature"),
        "work_report_reminder_rule",
        ["schedule_signature"],
        unique=True,
    )

    op.create_table(
        "work_report_reminder_run",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("rule_id", sa.Uuid(), nullable=True),
        sa.Column(
            "report_type",
            sqlmodel.sql.sqltypes.AutoString(length=16),
            nullable=False,
        ),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status",
            sqlmodel.sql.sqltypes.AutoString(length=16),
            nullable=False,
        ),
        sa.Column("target_count", sa.Integer(), nullable=False),
        sa.Column("sent_count", sa.Integer(), nullable=False),
        sa.Column("failed_count", sa.Integer(), nullable=False),
        sa.Column("skipped_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["rule_id"],
            ["work_report_reminder_rule.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "rule_id",
            "scheduled_for",
            name="uq_work_report_reminder_run_schedule",
        ),
    )
    op.create_index(
        op.f("ix_work_report_reminder_run_rule_id"),
        "work_report_reminder_run",
        ["rule_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_work_report_reminder_run_scheduled_for"),
        "work_report_reminder_run",
        ["scheduled_for"],
        unique=False,
    )
    op.create_index(
        op.f("ix_work_report_reminder_run_status"),
        "work_report_reminder_run",
        ["status"],
        unique=False,
    )

    op.create_table(
        "work_report_reminder_delivery",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column(
            "user_name",
            sqlmodel.sql.sqltypes.AutoString(length=255),
            nullable=True,
        ),
        sa.Column(
            "receiver_open_id",
            sqlmodel.sql.sqltypes.AutoString(length=128),
            nullable=False,
        ),
        sa.Column(
            "status",
            sqlmodel.sql.sqltypes.AutoString(length=16),
            nullable=False,
        ),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column(
            "feishu_message_id",
            sqlmodel.sql.sqltypes.AutoString(length=128),
            nullable=True,
        ),
        sa.Column(
            "error_code",
            sqlmodel.sql.sqltypes.AutoString(length=64),
            nullable=True,
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["run_id"], ["work_report_reminder_run.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["user.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "run_id",
            "user_id",
            name="uq_work_report_reminder_delivery_user",
        ),
    )
    op.create_index(
        op.f("ix_work_report_reminder_delivery_run_id"),
        "work_report_reminder_delivery",
        ["run_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_work_report_reminder_delivery_user_id"),
        "work_report_reminder_delivery",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_work_report_reminder_delivery_status"),
        "work_report_reminder_delivery",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_work_report_reminder_delivery_status"),
        table_name="work_report_reminder_delivery",
    )
    op.drop_index(
        op.f("ix_work_report_reminder_delivery_user_id"),
        table_name="work_report_reminder_delivery",
    )
    op.drop_index(
        op.f("ix_work_report_reminder_delivery_run_id"),
        table_name="work_report_reminder_delivery",
    )
    op.drop_table("work_report_reminder_delivery")
    op.drop_index(
        op.f("ix_work_report_reminder_run_status"),
        table_name="work_report_reminder_run",
    )
    op.drop_index(
        op.f("ix_work_report_reminder_run_scheduled_for"),
        table_name="work_report_reminder_run",
    )
    op.drop_index(
        op.f("ix_work_report_reminder_run_rule_id"),
        table_name="work_report_reminder_run",
    )
    op.drop_table("work_report_reminder_run")
    op.drop_index(
        op.f("ix_work_report_reminder_rule_schedule_signature"),
        table_name="work_report_reminder_rule",
    )
    op.drop_index(
        op.f("ix_work_report_reminder_rule_report_type"),
        table_name="work_report_reminder_rule",
    )
    op.drop_table("work_report_reminder_rule")
