from enum import Enum
from pydantic import Field
from buildwatchcv.schemas.base import BaseSchema

class ActivityState(str, Enum):
    """Состояние определения активности техники."""
    ACTIVE = "active"
    IDLE = "idle"
    UNCERTAIN = "uncertain"
    # и другие
    
class Confidence(BaseSchema):
    """Уверенность обнаружения и активности объекта."""
    detection: float = Field(ge=0.0, le=1.0)
    activity: float = Field(ge=0.0, le=1.0)
    activity_state: ActivityState