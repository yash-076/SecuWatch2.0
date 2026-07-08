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
    api_key: str | None = None
    ip_address: str | None = None
    last_seen: datetime | None
    status: str
    alerts_summary: AlertsSummaryOut
    heartbeat_interval: int
    log_min_interval: int
    log_max_interval: int
    alert_config: str | None = None

    model_config = ConfigDict(from_attributes=True)


class HeartbeatRequest(BaseModel):
    device_id: int
    api_key: str = Field(min_length=1)


class HeartbeatResponse(BaseModel):
    success: bool
    device_id: int
    last_seen: datetime
    status: str
    heartbeat_interval: int | None = None
    log_min_interval: int | None = None
    log_max_interval: int | None = None
    alert_config: str | None = None


class DeviceConfigRequest(BaseModel):
    device_id: int
    api_key: str = Field(min_length=1)


class DeviceConfigResponse(BaseModel):
    success: bool
    device_id: int
    heartbeat_interval: int
    log_min_interval: int
    log_max_interval: int
    alert_config: str | None = None


class DeviceConfigUpdateRequest(BaseModel):
    heartbeat_interval: int | None = Field(default=None, ge=1, le=3600)
    log_min_interval: int | None = Field(default=None, ge=1, le=3600)
    log_max_interval: int | None = Field(default=None, ge=1, le=3600)
    alert_config: str | None = Field(default=None)


class DeviceAlertIngestRequest(BaseModel):
    device_id: int
    api_key: str = Field(min_length=1)
    type: str = Field(min_length=1, max_length=100)
    severity: Literal["LOW", "MEDIUM", "HIGH"]
    description: str = Field(min_length=1)


class DeviceAlertIngestResponse(BaseModel):
    success: bool
    alert_id: int
