from pydantic import BaseModel

class ErrorMessage(BaseModel):
    """Represents a single error message."""
    msg: str


class ErrorResponse(BaseModel):
    """Defines the structure for API error responses."""
    detail: list[ErrorMessage] | None = None