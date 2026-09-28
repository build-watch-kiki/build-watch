from datetime import date
from unittest.mock import AsyncMock

from buildwatch.main import app
from buildwatch.progress.schemas import (
    DailyProgressSummaryResponse,
)
from buildwatch.progress.service import get_progress_service


def summary() -> DailyProgressSummaryResponse:
    return DailyProgressSummaryResponse(
        date=date(2026, 9, 25),
        is_final=False,
        status="behind",
        deviation_days=2,
        technique_deviation_count=1,
        message={
            "code": "stage_behind",
            "severity": "warning",
            "text": "Этап «Котлован» отстаёт от плана на 2 дня",
        },
        stages={
            "previous": {"id": 1, "name": "Котлован", "score": 0.82},
            "current": {"id": 1, "name": "Котлован", "score": 0.82},
            "next": {"id": 2, "name": "Фундамент", "score": 0.41},
        },
        quality="medium",
    )


async def test_daily_progress_contract_is_compact_and_nested(client):
    service = AsyncMock()
    service.list_daily_progress.return_value = [summary()]
    app.dependency_overrides[get_progress_service] = lambda: service

    response = await client.get(
        "/projects/1/progress/daily?from=2026-09-01&to=2026-09-25"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["metadata"] == {"total": 1, "limit": None}
    item = data["items"][0]
    assert item["status"] == "behind"
    assert item["stages"]["current"] == {
        "id": 1,
        "name": "Котлован",
        "score": 0.82,
    }
    assert item["message"]["code"] == "stage_behind"
    assert "outcome" not in item
    assert "previousScore" not in item
    assert "evidence" not in item
    request = service.list_daily_progress.await_args.args[1]
    assert request.from_date == date(2026, 9, 1)
    assert request.to_date == date(2026, 9, 25)


async def test_daily_progress_detail_contract(client):
    service = AsyncMock()
    service.get_daily_progress.return_value = {
        **summary().model_dump(),
        "techniques": {
            "stage_id": 1,
            "items": [
                {
                    "id": 3,
                    "name": "Самосвал",
                    "plan": 3,
                    "fact": 2,
                    "delta": -1,
                    "status": "missing",
                }
            ],
        },
        "messages": [
            {
                "code": "missing_required_equipment",
                "category": "technique",
                "severity": "warning",
                "text": "Не хватает техники",
                "stage_id": 1,
                "technique_id": 3,
                "evidence_photo_ids": [],
            }
        ],
        "quality": {
            "level": "medium",
            "observations": {"total": 8, "usable": 7},
            "coverage": 0.875,
            "agreement": 0.62,
            "reasons": ["moderate_count_variance"],
        },
        "evidence": [],
    }
    app.dependency_overrides[get_progress_service] = lambda: service

    response = await client.get("/projects/1/progress/daily/2026-09-25")

    assert response.status_code == 200
    data = response.json()
    assert data["techniques"]["stageId"] == 1
    assert data["techniques"]["items"][0]["plan"] == 3
    assert data["quality"]["observations"] == {"total": 8, "usable": 7}
    service.get_daily_progress.assert_awaited_once_with(1, date(2026, 9, 25))


async def test_daily_progress_rejects_reversed_range(client):
    app.dependency_overrides[get_progress_service] = lambda: AsyncMock()
    response = await client.get(
        "/projects/1/progress/daily?from=2026-09-25&to=2026-09-01"
    )
    assert response.status_code == 422
