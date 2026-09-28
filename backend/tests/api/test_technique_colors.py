import pytest

from buildwatch.techniques.colors import (
    CV_CLASS_COLORS,
    generate_color,
    resolve_color,
    validate_hex_color,
)


def test_cv_palette_covers_9_classes():
    assert len(CV_CLASS_COLORS) == 9
    for color in CV_CLASS_COLORS.values():
        assert validate_hex_color(color) == color


def test_resolve_prefers_explicit_and_palette():
    assert resolve_color("Экскаватор", "excavator") == "#0080FF"
    assert resolve_color("Новый класс", "new", "#ABCDEF") == "#ABCDEF"
    with pytest.raises(ValueError):
        resolve_color("Экскаватор", "excavator", "red")


def test_generate_is_deterministic_and_hex():
    assert generate_color("unknown-class") == generate_color("unknown-class")
    assert validate_hex_color(generate_color("unknown-class"))
