"""add name_ru for techniques

Revision ID: 0e1e340b21a1
Revises: a9bc01684615
Create Date: 2026-09-20 17:18:53.901206

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0e1e340b21a1"
down_revision: Union[str, Sequence[str], None] = "a9bc01684615"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "techniques",
        sa.Column("name_ru", sa.String(length=127), nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("techniques", "name_ru")
