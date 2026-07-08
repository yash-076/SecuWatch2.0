import random
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
    start_heartbeat_thread,
)

LOG_PATTERNS = {
    "linux": [
        "Failed SSH login attempt",
        "User logged in successfully",
    ],
    "web": [
        "GET /index.php?id=1 OR 1=1",
        "Suspicious user agent detected",
    ],
    "windows": [
        "Failed RDP login",
        "Admin privilege escalation attempt",
    ],
    "application": [
        "Unhandled exception occurred",
        "Database connection error",
    ],
}


def generate_log_message() -> str:
    device_type = random.choice(list(LOG_PATTERNS.keys()))
    message = random.choice(LOG_PATTERNS[device_type])
    return f"[{device_type.upper()}] {message}"


def log_loop(stop_event: threading.Event) -> None:
    """Mock log simulator loop."""
    with requests.Session() as session:
        while not stop_event.is_set():
            message = generate_log_message()
            payload = {
                "device_id": DEVICE_ID,
                "api_key": API_KEY,
                "message": message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            print(f"Sent log (Mock) | message=\"{message}\"")
            post_with_retry(session, "/logs", payload, "log")

            with agent_state.lock:
                local_detect_enabled = agent_state.local_detection_enabled
                threshold = agent_state.severity_threshold

            if local_detect_enabled:
                threat_info = check_log_for_threat(message)
                if threat_info:
                    alert_type, severity = threat_info
                    if is_severity_met(severity, threshold):
                        print(f"  [LOCAL DETECT] Anomaly found: type={alert_type}, severity={severity}. Sending direct alert...")
                        alert_payload = {
                            "device_id": DEVICE_ID,
                            "api_key": API_KEY,
                            "type": alert_type,
                            "severity": severity,
                            "description": f"[LOCAL DETECT] Local agent threat signature '{alert_type}' matches: {message}",
                        }
                        post_with_retry(session, "/devices/alerts", alert_payload, "alert")

            with agent_state.lock:
                min_delay = agent_state.log_min_interval
                max_delay = agent_state.log_max_interval

            delay = random.uniform(min_delay, max_delay)
            if stop_event.wait(delay):
                break


def main() -> None:
    stop_event = threading.Event()
    
    print("[MOCK AGENT] Starting SecuWatch Mock Log Simulator...")
    heartbeat_thread = start_heartbeat_thread(stop_event)
    
    logs_thread = threading.Thread(target=log_loop, args=(stop_event,), daemon=True)
    logs_thread.start()

    print("Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping mock agent...")
        stop_event.set()
        heartbeat_thread.join(timeout=2)
        logs_thread.join(timeout=2)
        print("Mock agent stopped.")


if __name__ == "__main__":
    main()
