from collections.abc import Sequence

from buildwatch.progress.schemas import (
    ProgressDetailMessageResponse,
    ProgressMessageResponse,
    ProgressStatus,
)


def plural_form(value: int, one: str, few: str, many: str) -> str:
    """Return a Russian noun form for an integer value."""

    number = abs(value) % 100
    if 11 <= number <= 14:
        return many
    number %= 10
    if number == 1:
        return one
    if 2 <= number <= 4:
        return few
    return many


def count_text(value: int, one: str, few: str, many: str) -> str:
    return f"{abs(value)} {plural_form(value, one, few, many)}"


def status_from_timing(timing_status: str) -> ProgressStatus:
    return {
        "early": "ahead",
        "on_schedule": "on_track",
        "late": "behind",
        "unknown": "unknown",
    }.get(timing_status, "unknown")


def stage_message(
    status: ProgressStatus,
    stage_name: str | None,
    deviation_days: int | None,
    technique_deviation_count: int = 0,
    *,
    compact: bool = False,
) -> ProgressMessageResponse:
    stage = f"Этап «{stage_name}»" if stage_name else "Этап"
    days = count_text(deviation_days or 0, "день", "дня", "дней")
    technique_suffix = ""
    code_suffix = ""
    if technique_deviation_count:
        kinds = count_text(technique_deviation_count, "виду", "видам", "видам")
        technique_suffix = f", отклонения по {kinds} техники"
        if compact:
            code_suffix = "_with_technique_deviations"

    if status == "ahead":
        text = (
            f"Опережение на {days}" if compact else f"{stage} опережает план на {days}"
        )
        code = "stage_ahead"
        severity = "info"
    elif status == "behind":
        text = (
            f"Отставание на {days}"
            if compact
            else f"{stage} отстаёт от плана на {days}"
        )
        code = "stage_behind"
        severity = "warning"
    elif status == "on_track":
        text = "По плану" if compact else f"{stage} выполняется по плану"
        code = "stage_on_track"
        severity = "info"
    else:
        text = "Недостаточно данных для определения этапа"
        code = "insufficient_data"
        severity = "warning"
        technique_suffix = ""
        code_suffix = ""

    return ProgressMessageResponse(
        code=f"{code}{code_suffix}",
        severity=severity,
        text=f"{text}{technique_suffix}",
    )


def progress_message(
    progress,
    status: ProgressStatus,
    minimum_stage_score: float,
    technique_deviation_count: int = 0,
) -> ProgressMessageResponse:
    """Build a daily summary without hiding the real identification failure."""

    if status == "unknown" and getattr(progress, "reason", None) == "low_stage_score":
        candidates: list[str] = []
        if (
            progress.previous_stage_name is not None
            and progress.previous_score is not None
        ):
            candidates.append(
                f"предыдущий «{progress.previous_stage_name}» — "
                f"{progress.previous_score:.0%}"
            )
        if progress.next_stage_name is not None and progress.next_score is not None:
            candidates.append(
                f"следующий «{progress.next_stage_name}» — {progress.next_score:.0%}"
            )
        comparison = ", ".join(candidates)
        details = f": {comparison}" if comparison else ""
        return ProgressMessageResponse(
            code="stage_score_below_threshold",
            severity="warning",
            text=(
                "Техника на снимках недостаточно соответствует плану этапа"
                f"{details}. Необходимый порог — {minimum_stage_score:.0%}"
            ),
        )

    return stage_message(
        status,
        progress.actual_stage_name,
        progress.time_deviation_days,
        technique_deviation_count,
    )


def detail_messages(
    progress,
    status: ProgressStatus,
    technique_rows: Sequence,
    evidence_photo_ids: list[int],
    summary_message: ProgressMessageResponse | None = None,
) -> list[ProgressDetailMessageResponse]:
    stage_id = progress.actual_stage_id
    stage_name = progress.actual_stage_name
    summary = summary_message or stage_message(
        status, stage_name, progress.time_deviation_days
    )
    category = "stage" if status == "unknown" else "schedule"
    messages = [
        ProgressDetailMessageResponse(
            **summary.model_dump(),
            category=category,
            stage_id=stage_id,
            evidence_photo_ids=evidence_photo_ids,
        )
    ]

    for row in technique_rows:
        if not row.is_deviation:
            continue
        name = f"«{row.technique_name_ru}»"
        if row.deviation_type == "missing":
            code = "missing_required_equipment"
            shortage = count_text(abs(row.delta), "единица", "единицы", "единиц")
            text = (
                f"Для этапа «{stage_name}» не хватает {shortage} техники {name}: "
                f"план — {row.planned_quantity}, факт — {row.actual_quantity}"
            )
        elif row.deviation_type == "unexpected":
            code = "unexpected_equipment"
            amount = count_text(row.actual_quantity, "единица", "единицы", "единиц")
            text = (
                f"На этапе «{stage_name}» обнаружена незапланированная техника "
                f"{name}: {amount}"
            )
        else:
            code = "quantity_mismatch"
            text = (
                f"Количество техники {name} на этапе «{stage_name}» отличается "
                f"от плана: план — {row.planned_quantity}, факт — {row.actual_quantity}"
            )
        messages.append(
            ProgressDetailMessageResponse(
                code=code,
                category="technique",
                severity="warning",
                text=text,
                stage_id=stage_id,
                technique_id=row.technique_id,
                evidence_photo_ids=evidence_photo_ids,
            )
        )

    if progress.data_quality in {"low", "insufficient"}:
        messages.append(
            ProgressDetailMessageResponse(
                code="low_data_quality",
                category="quality",
                severity="warning",
                text="Качество наблюдений недостаточно для надёжной оценки",
                stage_id=stage_id,
                evidence_photo_ids=evidence_photo_ids,
            )
        )
    return messages
