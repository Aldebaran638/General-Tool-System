"""add_question_bank_management_tables

Revision ID: a3cab8ecd49f
Revises: fb8291f0df59
Create Date: 2026-07-03 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision = "a3cab8ecd49f"
down_revision = "fb8291f0df59"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "question_bank_set",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sqlmodel.AutoString(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=False),
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
        sa.ForeignKeyConstraint(["category_id"], ["exam_category.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_question_bank_set_category_id"),
        "question_bank_set",
        ["category_id"],
        unique=False,
    )

    op.create_table(
        "question_bank_question",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("set_id", sa.Uuid(), nullable=False),
        sa.Column(
            "question_type",
            sqlmodel.AutoString(length=16),
            nullable=False,
        ),
        sa.Column("stem", sa.Text(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column(
            "difficulty",
            sqlmodel.AutoString(length=10),
            nullable=False,
            server_default="MEDIUM",
        ),
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
        sa.ForeignKeyConstraint(
            ["set_id"], ["question_bank_set.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_question_bank_question_set_id"),
        "question_bank_question",
        ["set_id"],
        unique=False,
    )

    op.create_table(
        "question_bank_option",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("question_id", sa.Uuid(), nullable=False),
        sa.Column(
            "option_key",
            sqlmodel.AutoString(length=4),
            nullable=False,
        ),
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
            ["question_id"], ["question_bank_question.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_question_bank_option_question_id"),
        "question_bank_option",
        ["question_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_question_bank_option_question_id"),
        table_name="question_bank_option",
    )
    op.drop_table("question_bank_option")
    op.drop_index(
        op.f("ix_question_bank_question_set_id"),
        table_name="question_bank_question",
    )
    op.drop_table("question_bank_question")
    op.drop_index(
        op.f("ix_question_bank_set_category_id"),
        table_name="question_bank_set",
    )
    op.drop_table("question_bank_set")
