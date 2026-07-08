from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_current_user, get_device_service, get_alert_service
from app.schemas.device import (
    DeviceCreateRequest,
    DeviceCreateResponse,
    DeviceDashboardOut,
    DeviceDeleteResponse,
    DeviceConfigRequest,
    DeviceConfigResponse,
    DeviceConfigUpdateRequest,
    DeviceAlertIngestRequest,
    DeviceAlertIngestResponse,
)
from app.services.device_service import DeviceService
from app.services.alert_engine.base import AlertData
from app.services.websocket_manager import ws_manager

router = APIRouter(prefix="/devices", tags=["Devices"])


@router.post("", response_model=DeviceCreateResponse, status_code=status.HTTP_201_CREATED)
def create_device(
    payload: DeviceCreateRequest,
    current_user=Depends(get_current_user),
    device_service: DeviceService = Depends(get_device_service),
):
    try:
        device, api_key = device_service.create_device(
            user=current_user,
            device_name=payload.device_name,
            device_type=payload.device_type,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return DeviceCreateResponse(
        id=device.id,
        device_name=device.device_name,
        device_type=device.device_type,
        api_key=api_key,
    )


@router.get("", response_model=list[DeviceDashboardOut])
def list_devices(
    current_user=Depends(get_current_user),
    device_service: DeviceService = Depends(get_device_service),
):
    return device_service.get_devices_with_insights(user=current_user)


@router.delete("/{device_id}", response_model=DeviceDeleteResponse)
def delete_device(
    device_id: int,
    current_user=Depends(get_current_user),
    device_service: DeviceService = Depends(get_device_service),
):
    try:
        deleted_device = device_service.delete_device(user=current_user, device_id=device_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return DeviceDeleteResponse(message=f"Device '{deleted_device.device_name}' deleted")


@router.get("/{device_id}/config", response_model=DeviceConfigResponse)
def get_device_configuration(
    device_id: int,
    current_user=Depends(get_current_user),
    device_service: DeviceService = Depends(get_device_service),
):
    try:
        device = device_service.get_device_by_id_for_user(user=current_user, device_id=device_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return DeviceConfigResponse(
        success=True,
        device_id=device.id,
        heartbeat_interval=device.heartbeat_interval,
        log_min_interval=device.log_min_interval,
        log_max_interval=device.log_max_interval,
        alert_config=device.alert_config,
    )


@router.put("/{device_id}/config", response_model=DeviceConfigResponse)
def update_device_configuration(
    device_id: int,
    payload: DeviceConfigUpdateRequest,
    current_user=Depends(get_current_user),
    device_service: DeviceService = Depends(get_device_service),
):
    try:
        device = device_service.update_device_config(
            user=current_user,
            device_id=device_id,
            heartbeat_interval=payload.heartbeat_interval,
            log_min_interval=payload.log_min_interval,
            log_max_interval=payload.log_max_interval,
            alert_config=payload.alert_config,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return DeviceConfigResponse(
        success=True,
        device_id=device.id,
        heartbeat_interval=device.heartbeat_interval,
        log_min_interval=device.log_min_interval,
        log_max_interval=device.log_max_interval,
        alert_config=device.alert_config,
    )


@router.post("/config", response_model=DeviceConfigResponse)
def device_get_config(
    payload: DeviceConfigRequest,
    device_service: DeviceService = Depends(get_device_service),
):
    try:
        device = device_service.authenticate_device(
            device_id=payload.device_id,
            api_key=payload.api_key,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    return DeviceConfigResponse(
        success=True,
        device_id=device.id,
        heartbeat_interval=device.heartbeat_interval,
        log_min_interval=device.log_min_interval,
        log_max_interval=device.log_max_interval,
        alert_config=device.alert_config,
    )


@router.post("/alerts", response_model=DeviceAlertIngestResponse, status_code=status.HTTP_201_CREATED)
def device_report_alert(
    payload: DeviceAlertIngestRequest,
    device_service: DeviceService = Depends(get_device_service),
    alert_service=Depends(get_alert_service),
):
    try:
        device = device_service.authenticate_device(
            device_id=payload.device_id,
            api_key=payload.api_key,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    alert_data = AlertData(
        type=payload.type,
        severity=payload.severity,
        description=payload.description,
    )

    try:
        alert = alert_service.create_alert(
            device=device,
            alert_data=alert_data,
            raw_log={
                "device_id": device.id,
                "device_type": device.device_type,
                "message": f"Direct alert reported by device: {payload.description}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

        if alert is not None:
            # Broadcast the alert to WebSocket clients in the same organization
            message = {
                "id": alert.id,
                "device_id": alert.device_id,
                "organization_id": device.user.organization_id,
                "type": alert.type,
                "severity": alert.severity,
                "description": alert.description,
                "created_at": alert.created_at.isoformat() if alert.created_at else None,
            }
            ws_manager.broadcast_sync(message)
            alert_id = alert.id
        else:
            alert_id = 0

    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return DeviceAlertIngestResponse(
        success=True,
        alert_id=alert_id,
    )

