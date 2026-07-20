"""add user language preference

Revision ID: 000000000002
Revises: 000000000001
Create Date: 2026-07-20 00:00:00.000000

"""

import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from alembic import op

# revision identifiers, used by Alembic.
revision = "000000000002"
down_revision = "000000000001"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "user",
        sa.Column(
            "language",
            sqlmodel.sql.sqltypes.AutoString(length=10),
            nullable=False,
            server_default="zh",
        ),
    )


def downgrade():
    op.drop_column("user", "language")
