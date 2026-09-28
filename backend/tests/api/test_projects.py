from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from buildwatch.projects.schemas import ProjectResponse, ProjectTypeResponse


def _make_project_type(id=1, name="Жилой дом"):
    return ProjectTypeResponse(id=id, name=name, created_at=datetime(2024, 1, 1))


def _make_project(id=1, name="Test Project", type_id=1):
    return ProjectResponse(
        id=id,
        name=name,
        start_dt=date(2024, 1, 1),
        end_dt=date(2024, 12, 31),
        created_at=datetime(2024, 1, 1),
        type=_make_project_type(id=type_id),
    )


async def test_get_projects(client, mock_db_manager):
    mock_db_manager.project_repo.get_count = AsyncMock(return_value=1)
    mock_db_manager.project_repo.get_projects = AsyncMock(
        return_value=[_make_project()]
    )

    response = await client.get("/projects")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "metadata" in data
    assert len(data["items"]) == 1
    assert data["metadata"]["total"] == 1


async def test_get_projects_empty(client, mock_db_manager):
    mock_db_manager.project_repo.get_count = AsyncMock(return_value=0)
    mock_db_manager.project_repo.get_projects = AsyncMock(return_value=[])

    response = await client.get("/projects")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["metadata"]["total"] == 0


async def test_get_project(client, mock_db_manager):
    mock_db_manager.project_repo.get_project_by_id = AsyncMock(
        return_value=_make_project(id=42)
    )

    response = await client.get("/projects/42")

    assert response.status_code == 200
    assert response.json()["id"] == 42
    mock_db_manager.project_repo.get_project_by_id.assert_awaited_once_with(42)


async def test_get_project_not_found(client, mock_db_manager):
    mock_db_manager.project_repo.get_project_by_id = AsyncMock(return_value=None)

    response = await client.get("/projects/42")

    assert response.status_code == 404


async def test_create_project(client, mock_db_manager):
    mock_db_manager.project_repo.get_project_types = AsyncMock(
        return_value=[_make_project_type()]
    )
    mock_db_manager.project_repo.create_project = AsyncMock(return_value=42)

    response = await client.post(
        "/projects",
        json={
            "name": "New Project",
            "type": "Жилой дом",
            "startDate": "2024-01-01",
            "endDate": "2024-12-31",
        },
    )
    assert response.status_code == 201
    assert response.json() == 42
    mock_db_manager.commit.assert_awaited_once()


async def test_create_project_type_not_found(client, mock_db_manager):
    mock_db_manager.project_repo.get_project_types = AsyncMock(return_value=[])

    response = await client.post(
        "/projects",
        json={
            "name": "New Project",
            "type": "Несуществующий тип",
            "startDate": "2024-01-01",
            "endDate": "2024-12-31",
        },
    )
    assert response.status_code == 404


async def test_get_available_work_types(client, mock_db_manager):
    from buildwatch.work_types.schemas import WorkTypeResponse
    from datetime import datetime as dt

    mock_db_manager.project_repo.get_project_by_id = AsyncMock(
        return_value=MagicMock(type_id=1)
    )
    mock_db_manager.work_type_repo.get_work_types = AsyncMock(
        return_value=[
            WorkTypeResponse(
                id=1, name="Фундамент", parent_id=None, created_at=dt(2024, 1, 1)
            )
        ]
    )
    mock_db_manager.work_type_repo.get_work_types_count = AsyncMock(return_value=1)

    response = await client.get("/projects/1/work-types")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) == 1
    assert data["metadata"]["total"] == 1
