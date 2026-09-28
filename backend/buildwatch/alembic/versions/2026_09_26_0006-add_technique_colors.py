"""Привязка цвета к технике для отрисовки bbox.

Revision ID: a1b2c3d4e5f6
Revises: 8e4b9f3d6a02
"""

from alembic import op
import sqlalchemy as sa

from buildwatch.techniques.colors import CV_CLASS_COLORS, generate_color

revision = "a1b2c3d4e5f6"
down_revision = "8e4b9f3d6a02"
branch_labels = None
depends_on = None

techniques = sa.table(
    "techniques",
    sa.column("id", sa.Integer()),
    sa.column("name_ru", sa.String()),
    sa.column("color", sa.String()),
)


def upgrade() -> None:
    op.add_column("techniques", sa.Column("color", sa.String(7), nullable=True))
    connection = op.get_bind()
    rows = connection.execute(sa.select(techniques.c.id, techniques.c.name_ru)).all()
    for row_id, name_ru in rows:
        color = CV_CLASS_COLORS.get(name_ru or "", generate_color(name_ru or str(row_id)))
        connection.execute(
            techniques.update().where(techniques.c.id == row_id).values(color=color)
        )
    with op.batch_alter_table("techniques") as batch:
        batch.alter_column("color", existing_type=sa.String(7), nullable=False)


def downgrade() -> None:
    op.drop_column("techniques", "color")
