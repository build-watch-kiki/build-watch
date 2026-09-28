from buildwatchcv.schemas.confidence import Confidence
from buildwatchcv.schemas.bbox import BBox
from buildwatchcv.schemas.base import BaseSchema

class Detection(BaseSchema):
    """Информация распознавания по каждому объекту."""
    object_id: int
    class_id: int
    class_name: str
    confidence: Confidence
    bbox: BBox
    