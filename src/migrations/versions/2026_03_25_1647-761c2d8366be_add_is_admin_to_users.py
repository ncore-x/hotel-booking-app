"""add_is_admin_to_users

Revision ID: 761c2d8366be
Revises: 6688f55c2da4
Create Date: 2026-03-25 16:47:30.891486

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "761c2d8366be"
down_revision: Union[str, Sequence[str], None] = "6688f55c2da4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_admin", sa.Boolean(), server_default="false", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("users", "is_admin")
