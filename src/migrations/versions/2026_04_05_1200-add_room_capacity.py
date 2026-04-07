"""add room capacity

Revision ID: a1b2c3d4e5f7
Revises: 2026_03_26_1148-0adef9c241fa
Create Date: 2026-04-05 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f7"
down_revision: Union[str, None] = "0adef9c241fa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "rooms",
        sa.Column("capacity", sa.Integer(), server_default="2", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("rooms", "capacity")
