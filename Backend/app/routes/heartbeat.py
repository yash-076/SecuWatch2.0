from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.device import HeartbeatRequest, HeartbeatResponse
from app.services.device_service import DeviceService, get_device_status
from app.services.kafka_producer import produce_heartbeat_event
from app.dependencies import get_device_service

router = APIRouter(tags=["Heartbeat"])


@router.post("/heartbeat", response_model=HeartbeatResponse)
def heartbeat(
    payload: HeartbeatRequest,
    device_service: DeviceService = Depends(get_device_service),
):
    try:
        device = device_service.authenticate_device(
            device_id=payload.device_id,
            api_key=payload.api_key,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    updated_device = device_service.update_device_last_seen(device)
    if updated_device.last_seen is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update heartbeat timestamp",
        )

    produce_heartbeat_event(
        {
            "device_id": updated_device.id,
            "timestamp": updated_device.last_seen.isoformat(),
            "status": get_device_status(updated_device.last_seen),
        }
    )

    return HeartbeatResponse(
        success=True,
        device_id=updated_device.id,
        last_seen=updated_device.last_seen,
        status=get_device_status(updated_device.last_seen),
    )
