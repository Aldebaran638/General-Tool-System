"""replace_exam_description_with_trainers

Revision ID: 83f4a6b7c8d9
Revises: 72d7262fe510
Create Date: 2026-06-03 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '83f4a6b7c8d9'
down_revision = '72d7262fe510'
branch_labels = None
depends_on = None


def upgrade():
    # Add trainer_ids column (JSON) to exam table
    op.add_column('exam', sa.Column('trainer_ids', sa.JSON(), nullable=True))
    # Drop description column from exam table
    op.drop_column('exam', 'description')


def downgrade():
    # Re-add description column
    op.add_column('exam', sa.Column('description', sa.Text(), nullable=True))
    # Drop trainer_ids column
    op.drop_column('exam', 'trainer_ids')
