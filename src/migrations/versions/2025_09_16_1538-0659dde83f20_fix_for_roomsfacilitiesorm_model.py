"""fix for RoomsFacilitiesOrm model

Revision ID: 0659dde83f20
Revises: c39b9701bfc0
Create Date: 2025-09-16 15:38:00.836455

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0659dde83f20"
down_revision: Union[str, Sequence[str], None] = "c39b9701bfc0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "rooms_facilities", sa.Column(
            "facility_id", sa.Integer(), nullable=False)
    )
    op.drop_constraint(
        op.f("rooms_facilities_facilities_id_fkey"),
        "rooms_facilities",
        type_="foreignkey",
    )
    op.create_foreign_key(
        None, "rooms_facilities", "facilities", ["facility_id"], ["id"]
    )
    op.drop_column("rooms_facilities", "facilities_id")


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column(
        "rooms_facilities",
        sa.Column("facilities_id", sa.INTEGER(),
                  autoincrement=False, nullable=False),
    )
    op.drop_constraint(None, "rooms_facilities", type_="foreignkey")
    op.create_foreign_key(
        op.f("rooms_facilities_facilities_id_fkey"),
        "rooms_facilities",
        "facilities",
        ["facilities_id"],
        ["id"],
    )
    op.drop_column("rooms_facilities", "facility_id")
