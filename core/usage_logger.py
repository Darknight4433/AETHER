"""
Aether Usage Logger — Persistent action tracking layer.

Every meaningful action Aether performs or observes is recorded here
with full temporal context. This feeds the Learning Engine.
"""

import os
import json
import time
from datetime import datetime
from loguru import logger

LOG_FILE = os.path.join("data", "usage.json")
MAX_ENTRIES = 5000  # Rolling window to prevent unbounded growth


def _ensure_log():
    """Ensure the log file and directory exist."""
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            json.dump([], f)


def log_action(action, app="unknown", metadata=None):
    """
    Log a user or system action with full temporal context.
    
    Args:
        action: What happened (e.g., "open_browser", "search_web", "mute")
        app: Which app was active (e.g., "chrome.exe", "code.exe")
        metadata: Optional dict with extra context
    """
    _ensure_log()

    now = datetime.now()
    entry = {
        "action": action,
        "app": app,
        "timestamp": now.isoformat(),
        "hour": now.hour,
        "minute": now.minute,
        "weekday": now.strftime("%A"),
        "day_type": "weekend" if now.weekday() >= 5 else "weekday",
    }

    if metadata:
        entry["meta"] = metadata

    try:
        with open(LOG_FILE, "r") as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        data = []

    data.append(entry)

    # Trim to rolling window
    if len(data) > MAX_ENTRIES:
        data = data[-MAX_ENTRIES:]

    try:
        with open(LOG_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Usage Logger write failed: {e}")

    logger.debug(f"Logged: {action} | {app} | {now.strftime('%H:%M %A')}")


def get_log():
    """Return the full usage log."""
    _ensure_log()
    try:
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def get_recent(n=50):
    """Return the most recent n log entries."""
    data = get_log()
    return data[-n:]
