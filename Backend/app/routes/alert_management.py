from fastapi import APIRouter, Depends, HTTPException, Path, status

from app.dependencies import get_alert_management_service, get_current_user
from app.models.alert import AlertStatus
from app.models.alert_activity import AlertActivityAction
from app.models.user import User
from app.schemas.alert import (
    AddAlertActivityRequest,
    AlertActivityOut,
    AlertOut,
    AssignAlertRequest,
    UpdateAlertStatusRequest,
)
from app.services.alert_management_service import AlertManagementService

router = APIRouter(prefix="/alerts", tags=["Alert Management"])


@router.patch("/{alert_id}/assign-to-me", response_model=AlertOut)
def assign_alert_to_me(
    alert_id: int = Path(ge=1),
    current_user: User = Depends(get_current_user),
    alert_management_service: AlertManagementService = Depends(get_alert_management_service),
):
    alert = alert_management_service.get_alert_for_user_scope(alert_id=alert_id, user=current_user)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    try:
        return alert_management_service.assign_alert_to_self(alert=alert, current_user=current_user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.patch("/{alert_id}/assign", response_model=AlertOut)
def assign_alert_to_user(
    payload: AssignAlertRequest,
    alert_id: int = Path(ge=1),
    current_user: User = Depends(get_current_user),
    alert_management_service: AlertManagementService = Depends(get_alert_management_service),
):
    alert = alert_management_service.get_alert_for_user_scope(alert_id=alert_id, user=current_user)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    try:
        alert_management_service.ensure_admin(current_user)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    target_user = alert_management_service.get_user_in_same_organization(
        target_user_id=payload.user_id,
        current_user=current_user,
    )
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found in organization")

    try:
        return alert_management_service.assign_alert_to_user(alert=alert, user=target_user, actor=current_user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.patch("/{alert_id}/status", response_model=AlertOut)
def update_alert_status(
    payload: UpdateAlertStatusRequest,
    alert_id: int = Path(ge=1),
    current_user: User = Depends(get_current_user),
    alert_management_service: AlertManagementService = Depends(get_alert_management_service),
):
    alert = alert_management_service.get_alert_for_user_scope(alert_id=alert_id, user=current_user)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    if not alert_management_service.can_modify_alert(alert=alert, user=current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only assigned user or admin can modify this alert",
        )

    try:
        new_status = AlertStatus(payload.status)
        return alert_management_service.update_alert_status(alert=alert, status=new_status, user=current_user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/{alert_id}/activity", response_model=AlertActivityOut, status_code=status.HTTP_201_CREATED)
def add_alert_activity(
    payload: AddAlertActivityRequest,
    alert_id: int = Path(ge=1),
    current_user: User = Depends(get_current_user),
    alert_management_service: AlertManagementService = Depends(get_alert_management_service),
):
    alert = alert_management_service.get_alert_for_user_scope(alert_id=alert_id, user=current_user)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    if not alert_management_service.can_modify_alert(alert=alert, user=current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only assigned user or admin can modify this alert",
        )

    activity = alert_management_service.add_alert_activity(
        alert=alert,
        user=current_user,
        action=AlertActivityAction.COMMENT_ADDED,
        note=payload.note,
        metadata=payload.metadata,
    )
    return AlertActivityOut(
        id=activity.id,
        alert_id=activity.alert_id,
        user_id=activity.user_id,
        action=activity.action.value,
        note=activity.note,
        metadata=activity.metadata_json,
        created_at=activity.created_at,
    )


@router.get("/{alert_id}/activity", response_model=list[AlertActivityOut])
def get_alert_activity(
    alert_id: int = Path(ge=1),
    current_user: User = Depends(get_current_user),
    alert_management_service: AlertManagementService = Depends(get_alert_management_service),
):
    alert = alert_management_service.get_alert_for_user_scope(alert_id=alert_id, user=current_user)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    activities = alert_management_service.list_alert_activities(alert=alert)
    return [
        AlertActivityOut(
            id=item.id,
            alert_id=item.alert_id,
            user_id=item.user_id,
            action=item.action.value,
            note=item.note,
            metadata=item.metadata_json,
            created_at=item.created_at,
        )
        for item in activities
    ]
