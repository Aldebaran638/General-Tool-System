"""add invoice_match table

Revision ID: 6b683da4fd50
Revises: 16583fefb912
Create Date: 2026-04-26 03:07:12.132412

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = '6b683da4fd50'
down_revision = '16583fefb912'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'invoice_match',
        sa.Column('status', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('score_breakdown', sa.JSON(), nullable=False),
        sa.Column('review_reason', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('owner_id', sa.Uuid(), nullable=False),
        sa.Column('purchase_record_id', sa.Uuid(), nullable=False),
        sa.Column('invoice_file_id', sa.Uuid(), nullable=False),
        sa.Column('confirmed_by_id', sa.Uuid(), nullable=True),
        sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancelled_by_id', sa.Uuid(), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['cancelled_by_id'], ['user.id']),
        sa.ForeignKeyConstraint(['confirmed_by_id'], ['user.id']),
        sa.ForeignKeyConstraint(['invoice_file_id'], ['invoice_file.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['owner_id'], ['user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['purchase_record_id'], ['purchase_record.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(
        'ix_invoice_match_purchase_record_id_partial',
        'invoice_match',
        ['purchase_record_id'],
        unique=True,
        postgresql_where=sa.text("status IN ('confirmed', 'needs_review')")
    )


def downgrade():
    op.drop_index('ix_invoice_match_purchase_record_id_partial', table_name='invoice_match')
    op.drop_table('invoice_match')
