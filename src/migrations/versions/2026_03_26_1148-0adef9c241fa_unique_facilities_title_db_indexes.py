"""unique_facilities_title_db_indexes

Revision ID: 0adef9c241fa
Revises: 896c5d07d433
Create Date: 2026-03-26 11:48:07.901348

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "0adef9c241fa"
down_revision: Union[str, Sequence[str], None] = "896c5d07d433"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_unique_constraint("uq_facilities_title", "facilities", ["title"])

    # Performance indexes for bookings, rooms, and hotel_images
    op.execute("CREATE INDEX IF NOT EXISTS idx_bookings_user_id ON bookings (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_bookings_room_id ON bookings (room_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_bookings_date_from ON bookings (date_from)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_rooms_hotel_id ON rooms (hotel_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_hotel_images_hotel_id ON hotel_images (hotel_id)")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP INDEX IF EXISTS idx_hotel_images_hotel_id")
    op.execute("DROP INDEX IF EXISTS idx_rooms_hotel_id")
    op.execute("DROP INDEX IF EXISTS idx_bookings_date_from")
    op.execute("DROP INDEX IF EXISTS idx_bookings_room_id")
    op.execute("DROP INDEX IF EXISTS idx_bookings_user_id")
    op.drop_constraint("uq_facilities_title", "facilities", type_="unique")
