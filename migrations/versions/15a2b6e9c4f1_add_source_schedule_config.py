"""add source schedule config

Revision ID: 15a2b6e9c4f1
Revises: 9f3b2f4a8c11
Create Date: 2026-06-09 15:45:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "15a2b6e9c4f1"
down_revision: Union[str, None] = "9f3b2f4a8c11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "scrape_sources",
        sa.Column("schedule_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "scrape_sources",
        sa.Column("schedule_interval_hours", sa.Integer(), nullable=False, server_default="6"),
    )

    op.alter_column("scrape_sources", "schedule_enabled", server_default=None)
    op.alter_column("scrape_sources", "schedule_interval_hours", server_default=None)


def downgrade() -> None:
    op.drop_column("scrape_sources", "schedule_interval_hours")
    op.drop_column("scrape_sources", "schedule_enabled")
