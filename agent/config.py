import os
import json
import platform

# Try to load .env manually
config_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(config_dir, ".env")
if os.path.exists(env_path):
    try:
        with open(env_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip()
    except Exception as e:
        print(f"[CONFIG] Error parsing .env file: {e}")

# Environment variable overrides are supported for quick local testing.
BACKEND_URL = os.getenv("SECUWATCH_BACKEND_URL", "http://localhost:8000")
DEVICE_ID = int(os.getenv("SECUWATCH_DEVICE_ID", "2"))
API_KEY = os.getenv("SECUWATCH_API_KEY", "rd_60uh02g6tY8i1oNoixGtYWZkza2Ib3kQTpx7JgpE")


# Timings (seconds)
HEARTBEAT_INTERVAL = 30
LOG_MIN_INTERVAL = 5
LOG_MAX_INTERVAL = 10
RETRY_DELAY = 5
REQUEST_TIMEOUT = 10

# Local Alerting defaults
LOCAL_DETECTION_ENABLED = True
SEVERITY_THRESHOLD = "MEDIUM"

# Log Harvesting Sources configuration
WATCH_FILES = []
WINDOWS_EVENT_CHANNELS = ["Security", "System", "Application"]

# Load agent_config.json if present
config_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(config_dir, "agent_config.json")

if os.path.exists(config_path):
    try:
        with open(config_path, "r") as f:
            data = json.load(f)
            if "watch_files" in data:
                WATCH_FILES = data["watch_files"]
            if "windows_event_channels" in data:
                WINDOWS_EVENT_CHANNELS = data["windows_event_channels"]
            print(f"[CONFIG] Loaded configuration from {config_path}")
    except Exception as e:
        print(f"[CONFIG] Error loading agent_config.json: {e}")

# Apply environment variable overrides if present
env_files = os.getenv("SECUWATCH_WATCH_FILES")
if env_files:
    WATCH_FILES = [p.strip() for p in env_files.split(",") if p.strip()]

env_channels = os.getenv("SECUWATCH_WINDOWS_EVENT_LOGS")
if env_channels:
    WINDOWS_EVENT_CHANNELS = [c.strip() for c in env_channels.split(",") if c.strip()]

# If watch_files is empty, set platform-specific defaults
if not WATCH_FILES:
    if platform.system() == "Windows":
        WATCH_FILES = [
            r"C:\Apache24\logs\access.log",
            r"C:\Apache24\logs\error.log",
        ]
    else:
        WATCH_FILES = [
            "/var/log/auth.log",
            "/var/log/syslog",
            "/var/log/apache2/access.log",
            "/var/log/apache2/error.log",
        ]

