"""Seed the technique catalog recognized by the CV model.

Revision ID: 8e4b9f3d6a02
Revises: 7d3a8f2c5e91
"""

import re
import unicodedata

from alembic import op
import sqlalchemy as sa

revision = "8e4b9f3d6a02"
down_revision = "7d3a8f2c5e91"
branch_labels = None
depends_on = None


TECHNIQUES = (
    ("dump_truck", "Самосвал", ("dump truck", "dumptruck", "самосвал")),
    ("excavator", "Экскаватор", ("excavator", "экскаватор")),
    ("roller", "Каток", ("roller", "road roller", "каток", "дорожный каток")),
    (
        "crane",
        "Автокран",
        (
            "crane",
            "crane truck",
            "truck crane",
            "mobile crane",
            "автокран",
            "кран манипулятор",
        ),
    ),
    (
        "forklift",
        "Вилочный погрузчик",
        ("forklift", "fork lift", "forklift truck", "вилочный погрузчик"),
    ),
    (
        "loader",
        "Погрузчик",
        (
            "loader",
            "front loader",
            "wheel loader",
            "погрузчик",
            "фронтальный погрузчик",
        ),
    ),
    (
        "mixer",
        "Автобетоносмеситель",
        (
            "mixer",
            "concrete mixer",
            "mixer truck",
            "автобетоносмеситель",
            "бетономешалка",
        ),
    ),
    ("bulldozer", "Бульдозер", ("bulldozer", "бульдозер")),
    ("truck", "Грузовик", ("truck", "грузовик")),
)

techniques = sa.table(
    "techniques",
    sa.column("id", sa.Integer()),
    sa.column("name", sa.String()),
    sa.column("name_ru", sa.String()),
)


def _normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold().replace("ё", "е")
    return " ".join(part for part in re.split(r"[^\w]+|_+", normalized) if part)


def upgrade() -> None:
    connection = op.get_bind()
    rows = connection.execute(sa.select(techniques.c.name, techniques.c.name_ru)).all()
    known_labels = {
        _normalize(label)
        for row in rows
        for label in row
        if isinstance(label, str) and label.strip()
    }

    for name, name_ru, aliases in TECHNIQUES:
        normalized_aliases = {_normalize(alias) for alias in aliases}
        if known_labels.isdisjoint(normalized_aliases):
            connection.execute(techniques.insert().values(name=name, name_ru=name_ru))
            known_labels.update({_normalize(name), _normalize(name_ru)})


def downgrade() -> None:
    # Catalog rows may already be referenced by stages; never delete user data.
    pass
