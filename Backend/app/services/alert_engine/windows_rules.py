import re

from app.models.log import Log
from app.services.alert_engine.base import AlertData, BaseAlertEngine


class WindowsAlertEngine(BaseAlertEngine):
    """Alert detection rules for Windows devices."""

    def process_log(self, log: Log) -> AlertData | None:
        """
        Detect security events in Windows logs.
        
        Rules:
        - Failed RDP login → HIGH alert
        - Failed user authentication → MEDIUM alert
        """
        message = log.message.lower()

        # Rule 1: Failed RDP login
        if self._is_failed_rdp_login(message):
            return AlertData(
                type="FAILED_RDP_LOGIN",
                severity="HIGH",
                description=f"Failed RDP login detected: {log.message[:100]}",
            )

        # Rule 2: Failed user authentication
        if self._is_failed_authentication(message):
            return AlertData(
                type="FAILED_AUTHENTICATION",
                severity="MEDIUM",
                description=f"Failed user authentication: {log.message[:100]}",
            )

        return None

    @staticmethod
    def _is_failed_rdp_login(message: str) -> bool:
        """Check if message indicates a failed RDP login."""
        rdp_patterns = [
            r"rdp.*failed",
            r"4625",  # Event ID for failed login
            r"remote desktop.*failed",
            r"logon failure",
        ]
        return any(re.search(pattern, message) for pattern in rdp_patterns)

    @staticmethod
    def _is_failed_authentication(message: str) -> bool:
        """Check if message indicates failed authentication."""
        auth_patterns = [
            r"authentication failed",
            r"logon failed",
            r"invalid credentials",
            r"password incorrect",
        ]
        return any(re.search(pattern, message) for pattern in auth_patterns)
