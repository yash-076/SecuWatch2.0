from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_current_user, get_device_service
from app.schemas.device import (
    DeviceCreateRequest,
    DeviceCreateResponse,
    DeviceDashboardOut,
    DeviceDeleteResponse,
)
from app.services.device_service import DeviceService

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
