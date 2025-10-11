"""add ON DELETE CASCADE to rooms_facilities.room_id

Revision ID: 6688f55c2da4
Revises: 0659dde83f20
Create Date: 2025-10-10 14:57:52.112277

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6688f55c2da4"
down_revision: Union[str, Sequence[str], None] = "0659dde83f20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Удаляем старый FK без каскада
    op.drop_constraint(
        "rooms_facilities_room_id_fkey",
        "rooms_facilities",
        type_="foreignkey"
    )

    # Создаём новый FK с ON DELETE CASCADE
    op.create_foreign_key(
        "rooms_facilities_room_id_fkey",
        "rooms_facilities",
        "rooms",
        ["room_id"],
        ["id"],
        ondelete="CASCADE"
    )


def downgrade() -> None:
    # Возвращаем FK без ON DELETE CASCADE
    op.drop_constraint(
        "rooms_facilities_room_id_fkey",
        "rooms_facilities",
        type_="foreignkey"
    )

    op.create_foreign_key(
        "rooms_facilities_room_id_fkey",
        "rooms_facilities",
        "rooms",
        ["room_id"],
        ["id"]
    )
