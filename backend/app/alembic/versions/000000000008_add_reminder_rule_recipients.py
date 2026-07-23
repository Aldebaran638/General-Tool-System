"""add reminder rule recipients

Revision ID: 000000000008
Revises: 000000000007
Create Date: 2026-07-23 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

revision = "000000000008"
down_revision = "000000000007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "work_report_reminder_rule_recipient",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("rule_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["rule_id"],
            ["work_report_reminder_rule.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "rule_id",
            "user_id",
            name="uq_work_report_reminder_rule_recipient",
        ),
    )
    op.create_index(
        op.f("ix_work_report_reminder_rule_recipient_rule_id"),
        "work_report_reminder_rule_recipient",
        ["rule_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_work_report_reminder_rule_recipient_user_id"),
        "work_report_reminder_rule_recipient",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_work_report_reminder_rule_recipient_user_id"),
        table_name="work_report_reminder_rule_recipient",
    )
    op.drop_index(
        op.f("ix_work_report_reminder_rule_recipient_rule_id"),
        table_name="work_report_reminder_rule_recipient",
    )
    op.drop_table("work_report_reminder_rule_recipient")
