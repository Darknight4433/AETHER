BLOCKED = ["delete", "format", "shutdown", "rm ", "drop", "kill", "wipe", "format c:"]

def is_safe(text):
    """Returns True if the text does not contain any restricted keywords."""
    return not any(b in text.lower() for b in BLOCKED)
