"""add exam_attempt, exam_answer, exam_paper_snapshot tables

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-02 00:00:00.000000+00:00
"""

from alembic import op
import sqlalchemy as sa
import sqlmodel

revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # exam_paper_snapshot
    op.create_table(
        "exam_paper_snapshot",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("exam_id", sa.Uuid(), nullable=False),
        sa.Column("snapshot_json", sa.JSON(), nullable=False),
        sa.Column("total_score", sa.Float(), nullable=False),
        sa.Column("question_count", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["exam_id"], ["exam.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_exam_paper_snapshot_exam_id", "exam_paper_snapshot", ["exam_id"]
    )

    # exam_attempt
    op.create_table(
        "exam_attempt",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("exam_id", sa.Uuid(), nullable=False),
        sa.Column("userid", sqlmodel.AutoString(length=64), nullable=False),
        sa.Column("attempt_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "status",
            sqlmodel.AutoString(length=20),
            nullable=False,
            server_default="IN_PROGRESS",
        ),
        sa.Column("total_score", sa.Float(), nullable=False),
        sa.Column("max_score", sa.Float(), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("correct_count", sa.Integer(), nullable=False),
        sa.Column("total_count", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expire_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "submitted_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("question_order_snapshot", sa.JSON(), nullable=True),
        sa.Column("option_order_snapshot", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["exam_id"], ["exam.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_exam_attempt_exam_id", "exam_attempt", ["exam_id"])
    op.create_index("ix_exam_attempt_userid", "exam_attempt", ["userid"])
    op.create_index(
        "ix_exam_attempt_exam_userid_status",
        "exam_attempt",
        ["exam_id", "userid", "status"],
    )

    # exam_answer
    op.create_table(
        "exam_answer",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("attempt_id", sa.Uuid(), nullable=False),
        sa.Column("question_id", sa.Uuid(), nullable=False),
        sa.Column("selected_option_ids", sa.JSON(), nullable=False),
        sa.Column(
            "is_correct", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column("score_awarded", sa.Float(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["attempt_id"], ["exam_attempt.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["question_id"], ["question.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_exam_answer_attempt_id", "exam_answer", ["attempt_id"])
    op.create_index("ix_exam_answer_question_id", "exam_answer", ["question_id"])

    # Add columns to exam_participant
    op.add_column(
        "exam_participant",
        sa.Column(
            "completion_status",
            sqlmodel.AutoString(length=20),
            nullable=False,
            server_default="NOT_STARTED",
        ),
    )
    op.add_column(
        "exam_participant", sa.Column("final_score", sa.Float(), nullable=True)
    )
    op.add_column(
        "exam_participant",
        sa.Column("final_passed", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "exam_participant", sa.Column("final_attempt_id", sa.Uuid(), nullable=True)
    )
    op.add_column(
        "exam_participant",
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_exam_participant_final_attempt",
        "exam_participant",
        "exam_attempt",
        ["final_attempt_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Add paper_snapshot_id to exam
    op.add_column("exam", sa.Column("paper_snapshot_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_exam_paper_snapshot",
        "exam",
        "exam_paper_snapshot",
        ["paper_snapshot_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_exam_paper_snapshot", "exam", type_="foreignkey")
    op.drop_column("exam", "paper_snapshot_id")

    op.drop_constraint(
        "fk_exam_participant_final_attempt", "exam_participant", type_="foreignkey"
    )
    op.drop_column("exam_participant", "completed_at")
    op.drop_column("exam_participant", "final_attempt_id")
    op.drop_column("exam_participant", "final_passed")
    op.drop_column("exam_participant", "final_score")
    op.drop_column("exam_participant", "completion_status")

    op.drop_index("ix_exam_answer_question_id", table_name="exam_answer")
    op.drop_index("ix_exam_answer_attempt_id", table_name="exam_answer")
    op.drop_table("exam_answer")

    op.drop_index("ix_exam_attempt_exam_userid_status", table_name="exam_attempt")
    op.drop_index("ix_exam_attempt_userid", table_name="exam_attempt")
    op.drop_index("ix_exam_attempt_exam_id", table_name="exam_attempt")
    op.drop_table("exam_attempt")

    op.drop_index(
        "ix_exam_paper_snapshot_exam_id", table_name="exam_paper_snapshot"
    )
    op.drop_table("exam_paper_snapshot")
