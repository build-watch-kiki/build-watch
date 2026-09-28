"""Детерминированные цвета техники — единый источник для отрисовки bbox.

Фиксированная палитра покрывает 9 классов, которые реально отдает CV.
Для всех остальных случаев (новые классы, technique=None) цвет
генерируется детерминированно через sha256 -> hue, поэтому количество
техники не ограничено.
"""

import colorsys
import hashlib
import re

HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")

# 9 готовых CV-классов
CV_CLASS_COLORS: dict[str, str] = {
    "Самосвал": "#FF0000",  # Dump truck
    "Экскаватор": "#0080FF",  # Excavator
    "Каток": "#FF007E",  # Roller
    "Автокран": "#00FFC9",  # crane_truck
    "Вилочный погрузчик": "#18FF00",  # forklift
    "Погрузчик": "#C3C806",  # loader
    "Автобетоносмеситель": "#FF00FF",  # Mixer
    "Бульдозер": "#B1FF00",  # Bulldozer
    "Грузовик": "#FF8000",  # Truck
}


def validate_hex_color(value: str) -> str:
    """Проверка формата #RRGGBB, возврат в верхнем регистре."""
    if not HEX_RE.match(value):
        raise ValueError(f"Bad hex color: {value!r}, expected #RRGGBB")
    return value.upper()


def generate_color(key: str | int) -> str:
    """Детерминированный цвет для произвольного ключа (без лимита количества)."""
    digest = hashlib.sha256(str(key).encode("utf-8")).digest()
    hue = int.from_bytes(digest[:2], "big") / 65535.0
    r, g, b = colorsys.hls_to_rgb(hue, 0.5, 0.7)
    return f"#{int(r * 255):02X}{int(g * 255):02X}{int(b * 255):02X}"


def resolve_color(
    name_ru: str | None = None,
    key: str | int = "",
    explicit: str | None = None,
) -> str:
    """Приоритет: explicit -> фиксированная палитра -> генератор."""
    if explicit:
        return validate_hex_color(explicit)
    if name_ru and name_ru in CV_CLASS_COLORS:
        return CV_CLASS_COLORS[name_ru]
    return generate_color(name_ru or key)
