from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from buildwatch.work_types.schemas import WorkTypeResponse


def _make_work_type(id=1, name="Фундамент"):
    return WorkTypeResponse(
        id=id, name=name, parent_id=None, created_at=datetime(2024, 1, 1)
    )


async def test_get_work_types(client, mock_db_manager):
    mock_db_manager.work_type_repo.get_work_types = AsyncMock(
        return_value=[_make_work_type()]
    )
    mock_db_manager.work_type_repo.get_work_types_count = AsyncMock(return_value=1)

    response = await client.get("/work-types")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) == 1
    assert data["metadata"]["total"] == 1


async def test_get_project_types(client, mock_db_manager):
    from buildwatch.projects.schemas import ProjectTypeResponse

    mock_db_manager.project_repo.get_project_types = AsyncMock(
        return_value=[
            ProjectTypeResponse(id=1, name="Жилой дом", created_at=datetime(2024, 1, 1))
        ]
    )
    mock_db_manager.project_repo.get_project_types_count = AsyncMock(return_value=1)

    response = await client.get("/project-types")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) == 1
    assert data["metadata"]["total"] == 1
