from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """База всех Pydantic-схем проекта."""
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
        populate_by_name=True,
    )