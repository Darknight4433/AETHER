import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "fast_commands.json")

try:
    with open(CONFIG_PATH, "r") as f:
        COMMANDS = json.load(f)
except Exception as e:
    print(f"Error loading fast commands: {e}")
    COMMANDS = {}

def match_fast_command(text):
    text = text.lower()
    for cmd in COMMANDS.values():
        for keyword in cmd.get("keywords", []):
            if keyword in text:
                return cmd["action"]
    return None
