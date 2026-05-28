"""add exam management tables

Revision ID: a1b2c3d4e5f6
Revises: c7d8e9f0a1b2
Create Date: 2026-05-28 00:00:00.000000+00:00
"""

from alembic import op
import sqlalchemy as sa
import sqlmodel

revision = "a1b2c3d4e5f6"
down_revision = "c7d8e9f0a1b2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # exam
    op.create_table(
        "exam",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sqlmodel.AutoString(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sqlmodel.AutoString(length=16),
            nullable=False,
            server_default="DRAFT",
        ),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column(
            "attempt_limit_type",
            sqlmodel.AutoString(length=16),
            nullable=False,
            server_default="UNLIMITED",
        ),
        sa.Column("attempt_limit_count", sa.Integer(), nullable=True),
        sa.Column("pass_score", sa.Float(), nullable=False),
        sa.Column(
            "submit_rule",
            sqlmodel.AutoString(length=16),
            nullable=False,
            server_default="ALL_REQUIRED",
        ),
        sa.Column("show_answer", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "random_question_order",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
        sa.Column(
            "random_option_order",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["created_by"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_exam_status", "exam", ["status"])

    # question
    op.create_table(
        "question",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("exam_id", sa.Uuid(), nullable=False),
        sa.Column(
            "question_type",
            sqlmodel.AutoString(length=16),
            nullable=False,
        ),
        sa.Column("stem", sa.Text(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("sort_no", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("analysis", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["exam_id"], ["exam.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_question_exam_id", "question", ["exam_id"])

    # question_option
    op.create_table(
        "question_option",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("question_id", sa.Uuid(), nullable=False),
        sa.Column("option_key", sqlmodel.AutoString(length=4), nullable=False),
        sa.Column("option_text", sa.Text(), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("sort_no", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["question_id"], ["question.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_question_option_question_id", "question_option", ["question_id"]
    )

    # exam_participant
    op.create_table(
        "exam_participant",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("exam_id", sa.Uuid(), nullable=False),
        sa.Column("userid", sqlmodel.AutoString(length=64), nullable=False),
        sa.Column("name_snapshot", sqlmodel.AutoString(length=255), nullable=True),
        sa.Column("center_snapshot", sqlmodel.AutoString(length=128), nullable=True),
        sa.Column(
            "department_snapshot", sqlmodel.AutoString(length=128), nullable=True
        ),
        sa.Column(
            "position_snapshot", sqlmodel.AutoString(length=128), nullable=True
        ),
        sa.Column("wecom_status_snapshot", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["exam_id"], ["exam.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("exam_id", "userid", name="uq_exam_participant_exam_userid"),
    )
    op.create_index("ix_exam_participant_exam_id", "exam_participant", ["exam_id"])
    op.create_index("ix_exam_participant_userid", "exam_participant", ["userid"])


def downgrade() -> None:
    op.drop_table("exam_participant")
    op.drop_index("ix_question_option_question_id", table_name="question_option")
    op.drop_table("question_option")
    op.drop_index("ix_question_exam_id", table_name="question")
    op.drop_table("question")
    op.drop_index("ix_exam_status", table_name="exam")
    op.drop_table("exam")
