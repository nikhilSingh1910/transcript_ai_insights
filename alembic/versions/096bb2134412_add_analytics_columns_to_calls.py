"""add analytics columns to calls

Revision ID: 096bb2134412
Revises: 9ee66a8de21b
Create Date: 2025-08-08 17:19:48.560265

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "096bb2134412"
down_revision: Union[str, Sequence[str], None] = "9ee66a8de21b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column(
        "calls", sa.Column("embedding", postgresql.ARRAY(sa.Float), nullable=True)
    )
    op.add_column("calls", sa.Column("agent_talk_ratio", sa.Float, nullable=True))
    op.add_column(
        "calls", sa.Column("customer_sentiment_score", sa.Float, nullable=True)
    )


def downgrade():
    op.drop_column("calls", "customer_sentiment_score")
    op.drop_column("calls", "agent_talk_ratio")
    op.drop_column("calls", "embedding")
