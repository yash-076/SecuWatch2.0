import re

from app.models.log import Log
from app.services.alert_engine.base import AlertData, BaseAlertEngine


class ApplicationAlertEngine(BaseAlertEngine):
    """Alert detection rules for application logs."""

    def process_log(self, log: Log) -> AlertData | None:
        """
        Detect security and error events in application logs.
        
        Rules:
        - Critical errors → HIGH alert
        - Warning patterns → MEDIUM alert
        """
        message = log.message.lower()

        # Rule 1: Critical errors
        if self._is_critical_error(message):
            return AlertData(
                type="CRITICAL_ERROR",
                severity="HIGH",
                description=f"Critical error detected: {log.message[:100]}",
            )

        # Rule 2: Warning patterns
        if self._is_warning(message):
            return AlertData(
                type="WARNING_DETECTED",
                severity="MEDIUM",
                description=f"Application warning: {log.message[:100]}",
            )

        return None

    @staticmethod
    def _is_critical_error(message: str) -> bool:
        """Check for critical error patterns."""
        error_patterns = [
            r"fatal",
            r"critical",
            r"panic",
            r"exception",
            r"error.*code.*[0-9]{3,4}",
            r"segmentation fault",
            r"stack overflow",
        ]
        return any(re.search(pattern, message) for pattern in error_patterns)

    @staticmethod
    def _is_warning(message: str) -> bool:
        """Check for warning patterns."""
        warning_patterns = [
            r"warning",
            r"deprecated",
            r"timeout",
            r"retry",
            r"failed connection",
        ]
        return any(re.search(pattern, message) for pattern in warning_patterns)
