"""add_hotel_images_and_hotels_unique_constraint

Revision ID: a1b2c3d4e5f6
Revises: 761c2d8366be
Create Date: 2026-03-25 20:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "761c2d8366be"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Unique constraint on hotels(title, location)
    op.create_unique_constraint(
        "uq_hotels_title_location", "hotels", ["title", "location"]
    )

    # hotel_images table
    op.create_table(
        "hotel_images",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("hotel_id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(length=500), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["hotel_id"], ["hotels.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_hotel_images_hotel_id", "hotel_images", ["hotel_id"])


def downgrade() -> None:
    op.drop_index("ix_hotel_images_hotel_id", table_name="hotel_images")
    op.drop_table("hotel_images")
    op.drop_constraint("uq_hotels_title_location", "hotels", type_="unique")
