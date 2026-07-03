"""make_ai_assistant_thread_user_exam_pk

Revision ID: fb8291f0df59
Revises: fa6ec1ea9bb7
Create Date: 2026-07-02 16:21:12.410070

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = 'fb8291f0df59'
down_revision = 'fa6ec1ea9bb7'
branch_labels = None
depends_on = None


def upgrade():
    # Drop the old single-column primary key and unique constraint on thread_id.
    op.drop_constraint('ai_assistant_thread_pkey', 'ai_assistant_thread', type_='primary')
    op.drop_constraint('ai_assistant_thread_thread_id_key', 'ai_assistant_thread', type_='unique')

    # Drop columns that are no longer needed.
    op.drop_column('ai_assistant_thread', 'id')
    op.drop_column('ai_assistant_thread', 'thread_id')

    # Use (user_id, exam_id) as the natural primary key.
    op.create_primary_key('ai_assistant_thread_pkey', 'ai_assistant_thread', ['user_id', 'exam_id'])


def downgrade():
    # Revert to the original schema with a synthetic id and thread_id.
    op.drop_constraint('ai_assistant_thread_pkey', 'ai_assistant_thread', type_='primary')

    op.add_column(
        'ai_assistant_thread',
        sa.Column('id', sa.Uuid(), nullable=False),
    )
    op.add_column(
        'ai_assistant_thread',
        sa.Column(
            'thread_id',
            sqlmodel.sql.sqltypes.AutoString(length=128),
            nullable=False,
        ),
    )

    op.create_primary_key('ai_assistant_thread_pkey', 'ai_assistant_thread', ['id'])
    op.create_unique_constraint(
        'ai_assistant_thread_thread_id_key',
        'ai_assistant_thread',
        ['thread_id'],
    )
