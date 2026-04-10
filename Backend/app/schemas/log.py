from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class LogIngestRequest(BaseModel):
    device_id: int = Field(gt=0)
    api_key: str = Field(min_length=1)
    message: str
    timestamp: datetime | None = None

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("api_key must not be empty")
        return normalized

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("message must not be empty")
        return normalized


class LogIngestResponse(BaseModel):
    success: bool
    log_id: int
    device_id: int
    timestamp: datetime
    event_type: str
    last_seen_updated: bool