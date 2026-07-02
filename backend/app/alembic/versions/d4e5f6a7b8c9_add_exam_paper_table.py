"""add_exam_paper_table

Revision ID: d4e5f6a7b8c9
Revises: 83f4a6b7c8d9
Create Date: 2026-06-03 17:10:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes

# revision identifiers, used by Alembic.
revision = 'd4e5f6a7b8c9'
down_revision = '83f4a6b7c8d9'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('exam_paper',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('exam_id', sa.Uuid(), nullable=False),
        sa.Column('docx_path', sqlmodel.sql.sqltypes.AutoString(length=512), nullable=True),
        sa.Column('status', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['exam_id'], ['exam.id']),
    )
    op.create_index(op.f('ix_exam_paper_exam_id'), 'exam_paper', ['exam_id'], unique=True)


def downgrade():
    op.drop_index(op.f('ix_exam_paper_exam_id'), table_name='exam_paper')
    op.drop_table('exam_paper')
