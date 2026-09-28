"""Add required quantity for stage techniques.

Revision ID: 9f2d6b7a4c31
Revises: 190867e1b504
"""

from alembic import op
import sqlalchemy as sa

revision = "9f2d6b7a4c31"
down_revision = "190867e1b504"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "stage_techniques",
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
    )
    op.create_check_constraint(
        "ck_stage_techniques_quantity_positive", "stage_techniques", "quantity >= 1"
    )
    op.alter_column("stage_techniques", "quantity", server_default=None)


def downgrade() -> None:
    op.drop_constraint(
        "ck_stage_techniques_quantity_positive", "stage_techniques", type_="check"
    )
    op.drop_column("stage_techniques", "quantity")
