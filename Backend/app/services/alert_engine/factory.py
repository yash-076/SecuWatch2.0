from app.services.alert_engine.application_rules import ApplicationAlertEngine
from app.services.alert_engine.base import BaseAlertEngine
from app.services.alert_engine.linux_rules import LinuxAlertEngine
from app.services.alert_engine.web_rules import WebAlertEngine
from app.services.alert_engine.windows_rules import WindowsAlertEngine


class DefaultAlertEngine(BaseAlertEngine):
    """Default engine that doesn't generate any alerts."""

    def process_log(self, log) -> None:
        """Default: no alerts."""
        return None


def get_alert_engine(device_type: str) -> BaseAlertEngine:
    """
    Factory function to get the appropriate alert engine for a device type.
    
    Args:
        device_type: The type of device (linux, windows, web, application)
        
    Returns:
        An instance of the appropriate alert engine
    """
    device_type_lower = device_type.lower().strip() if device_type else ""

    engines = {
        "linux": LinuxAlertEngine,
        "windows": WindowsAlertEngine,
        "web": WebAlertEngine,
        "application": ApplicationAlertEngine,
    }

    engine_class = engines.get(device_type_lower, DefaultAlertEngine)
    return engine_class()
