from unittest.mock import AsyncMock, patch

from buildwatch.infrastructure.broker import NEW_PHOTO_QUEUE
from buildwatch.main import app, lifespan


async def test_backend_declares_photo_queue_on_startup():
    with (
        patch("buildwatch.main.broker") as broker,
        patch("buildwatch.main.db_helper") as db_helper,
    ):
        broker.start = AsyncMock()
        broker.declare_queue = AsyncMock()
        broker.stop = AsyncMock()
        db_helper.dispose = AsyncMock()

        async with lifespan(app):
            broker.start.assert_awaited_once_with()
            broker.declare_queue.assert_awaited_once_with(NEW_PHOTO_QUEUE)

        broker.stop.assert_awaited_once_with()
