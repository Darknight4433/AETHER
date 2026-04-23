import json
import os
import time
from loguru import logger
from core.paths import data_path

FILE = data_path("memory_state.json")

def load_memory():
    try:
        if os.path.exists(FILE):
            with open(FILE, "r") as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load memory state: {e}")
        
    return {"actions": [], "habits": {}, "preferences": {}}

def save_memory(data):
    with open(FILE, "w") as f:
        json.dump(data, f, indent=2)

def log_action(action, metadata):
    data = load_memory()
    entry = {
        "action": action,
        "metadata": metadata,
        "timestamp": time.time()
    }
    data.setdefault("actions", []).append(entry)
    save_memory(data)
