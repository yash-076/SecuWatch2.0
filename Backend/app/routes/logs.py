from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_device_service, get_log_service
from app.schemas.log import LogIngestRequest, LogIngestResponse
from app.services.device_service import DeviceService
from app.services.kafka_producer import produce_log_event
from app.services.log_service import LogService

router = APIRouter(tags=["Logs"])


@router.post("/logs", response_model=LogIngestResponse, status_code=status.HTTP_201_CREATED)
def ingest_log(
    payload: LogIngestRequest,
    device_service: DeviceService = Depends(get_device_service),
    log_service: LogService = Depends(get_log_service),
):
    try:
        device = device_service.authenticate_device(
            device_id=payload.device_id,
            api_key=payload.api_key,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    try:
        log = log_service.create_log(
            device=device,
            message=payload.message,
            timestamp=payload.timestamp,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    # Publish lightweight event for async processing by Kafka consumers.
    produce_log_event(
        {
            "log_id": log.id,
            "device_id": log.device_id,
            "message": log.message,
            "timestamp": log.timestamp.isoformat(),
        }
    )

    last_seen_updated = True
    try:
        device_service.update_device_last_seen(device)
    except Exception:
        # Best effort backup heartbeat update; ingestion success should not be blocked.
        last_seen_updated = False

    return LogIngestResponse(
        success=True,
        log_id=log.id,
        device_id=log.device_id,
        timestamp=log.timestamp,
        event_type=LogService.EVENT_LOG_RECEIVED,
        last_seen_updated=last_seen_updated,
    )