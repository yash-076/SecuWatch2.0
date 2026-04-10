from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.models.log import Log


@dataclass
class AlertData:
    """Data structure for alert information."""
    type: str
    severity: str  # LOW, MEDIUM, HIGH
    description: str


class BaseAlertEngine(ABC):
    """
    Base class for device-specific alert engines.
    
    Implementations should detect anomalies/threats in log messages
    and return alert data or None if no alert is triggered.
    """

    @abstractmethod
    def process_log(self, log: Log) -> AlertData | None:
        """
        Process a log and determine if an alert should be generated.
        
        Args:
            log: The log entry to process
            
        Returns:
            AlertData if an alert condition is detected, None otherwise
        """
        pass
