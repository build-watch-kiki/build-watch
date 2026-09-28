from datetime import datetime

from pydantic import ConfigDict

from buildwatchcv.schemas.base import BaseSchema


class PhotoUploadedMessage(BaseSchema):
    """Формат события, публикуемого backend после загрузки фото."""

    cv_run_id: int
    project_id: int
    filename: str
    object_path: str
    url: str
    size: int
    content_type: str | None = None
    width: int | None = None
    height: int | None = None
    format: str | None = None
    created_at: datetime | None = None
    uploaded_at: datetime
