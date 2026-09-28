from unittest.mock import AsyncMock, MagicMock, patch

import pytest


async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"message": "ok"}


async def test_health_db(client, mock_db_manager):
    mock_db_manager._session = MagicMock()
    mock_db_manager._session.scalar = AsyncMock(return_value="PostgreSQL 16.0")
    response = await client.get("/health/db")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "ok"
    assert "detail" in data


async def test_health_s3(client, mock_s3_client):
    mock_bucket = MagicMock()
    mock_bucket.name = "test-bucket"
    mock_s3_client.client.list_buckets.return_value = [mock_bucket]
    response = await client.get("/health/s3")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "ok"
    assert data["buckets"] == ["test-bucket"]


async def test_health_broker(client):
    with patch("buildwatch.infrastructure.views.aio_pika") as mock_pika:
        mock_conn = AsyncMock()
        mock_channel = AsyncMock()
        mock_conn.channel = AsyncMock(return_value=mock_channel)
        mock_conn.transport.connection.server_properties = {
            "product": b"RabbitMQ",
            "version": b"3.12.0",
        }
        mock_pika.connect_robust = AsyncMock(return_value=mock_conn)

        response = await client.get("/health/broker")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "ok"
        assert data["detail"]["product"] == "RabbitMQ"
        assert data["detail"]["version"] == "3.12.0"
