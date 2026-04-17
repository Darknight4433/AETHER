from core.memory_engine import load_memory
import datetime

def detect_habits():
    data = load_memory()
    actions = data.get("actions", [])

    hour_map = {}

    for a in actions:
        try:
            hour = datetime.datetime.fromtimestamp(a["timestamp"]).hour
            key = (a["action"], hour)
            hour_map[key] = hour_map.get(key, 0) + 1
        except Exception:
            continue

    habits = {}
    for (action, hour), count in hour_map.items():
        if count >= 3:  # threshold
            habits.setdefault(hour, []).append(action)

    return habits
