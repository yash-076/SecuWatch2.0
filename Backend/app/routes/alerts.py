from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import get_alert_service, get_current_user
from app.models.user import User
from app.schemas.alert import AlertListResponse, AlertOut
from app.services.alert_service import AlertService

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("", response_model=AlertListResponse)
def list_alerts(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1),
    severity: Literal["LOW", "MEDIUM", "HIGH"] | None = Query(default=None),
    device_id: int | None = Query(default=None, ge=1),
    from_time: datetime | None = Query(default=None),
    to_time: datetime | None = Query(default=None),
    search: str | None = Query(default=None),
    sort_by: Literal["id", "device_id", "type", "severity", "created_at"] = Query(
        default="created_at"
    ),
    order: Literal["asc", "desc"] = Query(default="desc"),
    current_user: User = Depends(get_current_user),
    alert_service: AlertService = Depends(get_alert_service),
):
    if from_time and to_time and from_time > to_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="from_time must be less than or equal to to_time",
        )

    alerts, total = alert_service.get_alerts(
        user=current_user,
        page=page,
        limit=limit,
        severity=severity,
        device_id=device_id,
        from_time=from_time,
        to_time=to_time,
        search=search,
        sort_by=sort_by,
        order=order,
    )

    return AlertListResponse(
        total=total,
        page=page,
        limit=limit,
        alerts=[AlertOut(**alert) for alert in alerts],
    )
