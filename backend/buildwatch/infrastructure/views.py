import asyncio
from typing import Any

import aio_pika
from fastapi import APIRouter
from sqlalchemy import text

from buildwatch.infrastructure.database.helper import SessionDep
from buildwatch.infrastructure.minio_client import S3ClientDep
from buildwatch.settings import get_settings

router = APIRouter(tags=["health"], prefix="/health")


@router.get("", summary="Работоспособность приложения")
def health_check():
    """Проверка доступности приложения"""

    return {"message": "ok"}


@router.get("/db", summary="Работоспособность БД")
async def check_db(session: SessionDep):
    """Проверка подключения к БД"""
    version = await asyncio.wait_for(
        session.scalar(text("SELECT version()")), timeout=5.0
    )
    return {"message": "ok", "detail": version}


@router.get("/s3", summary="Работоспособность S3")
async def check_s3(s3_client: S3ClientDep) -> dict[str, Any]:
    """Проверка подключения к S3"""

    buckets = await asyncio.to_thread(s3_client.client.list_buckets)
    bucket_names = [b.name for b in buckets]
    return {"message": "ok", "buckets": bucket_names}


@router.get("/broker", summary="Работоспособность брокера")
async def check_broker() -> dict[str, Any]:
    """Проверка подключения к брокеру"""
    settings = get_settings()
    connection = await asyncio.wait_for(
        aio_pika.connect_robust(settings.broker.RABBITMQ_DSN), timeout=5.0
    )
    channel = None
    try:
        channel = await connection.channel()
        props = connection.transport.connection.server_properties

        # bytes -> str для читаемости
        product = props.get("product")
        version = props.get("version")
        if isinstance(product, bytes):
            product = product.decode()
        if isinstance(version, bytes):
            version = version.decode()

        return {
            "message": "ok",
            "detail": {
                "product": product,
                "version": version,
            },
        }
    finally:
        if channel is not None:
            try:
                await channel.close()
            except Exception:
                pass
        await connection.close()
