"""add job type and tags to job listings

Revision ID: 6d5f5a3f5d3b
Revises: d87b25596140
Create Date: 2026-06-09 12:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "6d5f5a3f5d3b"
down_revision: Union[str, None] = "d87b25596140"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "job_listings",
        sa.Column("job_type", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "job_listings",
        sa.Column("tags", postgresql.ARRAY(sa.String(length=100)), nullable=True),
    )
    op.create_index(op.f("ix_job_listings_job_type"), "job_listings", ["job_type"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_job_listings_job_type"), table_name="job_listings")
    op.drop_column("job_listings", "tags")
    op.drop_column("job_listings", "job_type")
