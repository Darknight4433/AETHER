import os

BASE_DIR = os.path.expanduser("~/AETHER_SANDBOX")
ALLOWED_ACTIONS = {
    "CREATE_FILE",
    "READ_FILE",
    "MOVE_FILE",
    "OPEN_APP",
    "SEARCH_WEB",
    "SET_VOLUME",
    "TAKE_SCREENSHOT"
}
BLOCKED_PATHS = ["C:\\Windows", "/etc", "/System"]

def ensure_base():
    os.makedirs(BASE_DIR, exist_ok=True)

def is_action_allowed(action):
    return action in ALLOWED_ACTIONS

def is_path_safe(path):
    abs_path = os.path.abspath(path)
    if any(abs_path.startswith(p) for p in BLOCKED_PATHS):
        return False
    return abs_path.startswith(os.path.abspath(BASE_DIR))
