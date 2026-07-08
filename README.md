# 🛡️ SecuWatch 2.0 — Real-Time Cybersecurity SOC Dashboard

SecuWatch 2.0 is a professional, multi-tenant Security Operations Center (SOC) dashboard. It aggregates logs from multiple distributed device agents (Windows, Linux, Web, Applications), processes them through a device-specific threat signature rules engine, saves security incidents to a persistent database, and streams alerts in real-time to a modern dashboard using WebSockets.

The application features a sleek, responsive dark-glass interface with neon-red accents, detailed threat metrics, device log config options, and AI analysis integration.

---

## 📁 Repository Structure

```
SecuWatch2.0/
├── Backend/                 # FastAPI Python backend server
│   ├── app/
│   │   ├── models/          # SQLAlchemy Database Models (PostgreSQL)
│   │   ├── routes/          # API endpoint routers (Auth, Devices, Alerts, Logs, WebSockets)
│   │   ├── services/        # Logic services (Deduplication, Threat rules engine, AI analysis)
│   │   └── utils/           # JWT, hashing, cryptography helper functions
│   ├── requirements.txt     # Python dependencies
│   └── .env                 # Backend environment config
│
├── Frontend/                # Vite + React + Tailwind CSS client
│   ├── src/
│   │   ├── components/      # Reusable widgets (Sidebar, Navbar, Charts, AlertDrawer)
│   │   ├── context/         # React Context for Global Authentication states
│   │   ├── pages/           # Landing page, Dashboard, Alerts table, Analytics, Device inventory
│   │   └── services/        # api.js client with Axios-style JWT interceptors
│   ├── index.html           # HTML entry point (Inter fonts loaded)
│   ├── tailwind.config.js   # Custom dark theme configuration
│   └── package.json         # Node.js dependencies
│
├── agent/                   # Logging agents for endpoint servers
│   ├── run_mock_simulator.py   # Mimics attack signatures for testing rules
│   ├── run_web_log_tailer.py   # Web server log monitor
│   ├── run_linux_syslog.py     # Linux auth/sudo syslog monitor
│   ├── run_windows_events.py   # Windows security event log collector
│   └── agent_config.json    # Local configuration file (Heartbeats, endpoints)
│
├── backend.md               # Backend Architecture Design Document
├── frontend.md              # Frontend Architecture Design Document
└── setup.md                 # Project Setup & Verification Instructions
```

---

## 🛠️ System Overview & Core Capabilities

### 1. Ingestion & Rule Execution
Agents tail files or query system event logs and send messages via HTTP POST to the backend. The backend `EventDispatcher` queries `get_alert_engine(device_type)` to parse lines using pre-configured regex patterns. If a malicious signature matches (such as SQL injection patterns or root privilege escalations), it outputs structured alert parameters.

### 2. Cache-First Deduplication
To prevent alerts flooding during automated attacks, alerts are hashed using device context and raw messages via SHA-256. These fingerprints are set in Redis (`SETNX`) with a configurable TTL (e.g. 5 minutes). If the hash exists, the backend suppresses the database commit.

### 3. Multi-Tenant WebSocket Broadcasting
Clients connect to `/ws/alerts` using their JWT authorization token. The connection is validated, scoped to their organization, and added to the connection pool. A background Redis pub/sub listener relays notifications to active client sockets belonging to the matching organization concurrently, achieving total data isolation.

### 4. Interactive SOC Operations Dashboard
*   **Landing Page**: Elegant introduction with animated grid effects, detailing actual project features.
*   **Dashboard View**: Dynamic cards for today's threat metrics, active WebSockets listener for real-time alert updates, and Recharts line/pie widgets.
*   **Alert Triage Drawer**: Triage incidents directly. Users can assign alerts to teammates or update status from Open to Resolving.
*   **Analytics Hub**: Deep metrics reporting, calculating Mean Time to Resolve (MTTR), false positive ratios, and listing top threat sources.
*   **Device Profiles**: Manage API credentials, heartbeat thresholds, logging latency, and local machine scanning config.

---

## 🚀 Quick Setup Reference

See the detailed guide in [setup.md](./setup.md) to set up and run the project.

### 1. Backend Setup
```bash
cd Backend
python -m venv venv
source venv/bin/activate  # Or venv\Scripts\activate on Windows
pip install -r requirements.txt
# Configure database and Redis connection in .env
uvicorn app.main:app --reload
```

### 2. Frontend Setup
```bash
cd Frontend
npm install
npm run dev
```

### 3. Agent Execution
```bash
cd agent
python -m venv venv
source venv/bin/activate  # Or venv\Scripts\activate on Windows
pip install -r requirements.txt
# Configure API keys and backend host in .env & agent_config.json
python run_mock_simulator.py
```

---

## 📚 Documentation Links
*   **Backend Architecture**: [backend.md](./backend.md)
*   **Frontend Design**: [frontend.md](./frontend.md)
*   **Detailed Setup Guide**: [setup.md](./setup.md)
*   **Cloud Deployment Guide**: [deployment.md](./deployment.md)
