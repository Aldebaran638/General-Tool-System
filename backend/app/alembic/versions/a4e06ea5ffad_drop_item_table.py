"""drop item table

Revision ID: a4e06ea5ffad
Revises: 6b683da4fd50
Create Date: 2026-04-26 07:41:01.462060

"""

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a4e06ea5ffad'
down_revision = '6b683da4fd50'
branch_labels = None
depends_on = None


def upgrade():
    # Drop the item table if it exists. CASCADE cleans up indexes and constraints.
    op.execute("DROP TABLE IF EXISTS item CASCADE")

    # Clean up any enum type that was only used by the item table.
    op.execute("DROP TYPE IF EXISTS itemstate CASCADE")


def downgrade():
    # Re-create the item table with the final schema prior to removal.
    # This matches the structure defined in the deleted project_management module.
    op.create_table(
        'item',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            server_default=sa.text('uuid_generate_v4()'),
            nullable=False,
        ),
        sa.Column(
            'title',
            sqlmodel.sql.sqltypes.AutoString(length=255),
            nullable=False,
        ),
        sa.Column(
            'description',
            sqlmodel.sql.sqltypes.AutoString(length=255),
            nullable=True,
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            'owner_id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column('amount', sa.Float(), nullable=True),
        sa.Column('test_amount', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(
            ['owner_id'],
            ['user.id'],
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id'),
    )
