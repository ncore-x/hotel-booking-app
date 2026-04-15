"""add oauth fields and make hashed_password nullable

Revision ID: d4e5f6a7b8c0
Revises: e5f6a7b8c9d0
Create Date: 2026-04-15 14:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4e5f6a7b8c0"
down_revision: Union[str, None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Make hashed_password nullable for OAuth users
    op.alter_column("users", "hashed_password", existing_type=sa.String(200), nullable=True)

    # Add OAuth columns
    op.add_column("users", sa.Column("oauth_provider", sa.String(20), nullable=True))
    op.add_column("users", sa.Column("oauth_id", sa.String(200), nullable=True))
    op.add_column("users", sa.Column("oauth_avatar_url", sa.String(500), nullable=True))

    # Partial unique index: only one account per (provider, oauth_id) pair
    op.create_index(
        "ix_users_oauth_provider_id",
        "users",
        ["oauth_provider", "oauth_id"],
        unique=True,
        postgresql_where=sa.text("oauth_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_users_oauth_provider_id", table_name="users")
    op.drop_column("users", "oauth_avatar_url")
    op.drop_column("users", "oauth_id")
    op.drop_column("users", "oauth_provider")
    op.alter_column("users", "hashed_password", existing_type=sa.String(200), nullable=False)
