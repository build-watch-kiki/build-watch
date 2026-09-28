from collections import Counter
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from buildwatch.infrastructure.database.models import (
    DailyProgressEvidenceORM,
    DailyProgressTechniqueORM,
)
from buildwatch.progress.algorithm import (
    StageTemplate,
    aggregate_daily_counts,
    assess_data_quality,
    choose_stage,
    compare_equipment,
    outcome_for,
    timing_for,
)
from buildwatch.progress.repository import PhotoObservation, ProgressRepository
from buildwatch.settings import AnalysisSettings
from buildwatch.techniques.mapping import TechniqueMatcher


class DailyProgressAnalyzer:
    """Build and persist one deterministic daily plan-fact snapshot."""

    def __init__(self, repository: ProgressRepository, settings: AnalysisSettings):
        self.repository = repository
        self.settings = settings
        self.timezone = ZoneInfo(settings.timezone)

    def analysis_date_for(self, captured_at: datetime) -> date:
        if captured_at.tzinfo is None:
            captured_at = captured_at.replace(tzinfo=timezone.utc)
        return captured_at.astimezone(self.timezone).date()

    def _day_bounds(self, analysis_date: date) -> tuple[datetime, datetime]:
        start = datetime.combine(analysis_date, time.min, tzinfo=self.timezone)
        return start.astimezone(timezone.utc), (start + timedelta(days=1)).astimezone(
            timezone.utc
        )

    @staticmethod
    def _stage_date(value: date | datetime) -> date:
        return value.date() if isinstance(value, datetime) else value

    async def recalculate_from(self, project_id: int, analysis_date: date) -> None:
        """Recalculate the changed day and all later materialized history."""

        dates = set(
            await self.repository.list_progress_dates(project_id, analysis_date)
        )
        dates.add(analysis_date)
        for target_date in sorted(dates):
            await self.recalculate(project_id, target_date)

    async def recalculate(self, project_id: int, analysis_date: date):
        project = await self.repository.lock_project(project_id)
        if project is None:
            raise ValueError(f"Unknown project {project_id}")

        start, end = self._day_bounds(analysis_date)
        observation_count = await self.repository.count_observations(
            project_id, start, end
        )
        observations = await self.repository.load_observations(project_id, start, end)
        techniques = list(await self.repository.load_techniques())
        technique_matcher = TechniqueMatcher(techniques)

        vectors: list[dict[int, int]] = []
        vectors_by_photo: dict[int, dict[int, int]] = {}
        unknown = Counter()
        known_detection_count = 0
        for observation in observations:
            counts: Counter[int] = Counter()
            for class_name, confidence in observation.detections:
                if confidence < self.settings.min_confidence:
                    continue
                technique = technique_matcher.resolve(class_name)
                if technique is None:
                    unknown[class_name] += 1
                else:
                    counts[technique.id] += 1
                    known_detection_count += 1
            vector = dict(counts)
            vectors.append(vector)
            vectors_by_photo[observation.photo_id] = vector

        technique_ids = [item.id for item in techniques]
        actual = aggregate_daily_counts(vectors, technique_ids)
        quality = assess_data_quality(observation_count, vectors, actual)
        common_values = {
            "observation_count": observation_count,
            "usable_observation_count": len(observations),
            "processing_coverage": quality.processing_coverage,
            "agreement_rate": quality.agreement_rate,
            "data_quality": quality.data_quality,
            "data_quality_reasons": list(quality.reasons),
            "unknown_detection_count": sum(unknown.values()),
            "unknown_classes": [
                {"className": name, "count": count}
                for name, count in sorted(unknown.items())
            ],
            "updated_at": datetime.now(timezone.utc),
        }

        if not observations:
            return await self._persist_insufficient(
                project_id,
                analysis_date,
                "no_usable_observations",
                common_values,
            )
        if unknown and known_detection_count == 0:
            return await self._persist_insufficient(
                project_id,
                analysis_date,
                "class_mapping_missing",
                common_values,
            )

        stages = list(await self.repository.load_stages(project_id))
        parent_ids = {
            stage.parent_id for stage in stages if stage.parent_id is not None
        }
        leaf_stages = [stage for stage in stages if stage.id not in parent_ids]
        if not leaf_stages:
            return await self._persist_insufficient(
                project_id, analysis_date, "no_leaf_stages", common_values
            )

        templates = [
            StageTemplate(
                id=stage.id,
                name=stage.name,
                start_date=self._stage_date(stage.start_dt),
                end_date=self._stage_date(stage.end_dt),
                quantities={
                    link.technique_id: link.quantity for link in stage.technique_links
                },
            )
            for stage in leaf_stages
        ]
        templates.sort(key=lambda item: (item.start_date, item.end_date, item.id))
        template_by_id = {item.id: item for item in templates}
        previous_result = await self.repository.last_actual_progress(
            project_id, analysis_date
        )
        previous = (
            template_by_id.get(previous_result.actual_stage_id)
            if previous_result is not None
            else None
        )
        if previous is None:
            baseline_date = analysis_date - timedelta(days=1)
            previous = next(
                (
                    item
                    for item in reversed(templates)
                    if item.start_date <= baseline_date
                ),
                templates[0],
            )
        previous_index = templates.index(previous)
        next_stage = (
            templates[previous_index + 1]
            if previous_index + 1 < len(templates)
            else None
        )

        decision = choose_stage(
            actual,
            previous,
            next_stage,
            minimum_score=self.settings.minimum_stage_score,
            transition_margin=self.settings.transition_margin,
        )
        if decision.selected_stage is None:
            evidence_stage = previous
            if (
                next_stage is not None
                and decision.next_score is not None
                and (
                    decision.previous_score is None
                    or decision.next_score > decision.previous_score
                )
            ):
                evidence_stage = next_stage
            evidence_rows = self._select_evidence(
                observations,
                vectors_by_photo,
                actual,
                evidence_stage.quantities,
            )
            return await self._persist_insufficient(
                project_id,
                analysis_date,
                decision.reason or "stage_not_identified",
                common_values,
                previous=previous,
                next_stage=next_stage,
                previous_score=decision.previous_score,
                next_score=decision.next_score,
                evidence_rows=evidence_rows,
            )

        selected = decision.selected_stage
        comparisons = compare_equipment(actual, selected.quantities)
        has_deviation = any(item.is_deviation for item in comparisons)
        timing_status, time_deviation_days = timing_for(
            analysis_date, decision.stage_changed, next_stage
        )
        values = {
            **common_values,
            "outcome": outcome_for(decision.stage_changed, has_deviation),
            "reason": None,
            "previous_stage_id": previous.id,
            "next_stage_id": next_stage.id if next_stage else None,
            "actual_stage_id": selected.id,
            "previous_stage_name": previous.name,
            "next_stage_name": next_stage.name if next_stage else None,
            "actual_stage_name": selected.name,
            "previous_score": decision.previous_score,
            "next_score": decision.next_score,
            "stage_changed": decision.stage_changed,
            "has_quantity_deviation": has_deviation,
            "timing_status": timing_status,
            "time_deviation_days": time_deviation_days,
        }
        technique_by_id = {item.id: item for item in techniques}
        technique_rows = []
        for item in comparisons:
            technique = technique_by_id[item.technique_id]
            technique_rows.append(
                DailyProgressTechniqueORM(
                    progress_id=0,
                    technique_id=item.technique_id,
                    technique_name=technique.name,
                    technique_name_ru=technique.name_ru,
                    planned_quantity=item.planned_quantity,
                    actual_quantity=item.actual_quantity,
                    delta=item.delta,
                    tolerance=item.tolerance,
                    is_deviation=item.is_deviation,
                    deviation_type=item.deviation_type,
                )
            )
        evidence_rows = self._select_evidence(
            observations, vectors_by_photo, actual, selected.quantities
        )
        return await self.repository.upsert_progress(
            project_id, analysis_date, values, technique_rows, evidence_rows
        )

    async def _persist_insufficient(
        self,
        project_id: int,
        analysis_date: date,
        reason: str,
        common_values: dict,
        previous: StageTemplate | None = None,
        next_stage: StageTemplate | None = None,
        previous_score: float | None = None,
        next_score: float | None = None,
        evidence_rows: list[DailyProgressEvidenceORM] | None = None,
    ):
        values = {
            **common_values,
            "outcome": "insufficient_data",
            "reason": reason,
            "previous_stage_id": previous.id if previous else None,
            "next_stage_id": next_stage.id if next_stage else None,
            "actual_stage_id": None,
            "previous_stage_name": previous.name if previous else None,
            "next_stage_name": next_stage.name if next_stage else None,
            "actual_stage_name": None,
            "previous_score": previous_score,
            "next_score": next_score,
            "stage_changed": False,
            "has_quantity_deviation": False,
            "timing_status": "unknown",
            "time_deviation_days": None,
        }
        return await self.repository.upsert_progress(
            project_id, analysis_date, values, [], evidence_rows or []
        )

    @staticmethod
    def _select_evidence(
        observations: list[PhotoObservation],
        vectors_by_photo: dict[int, dict[int, int]],
        aggregate: dict[int, int],
        planned: dict[int, int],
    ) -> list[DailyProgressEvidenceORM]:
        if not observations:
            return []
        reasons: dict[int, set[str]] = {}

        def add(photo_id: int, reason: str) -> None:
            reasons.setdefault(photo_id, set()).add(reason)

        representative = min(
            observations,
            key=lambda item: sum(
                abs(vectors_by_photo[item.photo_id].get(key, 0) - value)
                for key, value in aggregate.items()
            ),
        )
        add(representative.photo_id, "representative")

        planned_ids = set(planned)
        coverage = max(
            observations,
            key=lambda item: sum(
                min(vectors_by_photo[item.photo_id].get(key, 0), planned[key])
                for key in planned_ids
            ),
        )
        add(coverage.photo_id, "maximum_plan_coverage")

        unexpected_ids = {
            key for key, value in aggregate.items() if value > 0 and key not in planned
        }
        if unexpected_ids:
            unexpected = max(
                observations,
                key=lambda item: sum(
                    vectors_by_photo[item.photo_id].get(key, 0)
                    for key in unexpected_ids
                ),
            )
            add(unexpected.photo_id, "unexpected_equipment")

        return [
            DailyProgressEvidenceORM(
                progress_id=0,
                photo_id=photo_id,
                reason_codes=sorted(reason_codes),
            )
            for photo_id, reason_codes in list(reasons.items())[:3]
        ]
