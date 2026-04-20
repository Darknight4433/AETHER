import threading
import time
from ui.state import state

INTENT_MAP = {
    # System / App
    "OPEN_APP": "system",
    "KILL_PROCESS": "system",
    "SHUTDOWN": "system",
    "DEEP_WORK": "system",
    "START_DEV": "system",
    "MUTE": "system",
    "SCREENSHOT": "system",
    "TIME": "system",
    "PLANNING": "system",

    # Web
    "SEARCH": "web",
    "OPEN_URL": "web",

    # File ops
    "READ_FILE": "file",
    "WRITE_FILE": "file",
    "DELETE_FILE": "file",

    # Fallback / Thinking
    "LLM": "thinking",
    "CHAT": "thinking"
}

def trigger_intent_flash(intent_key):
    """
    Looks up the visual category for an intent, sets it in state,
    and flags intent_flash so the HUD can render the animation.
    """
    current_time = time.time()
    last_intent = state.get("last_intent_time", 0)
    
    if current_time - last_intent > 0.4:
        visual = INTENT_MAP.get(intent_key, "thinking")
        state["intent_visual"] = visual
        state["intent_flash"] = True
        state["last_intent_time"] = current_time
