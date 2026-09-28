from datetime import date

import pytest

from buildwatch.progress.algorithm import (
    StageTemplate,
    aggregate_daily_counts,
    assess_data_quality,
    choose_stage,
    compare_equipment,
    nearest_rank_percentile,
    outcome_for,
    timing_for,
)


def stage(stage_id: int, quantities: dict[int, int], start_day: int = 1):
    return StageTemplate(
        id=stage_id,
        name=f"Stage {stage_id}",
        start_date=date(2026, 9, start_day),
        end_date=date(2026, 9, start_day + 5),
        quantities=quantities,
    )


def test_repeated_equipment_is_not_summed_between_photos():
    actual = aggregate_daily_counts([{1: 1}, {1: 1}, {}, {1: 1}, {1: 1}], [1])
    assert actual == {1: 1}


def test_percentile_smooths_single_false_positive_and_misses():
    assert nearest_rank_percentile([1, 1, 1, 2, 1]) == 1
    assert nearest_rank_percentile([1, 1, 0, 1, 0]) == 1


def test_next_stage_requires_minimum_score_and_margin():
    previous = stage(1, {1: 2})
    next_stage = stage(2, {2: 3}, start_day=6)
    decision = choose_stage({2: 3}, previous, next_stage)
    assert decision.selected_stage == next_stage
    assert decision.stage_changed is True


def test_empty_successful_observations_keep_previous_stage_with_deviation():
    previous = stage(1, {1: 2})
    decision = choose_stage({1: 0}, previous, stage(2, {2: 1}))
    assert decision.selected_stage == previous
    assert decision.stage_changed is False
    comparison = compare_equipment({1: 0}, previous.quantities)
    assert comparison[0].deviation_type == "missing"


def test_identical_stage_templates_are_not_distinguishable():
    decision = choose_stage({1: 2}, stage(1, {1: 2}), stage(2, {1: 2}))
    assert decision.selected_stage is None
    assert decision.reason == "indistinguishable_stage_templates"


def test_terminal_stage_is_kept_even_when_equipment_is_unexpected():
    previous = stage(1, {1: 1})
    decision = choose_stage({2: 3}, previous, None)
    assert decision.selected_stage == previous
    assert decision.stage_changed is False


@pytest.mark.parametrize(
    ("planned", "actual", "is_deviation"),
    [(3, 2, True), (4, 3, False), (8, 6, False), (8, 5, True)],
)
def test_quantity_tolerance(planned, actual, is_deviation):
    comparison = compare_equipment({1: actual}, {1: planned})[0]
    assert comparison.is_deviation is is_deviation


def test_unplanned_equipment_is_reported():
    comparison = compare_equipment({2: 1}, {1: 1})
    assert {item.deviation_type for item in comparison} == {"missing", "unexpected"}


def test_quality_uses_processing_coverage_and_agreement():
    quality = assess_data_quality(
        observation_count=8,
        observations=[{1: 1}] * 6 + [{1: 3}],
        aggregate={1: 1},
    )
    assert quality.processing_coverage == pytest.approx(0.875)
    assert quality.agreement_rate == pytest.approx(6 / 7)
    assert quality.data_quality == "high"


def test_quality_marks_empty_day_insufficient():
    quality = assess_data_quality(3, [], {1: 0})
    assert quality.data_quality == "insufficient"
    assert quality.reasons == ("no_usable_observations",)


def test_outcomes_and_timing():
    assert outcome_for(False, True) == "previous_with_deviation"
    assert outcome_for(True, False) == "next_without_deviation"
    next_stage = stage(2, {2: 1}, start_day=10)
    assert timing_for(date(2026, 9, 8), True, next_stage) == ("early", -2)
    assert timing_for(date(2026, 9, 12), True, next_stage) == ("late", 2)
    assert timing_for(date(2026, 9, 12), False, next_stage) == ("late", 3)
