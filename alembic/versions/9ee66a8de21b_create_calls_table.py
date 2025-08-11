"""create calls table

Revision ID: 9ee66a8de21b
Revises: 8551bb04f524
Create Date: 2025-08-08 17:05:29.633430

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9ee66a8de21b"
down_revision: Union[str, Sequence[str], None] = "8551bb04f524"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        "calls",
        sa.Column("call_id", sa.UUID(), nullable=False),
        sa.Column("agent_id", sa.String(), nullable=True),
        sa.Column("customer_id", sa.String(), nullable=True),
        sa.Column("language", sa.String(), nullable=True),
        sa.Column("start_time", sa.DateTime(), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("transcript", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("call_id"),
    )
    op.create_index("ix_calls_agent_id", "calls", ["agent_id"], unique=False)
    op.create_index("ix_calls_start_time", "calls", ["start_time"], unique=False)
    # I am going ahead with pg_trgm, because it provides a fuzzy search which is typo tolerant.
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
    op.create_index(
        "ix_calls_transcript_gin",
        "calls",
        ["transcript"],
        postgresql_using="gin",
        postgresql_ops={"transcript": "gin_trgm_ops"},
    )


def downgrade() -> None:
    op.drop_index("ix_calls_transcript_gin", table_name="calls")
    op.drop_index("ix_calls_start_time", table_name="calls")
    op.drop_index("ix_calls_agent_id", table_name="calls")
    op.drop_table("calls")
