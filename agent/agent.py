from __future__ import annotations

import random
import threading
import time
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


def post_with_retry(session: requests.Session, endpoint: str, payload: dict, event_name: str) -> None:
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

            return
        except requests.RequestException as exc:
            print(f"Error sending {event_name}: {exc}. Retrying in {RETRY_DELAY}s...")
            time.sleep(RETRY_DELAY)


def heartbeat_loop(stop_event: threading.Event) -> None:
    with requests.Session() as session:
        while not stop_event.is_set():
            payload = {
                "device_id": DEVICE_ID,
                "api_key": API_KEY,
            }
            post_with_retry(session, "/heartbeat", payload, "heartbeat")

            if stop_event.wait(HEARTBEAT_INTERVAL):
                break


def log_loop(stop_event: threading.Event) -> None:
    with requests.Session() as session:
        while not stop_event.is_set():
            payload = {
                "device_id": DEVICE_ID,
                "api_key": API_KEY,
                "message": generate_log_message(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            print(f"Sent log | message=\"{payload['message']}\"")
            post_with_retry(session, "/logs", payload, "log")

            delay = random.uniform(LOG_MIN_INTERVAL, LOG_MAX_INTERVAL)
            if stop_event.wait(delay):
                break


def main() -> None:
    stop_event = threading.Event()

    heartbeat_thread = threading.Thread(target=heartbeat_loop, args=(stop_event,), daemon=True)
    logs_thread = threading.Thread(target=log_loop, args=(stop_event,), daemon=True)

    heartbeat_thread.start()
    logs_thread.start()

    print("SecuWatch agent started.")
    print(f"Backend: {BACKEND_URL}")
    print(f"Device ID: {DEVICE_ID}")
    print("Press Ctrl+C to stop.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping agent...")
        stop_event.set()
        heartbeat_thread.join(timeout=2)
        logs_thread.join(timeout=2)
        print("Agent stopped.")


if __name__ == "__main__":
    main()
