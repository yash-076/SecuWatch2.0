from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class DeviceCreateRequest(BaseModel):
    device_name: str = Field(min_length=1, max_length=255)
    device_type: Literal["linux", "windows", "web", "application"]


class DeviceCreateResponse(BaseModel):
    id: int
    device_name: str
    device_type: str
    api_key: str

    model_config = ConfigDict(from_attributes=True)


class DeviceDeleteResponse(BaseModel):
    message: str


class DeviceOut(BaseModel):
    id: int
    device_name: str
    last_seen: datetime | None

    model_config = ConfigDict(from_attributes=True)


class AlertsSummaryOut(BaseModel):
    total: int
    high: int
    medium: int
    low: int


class DeviceDashboardOut(BaseModel):
    id: int
    device_name: str
    device_type: str
    last_seen: datetime | None
    status: str
    alerts_summary: AlertsSummaryOut


class HeartbeatRequest(BaseModel):
    device_id: int
    api_key: str = Field(min_length=1)


class HeartbeatResponse(BaseModel):
    success: bool
    device_id: int
    last_seen: datetime
    status: str
