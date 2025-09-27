"""make email unique

Revision ID: 6068eeb7cdae
Revises: 99853efa4819
Create Date: 2025-09-08 18:25:26.278543

"""

from typing import Sequence, Union

from alembic import op


revision: str = "6068eeb7cdae"
down_revision: Union[str, Sequence[str], None] = "99853efa4819"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_unique_constraint(None, "users", ["email"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(None, "users", type_="unique")  # type: ignore
