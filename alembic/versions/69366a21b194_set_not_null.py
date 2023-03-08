"""set not null

Revision ID: 69366a21b194
Revises: ee011f74a986
Create Date: 2023-03-10 03:20:49.551296

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '69366a21b194'
down_revision = 'ee011f74a986'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        'post_category', 'name',
        existing_type=sa.VARCHAR(length=128),
        nullable=False
    )
    op.alter_column(
        'post_tag', 'name',
        existing_type=sa.VARCHAR(length=128),
        nullable=False
    )
    op.alter_column(
        'resource', 'title',
        existing_type=sa.VARCHAR(length=255),
        nullable=False
    )
    op.alter_column(
        'resource', 'url',
        existing_type=sa.VARCHAR(length=255),
        nullable=False
    )
    op.alter_column(
        'sys_permission', 'name',
        existing_type=sa.VARCHAR(length=20),
        nullable=False,
        comment=None,
        existing_comment='permission name'
    )
    op.alter_column(
        'sys_role', 'name',
        existing_type=sa.VARCHAR(length=20),
        nullable=False,
        comment=None,
        existing_comment='role name'
    )
    op.alter_column(
        'sys_user', 'username',
        existing_type=sa.VARCHAR(length=20),
        nullable=False,
        comment=None,
        existing_comment='username'
    )
    op.alter_column(
        'sys_user', 'email',
        existing_type=sa.VARCHAR(length=128),
        nullable=False,
        comment=None,
        existing_comment='email'
    )
    op.alter_column(
        'sys_user', 'password_hash',
        existing_type=postgresql.BYTEA(),
        nullable=False,
        comment=None,
        existing_comment='password hash'
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        'sys_user', 'password_hash',
        existing_type=postgresql.BYTEA(),
        nullable=True,
        comment='password hash'
    )
    op.alter_column(
        'sys_user', 'email',
        existing_type=sa.VARCHAR(length=128),
        nullable=True,
        comment='email'
    )
    op.alter_column(
        'sys_user', 'username',
        existing_type=sa.VARCHAR(length=20),
        nullable=True,
        comment='username'
    )
    op.alter_column(
        'sys_role', 'name',
        existing_type=sa.VARCHAR(length=20),
        nullable=True,
        comment='role name'
    )
    op.alter_column(
        'sys_permission', 'name',
        existing_type=sa.VARCHAR(length=20),
        nullable=True,
        comment='permission name'
    )
    op.alter_column(
        'resource', 'url',
        existing_type=sa.VARCHAR(length=255),
        nullable=True
    )
    op.alter_column(
        'resource', 'title',
        existing_type=sa.VARCHAR(length=255),
        nullable=True
    )
    op.alter_column(
        'post_tag', 'name',
        existing_type=sa.VARCHAR(length=128),
        nullable=True
    )
    op.alter_column(
        'post_category', 'name',
        existing_type=sa.VARCHAR(length=128),
        nullable=True
    )
    # ### end Alembic commands ###
