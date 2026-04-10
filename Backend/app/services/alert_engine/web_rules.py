import re

from app.models.log import Log
from app.services.alert_engine.base import AlertData, BaseAlertEngine


class WebAlertEngine(BaseAlertEngine):
    """Alert detection rules for web devices (servers, APIs)."""

    def process_log(self, log: Log) -> AlertData | None:
        """
        Detect security events in web logs.
        
        Rules:
        - SQL injection patterns → HIGH alert
        - Suspicious HTTP status codes (4xx, 5xx) → MEDIUM alert
        """
        message = log.message.lower()

        # Rule 1: SQL injection detection
        if self._is_sql_injection(message):
            return AlertData(
                type="SQL_INJECTION_ATTEMPT",
                severity="HIGH",
                description=f"Potential SQL injection detected: {log.message[:100]}",
            )

        # Rule 2: Suspicious HTTP errors
        if self._is_suspicious_http_error(message):
            return AlertData(
                type="SUSPICIOUS_HTTP_ERROR",
                severity="MEDIUM",
                description=f"Suspicious HTTP error detected: {log.message[:100]}",
            )

        return None

    @staticmethod
    def _is_sql_injection(message: str) -> bool:
        """Check for SQL injection patterns."""
        sql_patterns = [
            r"union.*select",
            r"or\s+1\s*=\s*1",
            r"drop\s+table",
            r"exec\s*\(",
            r"script\s*>",
            r"sql.*error",
            r"syntax error",
        ]
        return any(re.search(pattern, message) for pattern in sql_patterns)

    @staticmethod
    def _is_suspicious_http_error(message: str) -> bool:
        """Check for suspicious HTTP error codes."""
        error_patterns = [
            r"http.*5[0-9]{2}",  # 5xx errors
            r"http.*401",  # Unauthorized
            r"http.*403",  # Forbidden
            r"status.*500",
            r"internal server error",
        ]
        return any(re.search(pattern, message) for pattern in error_patterns)
