from __future__ import annotations

import os
import time
import random
import socket
import threading
from datetime import datetime, timezone

import requests

from config import (
    API_KEY,
    BACKEND_URL,
    DEVICE_ID,
    HEARTBEAT_INTERVAL,
    LOG_MAX_INTERVAL,
    LOG_MIN_INTERVAL,
    REQUEST_TIMEOUT,
    RETRY_DELAY,
    LOCAL_DETECTION_ENABLED,
    SEVERITY_THRESHOLD,
    WATCH_FILES,
    WINDOWS_EVENT_CHANNELS,
)

HOSTNAME = socket.gethostname()


class AgentState:
    """Thread-safe storage for runtime agent configuration fetched from the backend."""
    def __init__(self):
        self.lock = threading.Lock()
        self.heartbeat_interval = HEARTBEAT_INTERVAL
        self.log_min_interval = LOG_MIN_INTERVAL
        self.log_max_interval = LOG_MAX_INTERVAL
        self.local_detection_enabled = LOCAL_DETECTION_ENABLED
        self.severity_threshold = SEVERITY_THRESHOLD

    def update_config(self, config: dict):
        with self.lock:
            h_int = config.get("heartbeat_interval")
            l_min = config.get("log_min_interval")
            l_max = config.get("log_max_interval")
            alert_conf_str = config.get("alert_config")

            updated = False
            if h_int is not None and h_int != self.heartbeat_interval:
                print(f"[CONFIG] Heartbeat interval updated: {self.heartbeat_interval}s -> {h_int}s")
                self.heartbeat_interval = h_int
                updated = True
            if l_min is not None and l_min != self.log_min_interval:
                print(f"[CONFIG] Log min interval updated: {self.log_min_interval}s -> {l_min}s")
                self.log_min_interval = l_min
                updated = True
            if l_max is not None and l_max != self.log_max_interval:
                print(f"[CONFIG] Log max interval updated: {self.log_max_interval}s -> {l_max}s")
                self.log_max_interval = l_max
                updated = True

            if alert_conf_str:
                try:
                    import json
                    parsed = json.loads(alert_conf_str)
                    loc_det = parsed.get("local_detection", True)
                    sev_thresh = parsed.get("severity_threshold", "MEDIUM")
                    if loc_det != self.local_detection_enabled:
                        print(f"[CONFIG] Local detection enabled updated: {self.local_detection_enabled} -> {loc_det}")
                        self.local_detection_enabled = loc_det
                        updated = True
                    if sev_thresh != self.severity_threshold:
                        print(f"[CONFIG] Severity threshold updated: {self.severity_threshold} -> {sev_thresh}")
                        self.severity_threshold = sev_thresh
                        updated = True
                except Exception as e:
                    print(f"[CONFIG] Error parsing alert_config: {e}")

            if updated:
                print("[CONFIG] Runtime configuration synced and applied successfully.")


agent_state = AgentState()


def enrich_log_message(source: str, level: str, raw_message: str, event_id: str = "N/A") -> str:
    """Add Host, Source, Level, and Event ID metadata headers to the log message."""
    return f"[HOST: {HOSTNAME}] [SOURCE: {source}] [LEVEL: {level}] [EVENT_ID: {event_id}] {raw_message}"


def check_log_for_threat(message: str) -> tuple[str, str] | None:
    """Scan log message for threat signatures and return (alert_type, severity) or None."""
    msg_lower = message.lower()
    
    # Event IDs (Windows Security logon failures, privilege changes)
    if "event_id: 4625" in msg_lower:
        return "FAILED_RDP_LOGIN", "HIGH"
    elif "event_id: 4672" in msg_lower:
        return "PRIVILEGE_ESCALATION", "CRITICAL"

    # Text patterns
    if "failed ssh login" in msg_lower:
        return "FAILED_SSH_LOGIN", "HIGH"
    elif "1=1" in msg_lower or "union select" in msg_lower or "drop table" in msg_lower:
        return "SQL_INJECTION", "CRITICAL"
    elif "failed rdp login" in msg_lower or "logon failure" in msg_lower:
        return "FAILED_RDP_LOGIN", "HIGH"
    elif "privilege escalation" in msg_lower:
        return "PRIVILEGE_ESCALATION", "CRITICAL"
    elif "exception occurred" in msg_lower or "database connection error" in msg_lower or "core:error" in msg_lower:
        return "APPLICATION_CRITICAL", "MEDIUM"
    elif "suspicious user agent" in msg_lower:
        return "SUSPICIOUS_UA", "MEDIUM"
    return None


SEVERITY_LEVELS = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}


def is_severity_met(alert_severity: str, threshold: str) -> bool:
    """Verify if the alert severity is higher than or equal to the configured threshold."""
    return SEVERITY_LEVELS.get(alert_severity, 1) >= SEVERITY_LEVELS.get(threshold, 2)


def post_with_retry(session: requests.Session, endpoint: str, payload: dict, event_name: str) -> requests.Response:
    """Helper to post a payload with retry logic."""
    url = f"{BACKEND_URL.rstrip('/')}{endpoint}"

    while True:
        try:
            response = session.post(url, json=payload, timeout=REQUEST_TIMEOUT)
            print(f"Sent {event_name} | status={response.status_code}")

            if response.status_code >= 400:
                print(
                    f"{event_name.capitalize()} failed with status {response.status_code}. "
                    f"Retrying in {RETRY_DELAY}s..."
                )
                time.sleep(RETRY_DELAY)
                continue

            return response
        except requests.RequestException as exc:
            print(f"Error sending {event_name}: {exc}. Retrying in {RETRY_DELAY}s...")
            time.sleep(RETRY_DELAY)


def heartbeat_loop(stop_event: threading.Event) -> None:
    """Loop to sync status and retrieve runtime config updates."""
    with requests.Session() as session:
        while not stop_event.is_set():
            payload = {
                "device_id": DEVICE_ID,
                "api_key": API_KEY,
            }
            resp = post_with_retry(session, "/heartbeat", payload, "heartbeat")
            try:
                data = resp.json()
                agent_state.update_config(data)
            except Exception as e:
                print(f"Error parsing heartbeat response: {e}")

            with agent_state.lock:
                interval = agent_state.heartbeat_interval

            if stop_event.wait(interval):
                break


def start_heartbeat_thread(stop_event: threading.Event) -> threading.Thread:
    """Starts the configuration sync background heartbeat thread."""
    t = threading.Thread(target=heartbeat_loop, args=(stop_event,), daemon=True)
    t.start()
    return t
