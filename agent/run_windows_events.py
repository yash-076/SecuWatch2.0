import threading
import time
import requests
import sys
from datetime import datetime, timezone

from config import DEVICE_ID, API_KEY, WINDOWS_EVENT_CHANNELS
from core import (
    agent_state,
    check_log_for_threat,
    is_severity_met,
    post_with_retry,
    enrich_log_message,
    start_heartbeat_thread,
)

# Standard imports for Windows Event Logs
try:
    import win32evtlog
    import win32evtlogutil
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

if not HAS_WIN32:
    print("[ERROR] 'pywin32' is not installed. To run this agent, run: pip install pywin32")
    sys.exit(1)

EVENT_TYPE_MAP = {
    win32evtlog.EVENTLOG_ERROR_TYPE: "ERROR",
    win32evtlog.EVENTLOG_WARNING_TYPE: "WARNING",
    win32evtlog.EVENTLOG_INFORMATION_TYPE: "INFO",
    win32evtlog.EVENTLOG_AUDIT_SUCCESS: "SUCCESS",
    win32evtlog.EVENTLOG_AUDIT_FAILURE: "FAILURE",
}


def get_newest_record_number(channel: str) -> int:
    try:
        hand = win32evtlog.OpenEventLog(None, channel)
        flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
        events = win32evtlog.ReadEventLog(hand, flags, 0)
        if events:
            return events[0].RecordNumber
    except Exception:
        pass
    return 0


def read_new_windows_events(channel: str, last_record_num: int) -> list:
    events_list = []
    hand = None
    try:
        hand = win32evtlog.OpenEventLog(None, channel)
        num_records = win32evtlog.GetNumberOfEventLogRecords(hand)
        if num_records == 0:
            return []

        try:
            flags = win32evtlog.EVENTLOG_FORWARDS_READ | win32evtlog.EVENTLOG_SEEK_READ
            offset = last_record_num + 1
            events = win32evtlog.ReadEventLog(hand, flags, offset)
            while events:
                for event in events:
                    if event.RecordNumber > last_record_num:
                        events_list.append(event)
                flags = win32evtlog.EVENTLOG_FORWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
                events = win32evtlog.ReadEventLog(hand, flags, 0)
        except Exception:
            flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
            events = win32evtlog.ReadEventLog(hand, flags, 0)
            while events:
                stop = False
                for event in events:
                    if event.RecordNumber > last_record_num:
                        events_list.append(event)
                    else:
                        stop = True
                        break
                if stop:
                    break
                events = win32evtlog.ReadEventLog(hand, flags, 0)
            events_list.reverse()
    except Exception as e:
        err_msg = str(e)
        is_permission_error = False
        if hasattr(e, 'winerror'):
            if e.winerror in [5, 1314, 1317]:
                is_permission_error = True
        elif any(k in err_msg.lower() for k in ["access is denied", "privilege is not held", "permission denied"]):
            is_permission_error = True
            
        if is_permission_error:
            raise PermissionError("Access denied")
        else:
            print(f"[WIN-LOG] Error reading channel '{channel}': {e}")
    finally:
        if hand:
            win32evtlog.CloseEventLog(hand)
            
    return events_list


def format_event_message(event, channel: str) -> str:
    try:
        desc = win32evtlogutil.SafeFormatMessage(event, channel)
    except Exception:
        desc = None
    
    if not desc and event.StringInserts:
        desc = " | ".join(event.StringInserts)
    if not desc:
        desc = f"Windows Event from source '{event.SourceName}'"
    return desc


def win_event_monitoring_loop(stop_event: threading.Event) -> None:
    last_records = {}
    for channel in WINDOWS_EVENT_CHANNELS:
        last_num = get_newest_record_number(channel)
        last_records[channel] = last_num
        print(f"[WIN-LOG] Initialized '{channel}' channel cursor at event record #{last_num}")
        
    print(f"[WIN-LOG] Monitoring Windows Event channels: {WINDOWS_EVENT_CHANNELS}")
    permission_warned = set()
    
    with requests.Session() as session:
        while not stop_event.is_set():
            for channel in WINDOWS_EVENT_CHANNELS:
                try:
                    events = read_new_windows_events(channel, last_records[channel])
                    for event in events:
                        last_records[channel] = max(last_records[channel], event.RecordNumber)
                        
                        raw_msg = format_event_message(event, channel)
                        level = EVENT_TYPE_MAP.get(event.EventType, "INFO")
                        event_id = str(event.EventID & 0xFFFF)
                        
                        enriched = enrich_log_message(
                            source=f"WinEvent:{channel}",
                            level=level,
                            raw_message=raw_msg,
                            event_id=event_id
                        )
                        
                        payload = {
                            "device_id": DEVICE_ID,
                            "api_key": API_KEY,
                            "message": enriched,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                        print(f"Sent log (WinEvent:{channel}) | message=\"{enriched[:120]}...\"")
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
                                        "description": f"[LOCAL DETECT] Local agent threat signature '{alert_type}' matches Event ID {event_id}: {raw_msg}",
                                    }
                                    post_with_retry(session, "/devices/alerts", alert_payload, "alert")
                                    
                except PermissionError:
                    if channel not in permission_warned:
                        print(f"[WIN-LOG] [WARNING] Access denied to Windows Event Log '{channel}' channel. Run agent as Administrator to read it.")
                        permission_warned.add(channel)
                except Exception as e:
                    print(f"[WIN-LOG] Error polling '{channel}': {e}")
                    
            if stop_event.wait(2.0):
                break


def main() -> None:
    stop_event = threading.Event()
    
    print("[WIN-AGENT] Starting SecuWatch Windows Event Log Agent...")
    heartbeat_thread = start_heartbeat_thread(stop_event)
    
    win_thread = threading.Thread(target=win_event_monitoring_loop, args=(stop_event,), daemon=True)
    win_thread.start()

    print("Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping Windows agent...")
        stop_event.set()
        heartbeat_thread.join(timeout=2)
        win_thread.join(timeout=2)
        print("Windows agent stopped.")


if __name__ == "__main__":
    main()
