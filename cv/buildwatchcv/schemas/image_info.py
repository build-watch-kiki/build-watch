from typing import Literal

from pydantic import Field
from buildwatchcv.schemas.base import BaseSchema

class ImageInfo(BaseSchema):
    """Информация о снимке."""
    key: str = Field(description="Неизменный идентификатор, добавляется к URL")
    width: int = Field(ge=0)
    height: int = Field(ge=0)
    format: Literal["PNG", "JPEG", "JPG"]