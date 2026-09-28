from types import SimpleNamespace

from buildwatch.techniques.mapping import TechniqueMatcher, normalize_technique_label


def test_normalizes_case_spaces_hyphens_and_underscores():
    assert normalize_technique_label("  Crane_truck ") == "crane truck"
    assert normalize_technique_label("CRANE-TRUCK") == "crane truck"


def test_resolves_cv_aliases_against_live_catalog():
    dump_truck = SimpleNamespace(id=4, name="dump_truck", name_ru="Самосвал")
    crane = SimpleNamespace(id=3, name="crane", name_ru="Автокран")
    truck = SimpleNamespace(id=5, name="truck", name_ru="Грузовик")
    matcher = TechniqueMatcher([dump_truck, crane, truck])

    assert matcher.resolve("Dump truck") is dump_truck
    assert matcher.resolve("Truck") is truck
    assert matcher.resolve("crane_truck") is crane


def test_exact_catalog_match_wins_over_alias():
    truck = SimpleNamespace(id=4, name="truck", name_ru="Грузовик")
    dump_truck = SimpleNamespace(id=5, name="dump_truck", name_ru="Самосвал")
    matcher = TechniqueMatcher([truck, dump_truck])

    assert matcher.resolve("Truck") is truck
