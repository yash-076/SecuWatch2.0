import os
import threading
import time
import requests
from datetime import datetime, timezone

from config import DEVICE_ID, API_KEY
from core import (
    agent_state,
    check_log_for_threat,
    is_severity_met,
    post_with_retry,
    enrich_log_message,
    start_heartbeat_thread,
)


class FileTailer:
    """Tails a text file, handling rotations and yielding new lines."""
    def __init__(self, filepath: str):
        self.filepath = os.path.abspath(filepath)
        self.last_position = None
        self.last_inode = None
        self.warned_missing = False

    def tail(self) -> list[str]:
        """Yields new lines from the file if they exist."""
        if not os.path.exists(self.filepath):
            if not self.warned_missing:
                print(f"[TAILER] File not found: '{self.filepath}'. Will retry when it appears.")
                self.warned_missing = True
            return []

        if self.warned_missing:
            print(f"[TAILER] File found: '{self.filepath}'. Starting monitoring.")
            self.warned_missing = False

        lines = []
        try:
            stat = os.stat(self.filepath)
            current_size = stat.st_size
            current_inode = getattr(stat, 'st_ino', None)

            # First run: seek to end to only monitor new events
            if self.last_position is None:
                self.last_position = current_size
                self.last_inode = current_inode
                return []

            # Rotation/truncation check
            if current_inode != self.last_inode or current_size < self.last_position:
                print(f"[TAILER] File rotated or truncated: '{self.filepath}'")
                self.last_position = 0

            self.last_inode = current_inode

            if current_size > self.last_position:
                with open(self.filepath, "r", encoding="utf-8", errors="ignore") as f:
                    f.seek(self.last_position)
                    content = f.read()
                    self.last_position = f.tell()
                    lines = [line.rstrip('\r\n') for line in content.splitlines() if line.strip()]
        except Exception as e:
            print(f"[TAILER] Error reading '{self.filepath}': {e}")

        return lines


def linux_syslog_loop(stop_event: threading.Event) -> None:
    # Monitor auth.log and syslog by default on Linux
    sys_paths = ["/var/log/auth.log", "/var/log/syslog"]
    tailers = [FileTailer(p) for p in sys_paths]
    print(f"[SYS-LOG-AGENT] Monitoring Linux paths: {sys_paths}")
    
    with requests.Session() as session:
        while not stop_event.is_set():
            for tailer in tailers:
                lines = tailer.tail()
                for line in lines:
                    level = "INFO"
                    line_lower = line.lower()
                    if any(kw in line_lower for kw in ["error", "critical", "failed", "denied"]):
                        level = "ERROR"
                    elif any(kw in line_lower for kw in ["warning", "warn"]):
                        level = "WARNING"
                        
                    enriched = enrich_log_message(
                        source=f"File:{tailer.filepath}",
                        level=level,
                        raw_message=line
                    )
                    
                    payload = {
                        "device_id": DEVICE_ID,
                        "api_key": API_KEY,
                        "message": enriched,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                    print(f"Sent log (Linux) | message=\"{enriched[:120]}...\"")
                    post_with_retry(session, "/logs", payload, "log")
                    
                    with agent_state.lock:
                        local_detect_enabled = agent_state.local_detection_enabled
                        threshold = agent_state.severity_threshold
                        
                    if local_detect_enabled:
                        threat_info = check_log_for_threat(enriched)
                        if threat_info:
                            alert_type, severity = threat_info
                            if is_severity_met(severity, threshold):
                                print(f"  [LOCAL DETECT] Anomaly found: type={alert_type}, severity={severity}. Sending direct alert...")
                                alert_payload = {
                                    "device_id": DEVICE_ID,
                                    "api_key": API_KEY,
                                    "type": alert_type,
                                    "severity": severity,
                                    "description": f"[LOCAL DETECT] Local agent threat signature '{alert_type}' matches Linux syslog: {line}",
                                }
                                post_with_retry(session, "/devices/alerts", alert_payload, "alert")
            
            if stop_event.wait(1.0):
                break


def main() -> None:
    stop_event = threading.Event()
    
    print("[SYS-LOG-AGENT] Starting SecuWatch Linux Syslog Agent...")
    heartbeat_thread = start_heartbeat_thread(stop_event)
    
    sys_thread = threading.Thread(target=linux_syslog_loop, args=(stop_event,), daemon=True)
    sys_thread.start()

    print("Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping Linux syslog agent...")
        stop_event.set()
        heartbeat_thread.join(timeout=2)
        sys_thread.join(timeout=2)
        print("Linux syslog agent stopped.")


if __name__ == "__main__":
    main()
