"""add_ai_assistant_thread

Revision ID: fa6ec1ea9bb7
Revises: e5f6a7b8c9d0
Create Date: 2026-06-25 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes

# revision identifiers, used by Alembic.
revision = 'fa6ec1ea9bb7'
down_revision = 'e5f6a7b8c9d0'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('ai_assistant_thread',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('exam_id', sa.Uuid(), nullable=False),
        sa.Column('thread_id', sqlmodel.sql.sqltypes.AutoString(length=128), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('thread_id')
    )
    op.create_index(op.f('ix_ai_assistant_thread_exam_id'), 'ai_assistant_thread', ['exam_id'], unique=False)
    op.create_index(op.f('ix_ai_assistant_thread_user_id'), 'ai_assistant_thread', ['user_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_ai_assistant_thread_user_id'), table_name='ai_assistant_thread')
    op.drop_index(op.f('ix_ai_assistant_thread_exam_id'), table_name='ai_assistant_thread')
    op.drop_table('ai_assistant_thread')
