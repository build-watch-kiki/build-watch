from pydantic import AnyUrl, Field
from buildwatchcv.schemas.base import BaseSchema

class ModelInfo(BaseSchema):
    """Информация о CV-модели, которая была задействована в обнаружении."""
    name: str
    version: str
    storage_weights: AnyUrl
    
class Processing(BaseSchema):
    """Данные обработки."""
    inference_ms: int = Field(ge=0, description="Чистое время обработки изображения моделью")
    model: ModelInfo