import re

from app.models.log import Log
from app.services.alert_engine.base import AlertData, BaseAlertEngine


class LinuxAlertEngine(BaseAlertEngine):
    """Alert detection rules for Linux devices."""

    def process_log(self, log: Log) -> AlertData | None:
        """
        Detect security events in Linux logs.
        
        Rules:
        - Failed SSH login attempts → HIGH alert
        - Unauthorized access/permission denied → MEDIUM alert
        """
        message = log.message.lower()

        # Rule 1: Failed SSH login (multiple variations)
        if self._is_failed_ssh_login(message):
            return AlertData(
                type="FAILED_SSH_LOGIN",
                severity="HIGH",
                description=f"Failed SSH login detected: {log.message[:100]}",
            )

        # Rule 2: Unauthorized access / Permission denied
        if self._is_permission_denied(message):
            return AlertData(
                type="PERMISSION_DENIED",
                severity="MEDIUM",
                description=f"Permission denied or unauthorized access: {log.message[:100]}",
            )

        return None

    @staticmethod
    def _is_failed_ssh_login(message: str) -> bool:
        """Check if message indicates a failed SSH login."""
        ssh_patterns = [
            r"failed password",
            r"invalid user",
            r"authentication failure",
            r"ssh.*failed",
            r"wrong password",
            r"connection closed by authenticating user",
        ]
        return any(re.search(pattern, message) for pattern in ssh_patterns)

    @staticmethod
    def _is_permission_denied(message: str) -> bool:
        """Check if message indicates permission denial."""
        denied_patterns = [
            r"permission denied",
            r"unauthorized",
            r"access denied",
            r"forbidden",
        ]
        return any(re.search(pattern, message) for pattern in denied_patterns)
