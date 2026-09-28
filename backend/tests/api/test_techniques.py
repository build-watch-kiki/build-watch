from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from buildwatch.techniques.schemas import TechniqueResponse


def _make_technique(id=1, name="excavator", name_ru="Экскаватор", color="#0080FF"):
    return TechniqueResponse(
        id=id, name=name, name_ru=name_ru, color=color, created_at=datetime(2024, 1, 1)
    )


async def test_get_techniques(client, mock_db_manager):
    mock_db_manager.technique_repo.get_techniques = AsyncMock(
        return_value=[_make_technique()]
    )
    mock_db_manager.technique_repo.get_count = AsyncMock(return_value=1)

    response = await client.get("/techniques")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) == 1
    assert data["metadata"]["total"] == 1


async def test_create_technique(client, mock_db_manager):
    mock_db_manager.technique_repo.create_technique = AsyncMock(return_value=1)

    response = await client.post(
        "/techniques",
        json={"name": "bulldozer", "nameRu": "Бульдозер"},
    )
    assert response.status_code == 201
    assert response.json() == 1
    mock_db_manager.commit.assert_awaited_once()
    assert mock_db_manager.technique_repo.create_technique.await_args.kwargs[
        "color"
    ] == "#B1FF00"


async def test_create_technique_rejects_bad_color(client, mock_db_manager):
    mock_db_manager.technique_repo.create_technique = AsyncMock(return_value=1)

    response = await client.post(
        "/techniques",
        json={"name": "bulldozer", "nameRu": "Бульдозер", "color": "red"},
    )
    assert response.status_code == 422


async def test_get_technique_by_id(client, mock_db_manager):
    mock_db_manager.technique_repo.get_technique_by_id = AsyncMock(
        return_value=_make_technique()
    )

    response = await client.get("/techniques/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "excavator"
    assert data["nameRu"] == "Экскаватор"


async def test_update_technique(client, mock_db_manager):
    updated = _make_technique(name="crane", name_ru="Кран")
    mock_db_manager.technique_repo.update_technique = AsyncMock()
    mock_db_manager.technique_repo.get_technique_by_id = AsyncMock(return_value=updated)

    response = await client.put(
        "/techniques/1",
        json={"name": "crane", "nameRu": "Кран"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "crane"
    mock_db_manager.commit.assert_awaited_once()


async def test_delete_technique(client, mock_db_manager):
    mock_db_manager.technique_repo.delete_technique = AsyncMock()

    response = await client.delete("/techniques/1")
    assert response.status_code == 204
    mock_db_manager.commit.assert_awaited_once()
