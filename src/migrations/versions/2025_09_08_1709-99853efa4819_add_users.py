"""add users

Revision ID: 99853efa4819
Revises: 0b1179e48310
Create Date: 2025-09-08 17:09:42.963114

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "99853efa4819"
down_revision: Union[str, Sequence[str], None] = "0b1179e48310"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=200), nullable=False),
        sa.Column("hashed_password", sa.String(length=200), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("users")
