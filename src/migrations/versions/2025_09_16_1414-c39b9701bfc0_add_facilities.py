"""add facilities

Revision ID: c39b9701bfc0
Revises: 7832c167d7f2
Create Date: 2025-09-16 14:14:17.827572

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c39b9701bfc0"
down_revision: Union[str, Sequence[str], None] = "7832c167d7f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "facilities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "rooms_facilities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("room_id", sa.Integer(), nullable=False),
        sa.Column("facilities_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["facilities_id"],
            ["facilities.id"],
        ),
        sa.ForeignKeyConstraint(
            ["room_id"],
            ["rooms.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("rooms_facilities")
    op.drop_table("facilities")
