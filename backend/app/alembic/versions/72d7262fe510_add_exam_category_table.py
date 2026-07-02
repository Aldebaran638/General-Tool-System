"""add_exam_category_table

Revision ID: 72d7262fe510
Revises: b2c3d4e5f6a7
Create Date: 2026-06-03 09:05:43.289819

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes

# revision identifiers, used by Alembic.
revision = '72d7262fe510'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade():
    # Create exam_category table
    op.create_table('exam_category',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=128), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )

    # Add category_id column to exam table
    op.add_column('exam', sa.Column('category_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_exam_category_id'), 'exam', ['category_id'], unique=False)
    op.create_foreign_key(None, 'exam', 'exam_category', ['category_id'], ['id'])


def downgrade():
    # Remove category_id from exam
    op.drop_constraint(None, 'exam', type_='foreignkey')
    op.drop_index(op.f('ix_exam_category_id'), table_name='exam')
    op.drop_column('exam', 'category_id')

    # Drop exam_category table
    op.drop_table('exam_category')
