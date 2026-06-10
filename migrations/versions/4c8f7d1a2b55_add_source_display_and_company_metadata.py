"""add source display and company metadata

Revision ID: 4c8f7d1a2b55
Revises: 15a2b6e9c4f1
Create Date: 2026-06-09 16:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4c8f7d1a2b55"
down_revision: Union[str, None] = "15a2b6e9c4f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("scrape_sources", sa.Column("display_name", sa.String(length=150), nullable=True))
    op.add_column("scrape_sources", sa.Column("company_name", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("scrape_sources", "company_name")
    op.drop_column("scrape_sources", "display_name")
