"""Add description and embedding to jobs

Revision ID: 1f2354785481
Revises: 632dbda642b9
Create Date: 2026-10-19 15:12:33.243953

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import pgvector.sqlalchemy.vector


# revision identifiers, used by Alembic.
revision: str = '1f2354785481'
down_revision: Union[str, None] = '632dbda642b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('jobs', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('jobs', sa.Column('embedding', pgvector.sqlalchemy.vector.VECTOR(dim=1536), nullable=True))


def downgrade() -> None:
    op.drop_column('jobs', 'embedding')
    op.drop_column('jobs', 'description')