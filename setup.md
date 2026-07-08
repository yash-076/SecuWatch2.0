# ⚙️ SecuWatch 2.0: Installation & Setup Guide

This document describes how to set up the SecuWatch 2.0 system from scratch, configure environment variables, run backend and frontend servers, and hook up monitoring agents.

---

## 📋 Prerequisites
Ensure the following services are installed and running on your system:
*   **Python 3.10+**
*   **Node.js 18+** (with npm)
*   **PostgreSQL** (Active server running locally or accessible via network)
*   **Redis** (Active server used for deduplication caches and websocket broadcasts)

---

## 1. Backend Server Setup

### Step 1: Install Dependencies
Navigate to the `Backend` directory, configure a python virtual environment, and install the required modules:
```bash
cd Backend
python -m venv venv

# Activate Virtual Environment:
# On Windows (CMD / PowerShell):
venv\Scripts\activate
# On Linux / macOS:
source venv/bin/activate

# Install libraries:
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables
Create a file named `.env` in the `Backend` directory:
```env
# Server settings
APP_LOG_LEVEL=info

# Database settings (Replace credentials matching your local PostgreSQL instance)
DATABASE_URL=postgresql://postgres:password@localhost:5432/secuwatch2
AUTO_CREATE_DATABASE=true

# Redis settings
REDIS_URL=redis://localhost:6379/0

# Security (Set a secure random string)
SECRET_KEY=yoursecretkeyhere
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Kafka settings (Optional, defaults are disabled)
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPICS_AUTO_CREATE=false

# Triage configuration
ALERT_DEDUPE_WINDOW_SECONDS=300
```
*Note: If `AUTO_CREATE_DATABASE=true` is set, SecuWatch will attempt to create the target PostgreSQL database automatically on startup if it does not already exist.*

### Step 3: Run the Backend Server
Launch the server using Uvicorn:
```bash
uvicorn app.main:app --reload --port 8000
```
The server will boot and display:
`INFO: Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)`

You can access the auto-generated Swagger API documentation at:
`http://127.0.0.1:8000/docs`

---

## 2. Frontend Setup & Run

### Step 1: Install Dependencies
Navigate to the `Frontend` directory and install the Node packages:
```bash
cd Frontend
npm install
```

### Step 2: Run Developer Server
Start the Vite developer server:
```bash
npm run dev
```
The console will display:
`  VITE v5.4.x  ready in X ms`
`  ➜  Local:   http://localhost:5173/`

### Step 3: Verify Build (Optional)
To verify everything compiles cleanly for production deployment:
```bash
npm run build
```

---

## 3. Registering & Deploying Agents on Remote Servers

Since you are deploying the SecuWatch backend/dashboard to a central server, the agents must be deployed on the target systems (the machines you want to monitor). Follow these steps to configure and run the agents on any target Linux or Windows host:

### Step 1: Register the Device & Retrieve Credentials
1.  Open the SecuWatch Dashboard (e.g. `http://your-server-ip:5173`).
2.  Go to the **Devices** page in the left sidebar.
3.  Click **Add Device** in the upper right.
4.  Provide a name (e.g., `Linux-Database-01`) and select its category type (`linux`, `windows`, `web`, or `application`).
5.  Click **Add Device** to save.
6.  Look at the device entry:
    *   **Device ID**: Find the numerical Database ID (e.g. `1` or `2` — this is mapped as `DEVICE_ID` for configuration).
    *   **API Key**: Click the copy icon next to the masked key to copy the plain string key (e.g., `rd_xxxxxxxx...`).

---

### Step 2: Set Up the Agent on the Target Machine
Copy only the `agent/` folder from this repository onto your target machine.

1.  **Configure Virtual Environment**:
    Navigate to the copied `agent` directory and configure python:
    ```bash
    cd agent
    python -m venv venv

    # Activate Virtual Environment:
    # Linux/macOS:
    source venv/bin/activate
    # Windows:
    venv\Scripts\activate
    ```
2.  **Install Agent Requirements**:
    ```bash
    pip install -r requirements.txt
    ```

---

### Step 3: Configure Agent Environment Variables
Create a file named `.env` in the `agent/` directory on the target machine. Specify the central server URL, the Device ID, and the API key retrieved in **Step 1**:

```env
# Point to your deployed central backend server
SECUWATCH_BACKEND_URL=http://your-central-server-ip:8000
SECUWATCH_DEVICE_ID=3
SECUWATCH_API_KEY=rd_your_copied_api_key_here
```

Configure local path watch lists or events in `agent/agent_config.json`:
```json
{
  "watch_files": [
    "/var/log/apache2/access.log",
    "/var/log/auth.log"
  ],
  "windows_event_channels": [
    "Security"
  ]
}
```

---

### Step 4: Run the Target Agent Script

Depending on the OS and role of the target machine, run one of the following scripts:

#### A. Web Log Tailer (`run_web_log_tailer.py`)
Tracks Apache, Nginx, or application access/error log files in real-time. It continuously tails files configured in `watch_files`.
```bash
python run_web_log_tailer.py
```

#### B. Linux Syslog Agent (`run_linux_syslog.py`)
Reads system authentication logs (e.g. `/var/log/auth.log` or `/var/log/secure`), triaging root login events, SSH auth failures, and sudo commands.
```bash
python run_linux_syslog.py
```

#### C. Windows Event Log Collector (`run_windows_events.py`)
Queries native Windows Event Viewer channels (e.g., Security) using PyWin32 integration to capture logon failures (Event ID 4625) and privilege assignments (Event ID 4672).
*Note: Requires `pywin32` library installed on the Windows host.*
```bash
python run_windows_events.py
```

#### D. Mock Threat Simulator (`run_mock_simulator.py`)
For testing/validation. Simulates a target server sending benign heartbeats and periodic mock malicious attacks (SQL Injection attempts, brute-force root SSH logins) to test the end-to-end dashboard loop.
```bash
python run_mock_simulator.py
```

---

### Step 5: Verify Threat Stream Lifecycle
1.  Go to the **Devices** page on the SecuWatch Dashboard.
2.  Your target host's status indicator will turn green (**Online**) as soon as it receives the first heartbeat request.
3.  Any threat detected locally by the agent, or flagged by the backend signature engine, will trigger a red highlight and stream instantly to the **Dashboard** and **Alerts** pages via WebSockets.
