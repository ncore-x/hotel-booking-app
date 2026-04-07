"""split hotel location into city and address

Revision ID: b2c3d4e5f6a8
Revises: a1b2c3d4e5f7
Create Date: 2026-04-06 09:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b2c3d4e5f6a8"
down_revision: Union[str, None] = "a1b2c3d4e5f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add new columns
    op.add_column("hotels", sa.Column("city", sa.String(), nullable=True))
    op.add_column("hotels", sa.Column("address", sa.String(), nullable=True))

    # 2. Migrate data: split location on first comma
    op.execute("""
        UPDATE hotels SET
            city    = TRIM(SPLIT_PART(location, ',', 1)),
            address = CASE
                WHEN location LIKE '%,%'
                THEN TRIM(SUBSTRING(location FROM POSITION(',' IN location) + 1))
                ELSE NULL
            END
    """)

    # 3. Make city NOT NULL
    op.alter_column("hotels", "city", nullable=False)

    # 4. Drop old unique constraint and column
    op.drop_constraint("uq_hotels_title_location", "hotels", type_="unique")
    op.drop_column("hotels", "location")

    # 5. Add new unique constraint
    op.create_unique_constraint(
        "uq_hotels_title_city_address",
        "hotels",
        ["title", "city", "address"],
    )


def downgrade() -> None:
    op.add_column("hotels", sa.Column("location", sa.String(), nullable=True))
    op.execute("""
        UPDATE hotels SET
            location = CASE
                WHEN address IS NOT NULL AND address != ''
                THEN city || ', ' || address
                ELSE city
            END
    """)
    op.alter_column("hotels", "location", nullable=False)
    op.drop_constraint("uq_hotels_title_city_address", "hotels", type_="unique")
    op.drop_column("hotels", "city")
    op.drop_column("hotels", "address")
    op.create_unique_constraint(
        "uq_hotels_title_location",
        "hotels",
        ["title", "location"],
    )
