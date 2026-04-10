import os

# Environment variable overrides are supported for quick local testing.
BACKEND_URL = os.getenv("SECUWATCH_BACKEND_URL", "http://localhost:8000")
DEVICE_ID = int(os.getenv("SECUWATCH_DEVICE_ID", "1"))
API_KEY = os.getenv("SECUWATCH_API_KEY", "replace-with-device-api-key")

# Timings (seconds)
HEARTBEAT_INTERVAL = 30
LOG_MIN_INTERVAL = 5
LOG_MAX_INTERVAL = 10
RETRY_DELAY = 5
REQUEST_TIMEOUT = 10
