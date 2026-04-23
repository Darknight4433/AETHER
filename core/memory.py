import json
import os
from loguru import logger
from core.paths import data_path

FILE = data_path("memory.json")

def save(user, reply):
    try:
        with open(FILE, "r") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []

    data.append({"user": user, "reply": reply})
    
    # Keep last 20 exchanges to avoid overwhelming context
    with open(FILE, "w") as f:
        json.dump(data[-20:], f, indent=4)

def get_context():
    try:
        with open(FILE, "r") as f:
            data = json.load(f)
        return "\n".join([f"User: {d['user']}\nAether: {d['reply']}" for d in data])
    except (FileNotFoundError, json.JSONDecodeError):
        return ""
        
def clear_memory():
    if os.path.exists(FILE):
        os.remove(FILE)
