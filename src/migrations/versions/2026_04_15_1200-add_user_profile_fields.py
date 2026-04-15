"""add user profile fields

Revision ID: e5f6a7b8c9d0
Revises: c3d4e5f6a7b9
Create Date: 2026-04-15 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, None] = "c3d4e5f6a7b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("first_name", sa.String(100), nullable=True))
    op.add_column("users", sa.Column("last_name", sa.String(100), nullable=True))
    op.add_column("users", sa.Column("phone", sa.String(30), nullable=True))
    op.add_column("users", sa.Column("birth_date", sa.Date(), nullable=True))
    op.add_column("users", sa.Column("gender", sa.String(10), nullable=True))
    op.add_column("users", sa.Column("citizenship", sa.String(100), nullable=True))
    op.add_column("users", sa.Column("avatar_filename", sa.String(200), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "avatar_filename")
    op.drop_column("users", "citizenship")
    op.drop_column("users", "gender")
    op.drop_column("users", "birth_date")
    op.drop_column("users", "phone")
    op.drop_column("users", "last_name")
    op.drop_column("users", "first_name")
