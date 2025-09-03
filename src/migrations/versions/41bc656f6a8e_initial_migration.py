"""initial migration

Revision ID: 41bc656f6a8e
Revises:
Create Date: 2025-09-03 18:50:50.846985

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '41bc656f6a8e'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('hotels',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('title', sa.String(length=100), nullable=False),
                    sa.Column('location', sa.String(), nullable=False),
                    sa.PrimaryKeyConstraint('id')
                    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('hotels')
