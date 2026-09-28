from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

with (
    patch("buildwatch.infrastructure.broker.broker") as _mock_broker,
    patch("buildwatch.infrastructure.database.helper.db_helper") as _mock_db_helper,
):
    from buildwatch.main import app

from buildwatch.infrastructure.database.manager import get_db_manager, DBManager
from buildwatch.infrastructure.database.helper import db_helper
from buildwatch.infrastructure.minio_client import get_s3_client


@pytest.fixture()
def mock_db_manager():
    manager = MagicMock(spec=DBManager)
    manager.project_repo = AsyncMock()
    manager.stage_repo = AsyncMock()
    manager.work_type_repo = AsyncMock()
    manager.technique_repo = AsyncMock()
    manager.photos_repo = AsyncMock()
    manager.commit = AsyncMock()
    manager.rollback = AsyncMock()
    manager.recalculate_progress = AsyncMock()
    manager.list_gantt_progress = AsyncMock(return_value=[])
    return manager


@pytest.fixture()
def mock_s3_client():
    return MagicMock()


@pytest.fixture()
def _override_dependencies(mock_db_manager, mock_s3_client):
    app.dependency_overrides[get_db_manager] = lambda: mock_db_manager
    app.dependency_overrides[db_helper.session_getter] = (
        lambda: mock_db_manager._session
    )
    app.dependency_overrides[get_s3_client] = lambda: mock_s3_client
    yield
    app.dependency_overrides.clear()


@pytest.fixture()
async def client(_override_dependencies):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as ac:
        yield ac
