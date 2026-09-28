import math
from dataclasses import dataclass
from datetime import date
from typing import Mapping, Sequence


@dataclass(frozen=True, slots=True)
class StageTemplate:
    id: int
    name: str
    start_date: date
    end_date: date
    quantities: Mapping[int, int]


@dataclass(frozen=True, slots=True)
class EquipmentComparison:
    technique_id: int
    planned_quantity: int
    actual_quantity: int
    delta: int
    tolerance: int
    is_deviation: bool
    deviation_type: str


@dataclass(frozen=True, slots=True)
class QualityResult:
    processing_coverage: float
    agreement_rate: float
    data_quality: str
    reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class StageDecision:
    selected_stage: StageTemplate | None
    previous_score: float | None
    next_score: float | None
    stage_changed: bool
    reason: str | None = None


def nearest_rank_percentile(values: Sequence[int], percentile: float = 0.75) -> int:
    """Integer nearest-rank percentile; empty observations represent zero."""

    if not values:
        return 0
    ordered = sorted(values)
    rank = max(1, math.ceil(percentile * len(ordered)))
    return ordered[rank - 1]


def aggregate_daily_counts(
    observations: Sequence[Mapping[int, int]], technique_ids: Sequence[int]
) -> dict[int, int]:
    """Aggregate independent photo counts without summing objects across time."""

    return {
        technique_id: nearest_rank_percentile(
            [int(item.get(technique_id, 0)) for item in observations]
        )
        for technique_id in technique_ids
    }


def cosine_similarity(left: Mapping[int, int], right: Mapping[int, int]) -> float:
    keys = left.keys() | right.keys()
    numerator = sum(left.get(key, 0) * right.get(key, 0) for key in keys)
    left_norm = math.sqrt(sum(left.get(key, 0) ** 2 for key in keys))
    right_norm = math.sqrt(sum(right.get(key, 0) ** 2 for key in keys))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)


def quantity_overlap(left: Mapping[int, int], right: Mapping[int, int]) -> float:
    keys = left.keys() | right.keys()
    denominator = sum(max(left.get(key, 0), right.get(key, 0)) for key in keys)
    if denominator == 0:
        return 1.0
    numerator = sum(min(left.get(key, 0), right.get(key, 0)) for key in keys)
    return numerator / denominator


def stage_score(actual: Mapping[int, int], planned: Mapping[int, int]) -> float:
    return 0.7 * cosine_similarity(actual, planned) + 0.3 * quantity_overlap(
        actual, planned
    )


def choose_stage(
    actual: Mapping[int, int],
    previous: StageTemplate,
    next_stage: StageTemplate | None,
    minimum_score: float = 0.60,
    transition_margin: float = 0.10,
) -> StageDecision:
    """Choose between the last actual stage and its next planned neighbour."""

    if not previous.quantities:
        return StageDecision(None, None, None, False, "stage_has_no_technique_plan")
    if next_stage is not None and dict(previous.quantities) == dict(
        next_stage.quantities
    ):
        return StageDecision(
            None, None, None, False, "indistinguishable_stage_templates"
        )

    previous_score = stage_score(actual, previous.quantities)
    next_score = (
        stage_score(actual, next_stage.quantities)
        if next_stage is not None and next_stage.quantities
        else None
    )

    # A successfully processed empty site is evidence of a quantity deviation,
    # but cannot prove a stage transition.
    if not any(actual.values()):
        return StageDecision(previous, previous_score, next_score, False)

    # There is no alternative stage after the terminal one. Keep the known
    # stage and explain any mismatch through equipment deviations.
    if next_stage is None:
        return StageDecision(previous, previous_score, None, False)

    if (
        next_stage is not None
        and next_score is not None
        and next_score >= minimum_score
        and next_score - previous_score >= transition_margin
    ):
        return StageDecision(next_stage, previous_score, next_score, True)
    if previous_score >= minimum_score:
        return StageDecision(previous, previous_score, next_score, False)
    return StageDecision(None, previous_score, next_score, False, "low_stage_score")


def compare_equipment(
    actual: Mapping[int, int], planned: Mapping[int, int]
) -> list[EquipmentComparison]:
    result: list[EquipmentComparison] = []
    for technique_id in sorted(actual.keys() | planned.keys()):
        planned_quantity = int(planned.get(technique_id, 0))
        actual_quantity = int(actual.get(technique_id, 0))
        if planned_quantity == 0 and actual_quantity == 0:
            continue
        delta = actual_quantity - planned_quantity
        tolerance = math.floor(planned_quantity * 0.25)
        is_deviation = abs(delta) > tolerance
        if not is_deviation:
            deviation_type = "none"
        elif planned_quantity == 0:
            deviation_type = "unexpected"
        elif delta < 0:
            deviation_type = "missing"
        else:
            deviation_type = "quantity_mismatch"
        result.append(
            EquipmentComparison(
                technique_id=technique_id,
                planned_quantity=planned_quantity,
                actual_quantity=actual_quantity,
                delta=delta,
                tolerance=tolerance,
                is_deviation=is_deviation,
                deviation_type=deviation_type,
            )
        )
    return result


def assess_data_quality(
    observation_count: int,
    observations: Sequence[Mapping[int, int]],
    aggregate: Mapping[int, int],
) -> QualityResult:
    usable_count = len(observations)
    processing_coverage = usable_count / observation_count if observation_count else 0.0
    if usable_count == 0:
        return QualityResult(
            processing_coverage=processing_coverage,
            agreement_rate=0.0,
            data_quality="insufficient",
            reasons=("no_usable_observations",),
        )

    technique_ids = aggregate.keys()
    agreeing = sum(
        all(abs(item.get(key, 0) - aggregate.get(key, 0)) <= 1 for key in technique_ids)
        for item in observations
    )
    agreement_rate = agreeing / usable_count
    reasons: list[str] = []
    if usable_count < 3:
        reasons.append("too_few_usable_observations")
    if processing_coverage < 0.5:
        reasons.append("low_processing_coverage")
    if agreement_rate < 0.5:
        reasons.append("unstable_counts")

    if reasons:
        quality = "low"
    elif usable_count < 6 or processing_coverage < 0.8 or agreement_rate < 0.75:
        quality = "medium"
        if usable_count < 6:
            reasons.append("limited_observation_count")
        if processing_coverage < 0.8:
            reasons.append("partial_processing_coverage")
        if agreement_rate < 0.75:
            reasons.append("moderate_count_variance")
    else:
        quality = "high"
    return QualityResult(
        processing_coverage=processing_coverage,
        agreement_rate=agreement_rate,
        data_quality=quality,
        reasons=tuple(reasons),
    )


def outcome_for(stage_changed: bool, has_deviation: bool) -> str:
    stage = "next" if stage_changed else "previous"
    deviation = "with_deviation" if has_deviation else "without_deviation"
    return f"{stage}_{deviation}"


def timing_for(
    analysis_date: date,
    stage_changed: bool,
    next_stage: StageTemplate | None,
) -> tuple[str, int | None]:
    if next_stage is None:
        return "on_schedule", 0
    planned_transition = next_stage.start_date
    if stage_changed:
        delta = (analysis_date - planned_transition).days
        if delta < 0:
            return "early", delta
        if delta > 0:
            return "late", delta
        return "on_schedule", 0
    if analysis_date >= planned_transition:
        return "late", (analysis_date - planned_transition).days + 1
    return "on_schedule", 0
