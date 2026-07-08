from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AlertOut(BaseModel):
    id: int
    device_id: int
    type: str
    severity: str
    description: str
    status: str
    assigned_to: int | None = None
    assigned_to_email: str | None = None
    assigned_role: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AlertListResponse(BaseModel):
    total: int
    page: int
    limit: int
    alerts: list[AlertOut]


class AssignAlertRequest(BaseModel):
    user_id: int = Field(ge=1)


class UpdateAlertStatusRequest(BaseModel):
    status: str = Field(pattern="^(IN_PROGRESS|RESOLVED)$")


class AddAlertActivityRequest(BaseModel):
    note: str = Field(min_length=1)
    metadata: dict[str, Any] | None = None


class AlertActivityOut(BaseModel):
    id: int
    alert_id: int
    user_id: int
    action: str
    note: str | None = None
    metadata: dict[str, Any] | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
