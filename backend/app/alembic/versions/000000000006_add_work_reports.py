"""add work reports

Revision ID: 000000000006
Revises: 000000000005
Create Date: 2026-07-23 00:00:00.000000

"""

import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from alembic import op

revision = "000000000006"
down_revision = "000000000005"
branch_labels = None
depends_on = None


FIELD_DEFAULTS = (
    ("work_plan", "plan_content", True),
    ("work_plan", "planned_completion_date", True),
    ("work_plan", "expected_result", False),
    ("work_plan", "support_needed", False),
    ("work_plan", "remarks", False),
    ("task_summary", "work_goal", True),
    ("task_summary", "completion_date", False),
    ("task_summary", "progress_description", True),
    ("task_summary", "progress", True),
    ("task_summary", "incomplete_reason", False),
    ("work_review", "review_module", True),
    ("work_review", "review_content", True),
)


def upgrade() -> None:
    op.create_table(
        "work_report",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("reporter_id", sa.Uuid(), nullable=True),
        sa.Column(
            "reporter_name",
            sqlmodel.sql.sqltypes.AutoString(length=255),
            nullable=True,
        ),
        sa.Column(
            "reporter_email",
            sqlmodel.sql.sqltypes.AutoString(length=255),
            nullable=False,
        ),
        sa.Column(
            "report_type",
            sqlmodel.sql.sqltypes.AutoString(length=16),
            nullable=False,
        ),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column(
            "title", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False
        ),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "report_type IN ('weekly', 'monthly')",
            name="ck_work_report_report_type",
        ),
        sa.ForeignKeyConstraint(
            ["reporter_id"], ["user.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "reporter_id",
            "report_type",
            "period_start",
            name="uq_work_report_reporter_period",
        ),
    )
    op.create_index(
        op.f("ix_work_report_reporter_id"),
        "work_report",
        ["reporter_id"],
        unique=False,
    )

    op.create_table(
        "work_plan",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("work_report_id", sa.Uuid(), nullable=False),
        sa.Column("plan_content", sa.Text(), nullable=True),
        sa.Column("planned_completion_date", sa.Date(), nullable=True),
        sa.Column("expected_result", sa.Text(), nullable=True),
        sa.Column("support_needed", sa.Text(), nullable=True),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["work_report_id"], ["work_report.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_work_plan_work_report_id"),
        "work_plan",
        ["work_report_id"],
        unique=False,
    )

    op.create_table(
        "task_summary",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("work_report_id", sa.Uuid(), nullable=False),
        sa.Column("work_goal", sa.Text(), nullable=True),
        sa.Column("completion_date", sa.Date(), nullable=True),
        sa.Column("progress_description", sa.Text(), nullable=True),
        sa.Column("progress", sa.Integer(), nullable=True),
        sa.Column("incomplete_reason", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "progress IS NULL OR (progress >= 0 AND progress <= 100)",
            name="ck_task_summary_progress",
        ),
        sa.ForeignKeyConstraint(
            ["work_report_id"], ["work_report.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_task_summary_work_report_id"),
        "task_summary",
        ["work_report_id"],
        unique=False,
    )

    op.create_table(
        "work_review",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("work_report_id", sa.Uuid(), nullable=False),
        sa.Column("review_module", sa.Text(), nullable=True),
        sa.Column("review_content", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["work_report_id"], ["work_report.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_work_review_work_report_id"),
        "work_review",
        ["work_report_id"],
        unique=False,
    )

    config_table = op.create_table(
        "work_report_field_config",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "section",
            sqlmodel.sql.sqltypes.AutoString(length=32),
            nullable=False,
        ),
        sa.Column(
            "field_key",
            sqlmodel.sql.sqltypes.AutoString(length=64),
            nullable=False,
        ),
        sa.Column("is_required", sa.Boolean(), nullable=False),
        sa.Column("updated_by_id", sa.Uuid(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["updated_by_id"], ["user.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "section", "field_key", name="uq_work_report_field_config_key"
        ),
    )
    op.create_index(
        op.f("ix_work_report_field_config_section"),
        "work_report_field_config",
        ["section"],
        unique=False,
    )
    op.bulk_insert(
        config_table,
        [
            {
                "id": uuid.uuid4(),
                "section": section,
                "field_key": field_key,
                "is_required": is_required,
                "updated_by_id": None,
                "updated_at": datetime.now(timezone.utc),
            }
            for section, field_key, is_required in FIELD_DEFAULTS
        ],
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_work_report_field_config_section"),
        table_name="work_report_field_config",
    )
    op.drop_table("work_report_field_config")
    op.drop_index(op.f("ix_work_review_work_report_id"), table_name="work_review")
    op.drop_table("work_review")
    op.drop_index(
        op.f("ix_task_summary_work_report_id"), table_name="task_summary"
    )
    op.drop_table("task_summary")
    op.drop_index(op.f("ix_work_plan_work_report_id"), table_name="work_plan")
    op.drop_table("work_plan")
    op.drop_index(op.f("ix_work_report_reporter_id"), table_name="work_report")
    op.drop_table("work_report")
