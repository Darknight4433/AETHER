import re

def detect_intent(text):
    text = text.lower()

    if any(k in text for k in ["open", "launch", "start"]):
        return "OPEN_APP"

    if any(k in text for k in ["search", "google", "look up"]):
        return "SEARCH_WEB"

    if "play" in text:
        return "PLAY_SONG"

    if "time" in text or "what time" in text:
        return "GET_TIME"

    if "screen" in text and any(k in text for k in ["what", "read", "show", "see", "error"]):
        return "READ_SCREEN"

    if "click" in text:
        return "CLICK_UI"

    return "CHAT"
