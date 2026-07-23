"""harden feishu login

Revision ID: 000000000005
Revises: 000000000004
Create Date: 2026-07-23 00:00:00.000000

"""

import secrets

import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from alembic import op

from app.core.security import get_password_hash

revision = "000000000005"
down_revision = "000000000004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    users_without_password = connection.execute(
        sa.text('SELECT id FROM "user" WHERE hashed_password IS NULL')
    ).fetchall()
    for (user_id,) in users_without_password:
        connection.execute(
            sa.text(
                'UPDATE "user" SET hashed_password = :hashed_password WHERE id = :id'
            ),
            {
                "id": user_id,
                "hashed_password": get_password_hash(secrets.token_urlsafe(32)),
            },
        )

    op.alter_column(
        "user",
        "hashed_password",
        existing_type=sqlmodel.sql.sqltypes.AutoString(),
        nullable=False,
    )
    op.drop_index(op.f("ix_user_feishu_user_id"), table_name="user")
    op.alter_column(
        "user",
        "feishu_user_id",
        new_column_name="feishu_open_id",
        existing_type=sqlmodel.sql.sqltypes.AutoString(length=128),
        existing_nullable=True,
    )
    op.create_index(
        op.f("ix_user_feishu_open_id"),
        "user",
        ["feishu_open_id"],
        unique=True,
    )

    op.drop_constraint(
        "feishu_login_ticket_user_id_fkey",
        "feishu_login_ticket",
        type_="foreignkey",
    )
    op.create_foreign_key(
        op.f("fk_feishu_login_ticket_user_id_user"),
        "feishu_login_ticket",
        "user",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("fk_feishu_login_ticket_user_id_user"),
        "feishu_login_ticket",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "feishu_login_ticket_user_id_fkey",
        "feishu_login_ticket",
        "user",
        ["user_id"],
        ["id"],
    )

    op.drop_index(op.f("ix_user_feishu_open_id"), table_name="user")
    op.alter_column(
        "user",
        "feishu_open_id",
        new_column_name="feishu_user_id",
        existing_type=sqlmodel.sql.sqltypes.AutoString(length=128),
        existing_nullable=True,
    )
    op.create_index(
        op.f("ix_user_feishu_user_id"),
        "user",
        ["feishu_user_id"],
        unique=True,
    )
    op.alter_column(
        "user",
        "hashed_password",
        existing_type=sqlmodel.sql.sqltypes.AutoString(),
        nullable=True,
    )
