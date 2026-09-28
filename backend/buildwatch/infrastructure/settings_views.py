from fastapi import APIRouter

from buildwatch.settings import get_settings

router = APIRouter(tags=["Настройки"], prefix="/settings")


@router.get("", summary="Настройки приложения")
def get_public_settings():
    """Публичные настройки приложения без секретов"""
    settings = get_settings()
    return {
        "app": {"title": settings.app.title},
        "run": {
            "port": settings.run.port,
            "host": settings.run.host,
            "prefix": settings.run.prefix,
        },
        "s3": {
            # "endpoint": settings.s3.endpoint,
            "bucket": settings.s3.bucket,
        },
        "log": {
            "level": settings.log.level,
        },
        "use_mock": {
            "stage_repo": settings.use_mock.stage_repo,
            "technique_repo": settings.use_mock.technique_repo,
        },
    }
