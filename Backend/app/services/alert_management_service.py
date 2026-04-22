from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.alert import Alert, AlertStatus
from app.models.alert_activity import AlertActivity, AlertActivityAction
from app.models.device import Device
from app.models.user import User


class AlertManagementService:
    def __init__(self, db: Session):
        self.db = db

    def get_alert_for_user_scope(self, alert_id: int, user: User) -> Alert | None:
        return self.db.scalar(
            select(Alert)
            .join(Device, Device.id == Alert.device_id)
            .join(User, User.id == Device.user_id)
            .where(Alert.id == alert_id, User.organization_id == user.organization_id)
        )

    def get_user_in_same_organization(self, target_user_id: int, current_user: User) -> User | None:
        return self.db.scalar(
            select(User).where(
                User.id == target_user_id,
                User.organization_id == current_user.organization_id,
            )
        )

    def assign_alert_to_user(self, alert: Alert, user: User, actor: User) -> Alert:
        self._ensure_not_resolved(alert)
        alert.assigned_to = user.id
        alert.assigned_role = user.role.value
        alert.status = AlertStatus.IN_PROGRESS
        alert.updated_at = datetime.now(timezone.utc)
        self.add_alert_activity(
            alert=alert,
            user=actor,
            action=AlertActivityAction.ASSIGNED,
            note=f"Alert assigned to user {user.id}",
            metadata={"assigned_to": user.id, "assigned_role": user.role.value},
            commit=False,
        )
        self.db.commit()
        self.db.refresh(alert)
        return alert

    def assign_alert_to_self(self, alert: Alert, current_user: User) -> Alert:
        return self.assign_alert_to_user(alert=alert, user=current_user, actor=current_user)

    def update_alert_status(self, alert: Alert, status: AlertStatus, user: User) -> Alert:
        self._validate_status_transition(alert.status, status)
        alert.status = status
        alert.updated_at = datetime.now(timezone.utc)
        action = AlertActivityAction.RESOLVED if status == AlertStatus.RESOLVED else AlertActivityAction.STATUS_CHANGED
        self.add_alert_activity(
            alert=alert,
            user=user,
            action=action,
            note=f"Alert status changed to {status.value}",
            metadata={"status": status.value},
            commit=False,
        )
        self.db.commit()
        self.db.refresh(alert)
        return alert

    def add_alert_activity(
        self,
        alert: Alert,
        user: User,
        action: AlertActivityAction,
        note: str | None = None,
        metadata: dict[str, Any] | None = None,
        commit: bool = True,
    ) -> AlertActivity:
        activity = AlertActivity(
            alert_id=alert.id,
            user_id=user.id,
            action=action,
            note=note,
            metadata_json=metadata,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(activity)
        if commit:
            self.db.commit()
            self.db.refresh(activity)
        return activity

    def list_alert_activities(self, alert: Alert) -> list[AlertActivity]:
        stmt = (
            select(AlertActivity)
            .where(AlertActivity.alert_id == alert.id)
            .order_by(AlertActivity.created_at.asc())
        )
        return list(self.db.scalars(stmt))

    @staticmethod
    def can_modify_alert(alert: Alert, user: User) -> bool:
        return user.role == User.Role.ADMIN or alert.assigned_to == user.id

    @staticmethod
    def ensure_admin(user: User) -> None:
        if user.role != User.Role.ADMIN:
            raise PermissionError("Only admin users can perform this action")

    @staticmethod
    def _validate_status_transition(current_status: AlertStatus, target_status: AlertStatus) -> None:
        if current_status == target_status:
            raise ValueError("Alert already has the requested status")

        allowed = {
            AlertStatus.NEW: {AlertStatus.IN_PROGRESS, AlertStatus.RESOLVED},
            AlertStatus.IN_PROGRESS: {AlertStatus.RESOLVED},
            AlertStatus.RESOLVED: set(),
        }
        if target_status not in allowed[current_status]:
            raise ValueError(f"Invalid status transition from {current_status.value} to {target_status.value}")

    @staticmethod
    def _ensure_not_resolved(alert: Alert) -> None:
        if alert.status == AlertStatus.RESOLVED:
            raise ValueError("Resolved alerts cannot be reassigned")
