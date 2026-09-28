from datetime import date, datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

from sqlalchemy.dialects import postgresql

from buildwatch.progress.analyzer import DailyProgressAnalyzer
from buildwatch.progress.repository import PhotoObservation, ProgressRepository
from buildwatch.settings import AnalysisSettings


def technique(technique_id: int, name: str):
    return SimpleNamespace(id=technique_id, name=name, name_ru=name.title())


def stage(stage_id: int, start_day: int, technique_id: int, quantity: int):
    return SimpleNamespace(
        id=stage_id,
        parent_id=None,
        name=f"Stage {stage_id}",
        start_dt=datetime(2026, 9, start_day, tzinfo=timezone.utc),
        end_dt=datetime(2026, 9, start_day + 4, tzinfo=timezone.utc),
        technique_links=[SimpleNamespace(technique_id=technique_id, quantity=quantity)],
    )


def observation(photo_id: int, detections):
    return PhotoObservation(
        photo_id=photo_id,
        storage_key=f"photo-{photo_id}.jpg",
        captured_at=datetime(2026, 9, 5, 10, tzinfo=timezone.utc),
        detections=detections,
    )


def repository_for(observations):
    repo = AsyncMock()
    repo.lock_project.return_value = SimpleNamespace(id=1)
    repo.count_observations.return_value = len(observations)
    repo.load_observations.return_value = observations
    repo.load_techniques.return_value = [
        technique(1, "excavator"),
        technique(2, "crane"),
        technique(3, "dump_truck"),
        technique(4, "truck"),
    ]
    repo.load_stages.return_value = [stage(1, 1, 1, 1), stage(2, 6, 2, 1)]
    repo.last_actual_progress.return_value = None
    repo.upsert_progress.side_effect = lambda *args: args
    return repo


async def test_project_lock_targets_only_projects_table():
    session = AsyncMock()
    session.scalar.return_value = SimpleNamespace(id=1)
    repository = ProgressRepository(session)

    await repository.lock_project(1)

    query = session.scalar.await_args.args[0]
    sql = str(query.compile(dialect=postgresql.dialect()))
    assert "FOR UPDATE OF projects" in sql


async def test_analyzer_does_not_sum_same_object_between_photos():
    repo = repository_for(
        [
            observation(1, [("excavator", 0.9)]),
            observation(2, [("excavator", 0.8)]),
            observation(3, [("excavator", 0.95)]),
        ]
    )
    analyzer = DailyProgressAnalyzer(repo, AnalysisSettings())
    await analyzer.recalculate(1, date(2026, 9, 5))

    values = repo.upsert_progress.await_args.args[2]
    technique_rows = repo.upsert_progress.await_args.args[3]
    assert values["outcome"] == "previous_without_deviation"
    assert values["actual_stage_id"] == 1
    excavator = next(row for row in technique_rows if row.technique_id == 1)
    assert excavator.actual_quantity == 1


async def test_analyzer_detects_next_stage():
    repo = repository_for(
        [
            observation(1, [("crane", 0.9)]),
            observation(2, [("crane", 0.8)]),
            observation(3, [("crane", 0.95)]),
        ]
    )
    analyzer = DailyProgressAnalyzer(repo, AnalysisSettings())
    await analyzer.recalculate(1, date(2026, 9, 6))

    values = repo.upsert_progress.await_args.args[2]
    assert values["outcome"] == "next_without_deviation"
    assert values["actual_stage_id"] == 2
    assert values["stage_changed"] is True


async def test_analyzer_reports_unmapped_model_classes():
    repo = repository_for([observation(1, [("concrete_pump", 0.9)])])
    analyzer = DailyProgressAnalyzer(repo, AnalysisSettings())
    await analyzer.recalculate(1, date(2026, 9, 5))

    values = repo.upsert_progress.await_args.args[2]
    assert values["outcome"] == "insufficient_data"
    assert values["reason"] == "class_mapping_missing"
    assert values["unknown_detection_count"] == 1
    assert values["unknown_classes"] == [{"className": "concrete_pump", "count": 1}]


async def test_analyzer_maps_cv_aliases_to_catalog_techniques():
    detections = [
        ("Dump truck", 0.9),
        ("Truck", 0.9),
        ("crane_truck", 0.9),
    ]
    repo = repository_for(
        [
            observation(1, detections),
            observation(2, detections),
            observation(3, detections),
        ]
    )
    repo.load_stages.return_value[0].technique_links = [
        SimpleNamespace(technique_id=2, quantity=1),
        SimpleNamespace(technique_id=3, quantity=1),
        SimpleNamespace(technique_id=4, quantity=1),
    ]
    analyzer = DailyProgressAnalyzer(repo, AnalysisSettings())

    await analyzer.recalculate(1, date(2026, 9, 5))

    values = repo.upsert_progress.await_args.args[2]
    technique_rows = repo.upsert_progress.await_args.args[3]
    actual = {row.technique_name: row.actual_quantity for row in technique_rows}
    assert values["unknown_detection_count"] == 0
    assert values["unknown_classes"] == []
    assert actual["dump_truck"] == 1
    assert actual["truck"] == 1
    assert actual["crane"] == 1


async def test_successful_empty_photos_are_usable_zero_observations():
    repo = repository_for([observation(1, []), observation(2, []), observation(3, [])])
    analyzer = DailyProgressAnalyzer(repo, AnalysisSettings())
    await analyzer.recalculate(1, date(2026, 9, 5))

    values = repo.upsert_progress.await_args.args[2]
    assert values["usable_observation_count"] == 3
    assert values["outcome"] == "previous_with_deviation"


async def test_low_stage_score_keeps_representative_evidence():
    repo = repository_for(
        [
            observation(1, [("dump_truck", 0.9)]),
            observation(2, [("dump_truck", 0.8)]),
            observation(3, [("dump_truck", 0.95)]),
        ]
    )
    analyzer = DailyProgressAnalyzer(repo, AnalysisSettings())

    await analyzer.recalculate(1, date(2026, 9, 5))

    values = repo.upsert_progress.await_args.args[2]
    evidence_rows = repo.upsert_progress.await_args.args[4]
    assert values["reason"] == "low_stage_score"
    assert values["actual_stage_id"] is None
    assert [row.photo_id for row in evidence_rows] == [1]


async def test_late_photo_recalculates_following_materialized_days():
    repo = repository_for([])
    repo.list_progress_dates.return_value = [date(2026, 9, 5), date(2026, 9, 6)]
    analyzer = DailyProgressAnalyzer(repo, AnalysisSettings())
    analyzer.recalculate = AsyncMock()

    await analyzer.recalculate_from(1, date(2026, 9, 5))

    assert [call.args for call in analyzer.recalculate.await_args_list] == [
        (1, date(2026, 9, 5)),
        (1, date(2026, 9, 6)),
    ]
