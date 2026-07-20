"""add okr

Revision ID: 000000000003
Revises: 000000000002
Create Date: 2026-07-20 07:11:33.157886

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = '000000000003'
down_revision = '000000000002'
branch_labels = None
depends_on = None


def upgrade():
    # id 永远是第一列，外键 id 紧随其后（项目约定）
    op.create_table('department',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
    sa.Column('description', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
    sa.Column('sort_order', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_department_name'), 'department', ['name'], unique=True)
    op.create_table('objective',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_by_id', sa.Uuid(), nullable=False),
    sa.Column('title', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['created_by_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('key_result',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('objective_id', sa.Uuid(), nullable=False),
    sa.Column('assignee_id', sa.Uuid(), nullable=False),
    sa.Column('title', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('start_date', sa.Date(), nullable=False),
    sa.Column('deadline', sa.Date(), nullable=False),
    sa.Column('progress', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['assignee_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['objective_id'], ['objective.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_key_result_assignee_id'), 'key_result', ['assignee_id'], unique=False)
    op.create_index(op.f('ix_key_result_objective_id'), 'key_result', ['objective_id'], unique=False)
    op.add_column('user', sa.Column('department_id', sa.Uuid(), nullable=True))
    op.create_foreign_key('fk_user_department_id_department', 'user', 'department', ['department_id'], ['id'])


def downgrade():
    op.drop_constraint('fk_user_department_id_department', 'user', type_='foreignkey')
    op.drop_column('user', 'department_id')
    op.drop_index(op.f('ix_key_result_objective_id'), table_name='key_result')
    op.drop_index(op.f('ix_key_result_assignee_id'), table_name='key_result')
    op.drop_table('key_result')
    op.drop_table('objective')
    op.drop_index(op.f('ix_department_name'), table_name='department')
    op.drop_table('department')
