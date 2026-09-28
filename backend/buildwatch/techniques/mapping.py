import re
import unicodedata
from collections.abc import Iterable
from typing import Protocol, TypeVar


class TechniqueLike(Protocol):
    id: int
    name: str
    name_ru: str


TechniqueT = TypeVar("TechniqueT", bound=TechniqueLike)

_SEPARATORS = re.compile(r"[^\w]+|_+", re.UNICODE)

# A CV model label is resolved against the live technique catalog. Exact matches
# win; these aliases are only fallbacks when the catalog uses another common name.
_ALIAS_CANDIDATES: dict[str, tuple[str, ...]] = {
    "dump truck": ("dump truck", "dumptruck", "самосвал"),
    "dumptruck": ("dumptruck", "dump truck", "самосвал"),
    "самосвал": ("самосвал", "dump truck", "dumptruck"),
    "excavator": ("excavator", "экскаватор"),
    "экскаватор": ("экскаватор", "excavator"),
    "roller": ("roller", "road roller", "каток", "дорожный каток"),
    "road roller": ("road roller", "roller", "дорожный каток", "каток"),
    "каток": ("каток", "дорожный каток", "roller", "road roller"),
    "crane truck": (
        "crane truck",
        "truck crane",
        "mobile crane",
        "crane",
        "автокран",
        "кран манипулятор",
    ),
    "truck crane": (
        "truck crane",
        "crane truck",
        "mobile crane",
        "crane",
        "автокран",
        "кран манипулятор",
    ),
    "mobile crane": (
        "mobile crane",
        "crane truck",
        "truck crane",
        "crane",
        "автокран",
    ),
    "автокран": ("автокран", "crane", "crane truck", "truck crane", "mobile crane"),
    "forklift": ("forklift", "fork lift", "forklift truck", "вилочный погрузчик"),
    "fork lift": ("fork lift", "forklift", "forklift truck", "вилочный погрузчик"),
    "loader": (
        "loader",
        "front loader",
        "wheel loader",
        "погрузчик",
        "фронтальный погрузчик",
    ),
    "front loader": (
        "front loader",
        "wheel loader",
        "loader",
        "фронтальный погрузчик",
        "погрузчик",
    ),
    "mixer": (
        "mixer",
        "concrete mixer",
        "mixer truck",
        "автобетоносмеситель",
        "бетономешалка",
    ),
    "concrete mixer": (
        "concrete mixer",
        "mixer truck",
        "mixer",
        "автобетоносмеситель",
        "бетономешалка",
    ),
    "bulldozer": ("bulldozer", "бульдозер"),
    "бульдозер": ("бульдозер", "bulldozer"),
    "truck": ("truck", "грузовик"),
    "грузовик": ("грузовик", "truck"),
}


def normalize_technique_label(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold().replace("ё", "е")
    return " ".join(part for part in _SEPARATORS.split(normalized) if part)


class TechniqueMatcher:
    def __init__(self, techniques: Iterable[TechniqueT]):
        self._by_label: dict[str, TechniqueT] = {}
        for technique in techniques:
            for label in (technique.name, technique.name_ru):
                normalized = normalize_technique_label(label)
                if normalized:
                    self._by_label.setdefault(normalized, technique)

    def resolve(self, class_name: str) -> TechniqueT | None:
        normalized = normalize_technique_label(class_name)
        if not normalized:
            return None

        exact = self._by_label.get(normalized)
        if exact is not None:
            return exact

        for candidate in _ALIAS_CANDIDATES.get(normalized, ()):
            technique = self._by_label.get(normalize_technique_label(candidate))
            if technique is not None:
                return technique
        return None
