# SecuWatch 2.0 Lightweight Agent (MVP)

This script simulates a machine that continuously sends:
- Heartbeats to `/heartbeat` every 30 seconds
- Logs to `/logs` every 5-10 seconds

## 1) Configure

Edit `config.py` or use environment variables:

- `SECUWATCH_BACKEND_URL` (default: `http://localhost:8000`)
- `SECUWATCH_DEVICE_ID` (default: `1`)
- `SECUWATCH_API_KEY` (required for real auth)

## 2) Install dependencies

```bash
pip install -r requirements.txt
```

## 3) Run

```bash
python agent.py
```

## Notes

- This is intentionally simple (MVP): no OS log collection, no daemonization.
- Retry behavior is built in for failed requests.

## Future Design Considerations

- Read real system logs from OS/application sources
- Run as a background service/daemon
- Auto-register devices and rotate API keys
