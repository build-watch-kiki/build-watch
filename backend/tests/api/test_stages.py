from datetime import date, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from buildwatch.infrastructure.database.specifications import LimitOffsetSpec


def _make_work_type(id=1, name="Фундамент"):
    return SimpleNamespace(
        id=id, name=name, parent_id=None, created_at=datetime(2024, 1, 1)
    )


def _make_technique(id=1, name="excavator", name_ru="Экскаватор"):
    return SimpleNamespace(
        id=id,
        name=name,
        name_ru=name_ru,
        color="#0080FF",
        created_at=datetime(2024, 1, 1),
    )


def _make_stage_orm(id=1, project_id=1, name="Этап 1", work_type=None):
    return SimpleNamespace(
        id=id,
        project_id=project_id,
        parent_id=None,
        name=name,
        start_dt=date(2024, 1, 1),
        end_dt=date(2024, 6, 30),
        created_at=datetime(2024, 1, 1),
        work_type=work_type or _make_work_type(),
        work_type_id=(work_type.id if work_type else 1),
        technique_links=[],
    )


def _make_link(technique=None, quantity=1):
    return SimpleNamespace(technique=technique or _make_technique(), quantity=quantity)


async def test_get_stages(client, mock_db_manager):
    mock_db_manager.stage_repo.get_stages = AsyncMock(return_value=[_make_stage_orm()])
    mock_db_manager.stage_repo.get_count = AsyncMock(return_value=1)

    response = await client.get("/projects/1/stages")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) == 1
    assert data["items"][0]["workTypeId"] == 1
    assert data["items"][0]["workTypeName"] == "Фундамент"
    assert "name" not in data["items"][0]
    assert "workType" not in data["items"][0]
    assert data["metadata"]["total"] == 1


async def test_create_stage(client, mock_db_manager):
    mock_db_manager.project_repo.get_project_by_id = AsyncMock(
        return_value=MagicMock(id=1)
    )
    mock_db_manager.work_type_repo.get_work_type_by_id = AsyncMock(
        return_value=_make_work_type()
    )
    mock_db_manager.stage_repo.create_stage = AsyncMock(return_value=10)

    response = await client.post(
        "/projects/1/stages",
        json={
            "work_type_id": 1,
            "startDate": "2024-01-01",
            "endDate": "2024-06-30",
        },
    )
    assert response.status_code == 201
    assert response.json() == 10
    assert (
        mock_db_manager.stage_repo.create_stage.await_args.kwargs["name"] == "Фундамент"
    )
    mock_db_manager.commit.assert_awaited_once()
    mock_db_manager.recalculate_progress.assert_awaited_once_with(1)


async def test_create_stage_with_technique_quantities(client, mock_db_manager):
    mock_db_manager.project_repo.get_project_by_id = AsyncMock(
        return_value=MagicMock(id=1)
    )
    mock_db_manager.work_type_repo.get_work_type_by_id = AsyncMock(
        return_value=_make_work_type()
    )
    mock_db_manager.technique_repo.get_techniques = AsyncMock(
        return_value=[_make_technique()]
    )
    mock_db_manager.stage_repo.create_stage = AsyncMock(return_value=10)

    response = await client.post(
        "/projects/1/stages",
        json={
            "work_type_id": 1,
            "startDate": "2024-01-01",
            "endDate": "2024-06-30",
            "techniques": [{"name": "excavator", "quantity": 3}],
        },
    )
    assert response.status_code == 201
    assert (
        mock_db_manager.stage_repo.create_stage.await_args.kwargs["name"] == "Фундамент"
    )
    mock_db_manager.stage_repo.set_stage_techniques.assert_awaited_once_with(
        10, [(1, 3)]
    )


@pytest.mark.parametrize("quantity", [0, -1, 1.5, "2", None])
async def test_create_stage_rejects_invalid_quantity(client, mock_db_manager, quantity):
    response = await client.post(
        "/projects/1/stages",
        json={
            "work_type_id": 1,
            "startDate": "2024-01-01",
            "endDate": "2024-06-30",
            "techniques": [{"name": "excavator", "quantity": quantity}],
        },
    )
    assert response.status_code == 422
    mock_db_manager.stage_repo.create_stage.assert_not_awaited()


@pytest.mark.parametrize(
    "path", ["/projects/1/stages", "/projects/1/stages/1/techniques"]
)
async def test_stage_technique_duplicates_and_missing(client, mock_db_manager, path):
    mock_db_manager.project_repo.get_project_by_id = AsyncMock(
        return_value=MagicMock(id=1)
    )
    mock_db_manager.work_type_repo.get_work_type_by_id = AsyncMock(
        return_value=_make_work_type()
    )
    mock_db_manager.stage_repo.get_stage_by_id = AsyncMock(
        return_value=_make_stage_orm()
    )
    base = {"techniques": [{"name": "excavator", "quantity": 2}]}
    if path.endswith("/techniques"):
        send = client.put
    else:
        send = client.post
        base.update(work_type_id=1, startDate="2024-01-01", endDate="2024-06-30")
    duplicate = {**base, "techniques": base["techniques"] * 2}
    response = await send(path, json=duplicate)
    assert response.status_code == 400

    mock_db_manager.technique_repo.get_techniques = AsyncMock(return_value=[])
    response = await send(path, json=base)
    assert response.status_code == 404
    mock_db_manager.stage_repo.set_stage_techniques.assert_not_awaited()


async def test_create_stage_project_not_found(client, mock_db_manager):
    mock_db_manager.project_repo.get_project_by_id = AsyncMock(return_value=None)

    response = await client.post(
        "/projects/999/stages",
        json={
            "work_type_id": 1,
            "startDate": "2024-01-01",
            "endDate": "2024-06-30",
        },
    )
    assert response.status_code == 404


async def test_create_stage_parent_not_found(client, mock_db_manager):
    mock_db_manager.project_repo.get_project_by_id = AsyncMock(
        return_value=MagicMock(id=1)
    )
    mock_db_manager.work_type_repo.get_work_type_by_id = AsyncMock(
        return_value=_make_work_type()
    )
    mock_db_manager.stage_repo.get_stage_by_id = AsyncMock(return_value=None)

    response = await client.post(
        "/projects/1/stages",
        json={
            "parentId": 999,
            "workTypeId": 1,
            "startDate": "2024-01-01",
            "endDate": "2024-06-30",
        },
    )

    assert response.status_code == 404
    mock_db_manager.stage_repo.create_stage.assert_not_awaited()


async def test_create_stage_parent_from_another_project(client, mock_db_manager):
    mock_db_manager.project_repo.get_project_by_id = AsyncMock(
        return_value=MagicMock(id=1)
    )
    mock_db_manager.work_type_repo.get_work_type_by_id = AsyncMock(
        return_value=_make_work_type()
    )
    mock_db_manager.stage_repo.get_stage_by_id = AsyncMock(
        return_value=_make_stage_orm(project_id=2)
    )

    response = await client.post(
        "/projects/1/stages",
        json={
            "parentId": 2,
            "workTypeId": 1,
            "startDate": "2024-01-01",
            "endDate": "2024-06-30",
        },
    )

    assert response.status_code == 404
    mock_db_manager.stage_repo.create_stage.assert_not_awaited()


async def test_get_stage_by_id(client, mock_db_manager):
    stage = _make_stage_orm()
    stage.technique_links = [_make_link(quantity=4)]
    mock_db_manager.stage_repo.get_stage_by_id = AsyncMock(return_value=stage)

    response = await client.get("/projects/1/stages/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["workTypeName"] == "Фундамент"
    assert "name" not in data
    assert data["requiresTechnique"][0]["quantity"] == 4


async def test_update_stage(client, mock_db_manager):
    updated = _make_stage_orm(work_type=_make_work_type(id=2, name="Обновлённый тип"))
    mock_db_manager.stage_repo.get_stage_by_id = AsyncMock(return_value=updated)
    mock_db_manager.stage_repo.update_stage = AsyncMock()
    mock_db_manager.work_type_repo.get_work_type_by_id = AsyncMock(
        return_value=updated.work_type
    )

    response = await client.put(
        "/projects/1/stages/1",
        json={"workTypeId": 2},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["workTypeId"] == 2
    assert data["workTypeName"] == "Обновлённый тип"
    mock_db_manager.stage_repo.update_stage.assert_awaited_once_with(
        1, work_type_id=2, name="Обновлённый тип"
    )
    mock_db_manager.commit.assert_awaited_once()
    mock_db_manager.recalculate_progress.assert_awaited_once_with(1)


@pytest.mark.parametrize(
    "method,path,body",
    [
        (
            "post",
            "/projects/1/stages",
            {
                "workTypeId": 1,
                "name": "Чужое имя",
                "startDate": "2024-01-01",
                "endDate": "2024-06-30",
            },
        ),
        ("put", "/projects/1/stages/1", {"name": "Чужое имя"}),
    ],
)
async def test_stage_rejects_name(client, mock_db_manager, method, path, body):
    response = await getattr(client, method)(path, json=body)
    assert response.status_code == 422
    mock_db_manager.stage_repo.create_stage.assert_not_awaited()
    mock_db_manager.stage_repo.update_stage.assert_not_awaited()


async def test_stage_search_filters_items_and_total(client, mock_db_manager):
    mock_db_manager.stage_repo.get_stages = AsyncMock(return_value=[_make_stage_orm()])
    mock_db_manager.stage_repo.get_count = AsyncMock(return_value=1)
    response = await client.get("/projects/1/stages?search_value=Фундамент")
    assert response.status_code == 200
    assert response.json()["metadata"]["total"] == 1
    from buildwatch.stages.specifications import StageWorkTypeNameSpec

    for call in (
        mock_db_manager.stage_repo.get_stages.await_args,
        mock_db_manager.stage_repo.get_count.await_args,
    ):
        assert any(
            isinstance(spec, StageWorkTypeNameSpec) and spec.value == "Фундамент"
            for spec in call.args
        )


async def test_stage_shape_matches_across_get_and_put(client, mock_db_manager):
    stage = _make_stage_orm(name="Внутреннее имя")
    mock_db_manager.stage_repo.get_stages = AsyncMock(return_value=[stage])
    mock_db_manager.stage_repo.get_count = AsyncMock(return_value=1)
    mock_db_manager.stage_repo.get_stage_by_id = AsyncMock(return_value=stage)
    mock_db_manager.project_repo.get_project_by_id = AsyncMock(
        return_value=MagicMock(id=1)
    )

    list_response = await client.get("/projects/1/stages")
    gantt_response = await client.get("/projects/1/stages/gantt")
    detail_response = await client.get("/projects/1/stages/1")
    update_response = await client.put("/projects/1/stages/1", json={})
    techniques_response = await client.put(
        "/projects/1/stages/1/techniques", json={"techniques": []}
    )

    responses = [
        list_response.json()["items"][0],
        gantt_response.json()["items"][0],
        detail_response.json(),
        update_response.json(),
        techniques_response.json(),
    ]
    assert all(
        response.status_code == 200
        for response in (
            list_response,
            gantt_response,
            detail_response,
            update_response,
            techniques_response,
        )
    )
    assert all(item == responses[0] for item in responses)
    assert responses[0]["workTypeName"] == "Фундамент"
    assert responses[0]["workTypeId"] == 1
    assert "name" not in responses[0] and "workType" not in responses[0]


async def test_delete_stage(client, mock_db_manager):
    mock_db_manager.stage_repo.get_stage_by_id = AsyncMock(
        return_value=_make_stage_orm()
    )
    mock_db_manager.stage_repo.delete_stage = AsyncMock()

    response = await client.delete("/projects/1/stages/1")
    assert response.status_code == 204
    mock_db_manager.commit.assert_awaited_once()
    mock_db_manager.recalculate_progress.assert_awaited_once_with(1)


async def test_set_stage_techniques(client, mock_db_manager):
    stage = _make_stage_orm()
    stage.technique_links = [_make_link(quantity=2)]
    mock_db_manager.project_repo.get_project_by_id = AsyncMock(
        return_value=MagicMock(id=1)
    )
    mock_db_manager.stage_repo.get_stage_by_id = AsyncMock(return_value=stage)
    mock_db_manager.technique_repo.get_techniques = AsyncMock(
        return_value=[_make_technique()]
    )
    mock_db_manager.stage_repo.set_stage_techniques = AsyncMock()

    response = await client.put(
        "/projects/1/stages/1/techniques",
        json={"techniques": [{"name": "excavator", "quantity": 2}]},
    )
    assert response.status_code == 200
    data = response.json()
    assert "requiresTechnique" in data
    assert data["requiresTechnique"][0]["quantity"] == 2
    mock_db_manager.stage_repo.set_stage_techniques.assert_awaited_once_with(
        1, [(1, 2)]
    )
    mock_db_manager.commit.assert_awaited_once()
    mock_db_manager.recalculate_progress.assert_awaited_once_with(1)


async def test_clear_stage_techniques(client, mock_db_manager):
    stage = _make_stage_orm()
    mock_db_manager.project_repo.get_project_by_id = AsyncMock(
        return_value=MagicMock(id=1)
    )
    mock_db_manager.stage_repo.get_stage_by_id = AsyncMock(return_value=stage)

    response = await client.put(
        "/projects/1/stages/1/techniques", json={"techniques": []}
    )
    assert response.status_code == 200
    assert response.json()["requiresTechnique"] == []
    mock_db_manager.stage_repo.set_stage_techniques.assert_awaited_once_with(1, [])


@pytest.mark.parametrize("quantity", [0, "2"])
async def test_put_stage_techniques_rejects_invalid_quantity(
    client, mock_db_manager, quantity
):
    response = await client.put(
        "/projects/1/stages/1/techniques",
        json={"techniques": [{"name": "excavator", "quantity": quantity}]},
    )
    assert response.status_code == 422
    mock_db_manager.stage_repo.set_stage_techniques.assert_not_awaited()


async def test_gantt_returns_full_project_and_real_total(client, mock_db_manager):
    stages = [_make_stage_orm(id=i) for i in range(1, 61)]
    mock_db_manager.stage_repo.get_stages = AsyncMock(return_value=stages)
    mock_db_manager.stage_repo.get_count = AsyncMock(return_value=60)

    response = await client.get("/projects/1/stages/gantt")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 60
    assert response.json()["metadata"] == {"total": 60, "limit": None}
    assert not any(
        isinstance(spec, LimitOffsetSpec)
        for spec in mock_db_manager.stage_repo.get_stages.await_args.args
    )

    mock_db_manager.stage_repo.get_stages = AsyncMock(return_value=stages[:10])
    limited = await client.get("/projects/1/stages/gantt?limit=10")
    assert limited.status_code == 200
    assert len(limited.json()["items"]) == 10
    assert limited.json()["metadata"] == {"total": 60, "limit": 10}


async def test_gantt_embeds_actual_progress(client, mock_db_manager):
    stage = _make_stage_orm(id=7)
    mock_db_manager.stage_repo.get_stages = AsyncMock(return_value=[stage])
    mock_db_manager.stage_repo.get_count = AsyncMock(return_value=1)
    progress = SimpleNamespace(
        actual_stage_name="Фундамент",
        timing_status="late",
        time_deviation_days=2,
        techniques=[SimpleNamespace(is_deviation=True)],
    )
    mock_db_manager.list_gantt_progress.return_value = [
        SimpleNamespace(
            stage_id=7,
            start_date=date(2026, 9, 18),
            end_date=date(2026, 9, 25),
            progress=progress,
        )
    ]

    response = await client.get("/projects/1/stages/gantt")

    assert response.status_code == 200
    actual = response.json()["items"][0]["actual"]
    assert actual["startDate"] == "2026-09-18"
    assert actual["endDate"] == "2026-09-25"
    assert actual["status"] == "behind"
    assert actual["techniqueDeviationCount"] == 1
    assert actual["message"]["code"] == ("stage_behind_with_technique_deviations")
