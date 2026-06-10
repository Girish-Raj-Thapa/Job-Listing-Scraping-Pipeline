"""add source retry and rate limit config

Revision ID: 9f3b2f4a8c11
Revises: 6d5f5a3f5d3b
Create Date: 2026-06-09 15:15:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9f3b2f4a8c11"
down_revision: Union[str, None] = "6d5f5a3f5d3b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "scrape_sources",
        sa.Column("rate_limit_seconds", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "scrape_sources",
        sa.Column("request_timeout_seconds", sa.Integer(), nullable=False, server_default="30"),
    )
    op.add_column(
        "scrape_sources",
        sa.Column("max_retries", sa.Integer(), nullable=False, server_default="3"),
    )
    op.add_column(
        "scrape_sources",
        sa.Column("retry_backoff_seconds", sa.Integer(), nullable=False, server_default="30"),
    )

    op.alter_column("scrape_sources", "rate_limit_seconds", server_default=None)
    op.alter_column("scrape_sources", "request_timeout_seconds", server_default=None)
    op.alter_column("scrape_sources", "max_retries", server_default=None)
    op.alter_column("scrape_sources", "retry_backoff_seconds", server_default=None)


def downgrade() -> None:
    op.drop_column("scrape_sources", "retry_backoff_seconds")
    op.drop_column("scrape_sources", "max_retries")
    op.drop_column("scrape_sources", "request_timeout_seconds")
    op.drop_column("scrape_sources", "rate_limit_seconds")
