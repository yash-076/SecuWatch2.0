from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AlertOut(BaseModel):
    id: int
    device_id: int
    type: str
    severity: str
    description: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AlertListResponse(BaseModel):
    total: int
    page: int
    limit: int
    alerts: list[AlertOut]
