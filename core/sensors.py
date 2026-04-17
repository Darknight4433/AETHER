import datetime
from vision.screen import capture_screen
from vision.ocr import extract_text

def get_time_block():
    hour = datetime.datetime.now().hour
    if 6 <= hour < 12: return "morning"
    if 12 <= hour < 18: return "afternoon"
    if 18 <= hour < 23: return "evening"
    return "night"

def screen_text_sample():
    try:
        path = capture_screen()
        text = extract_text(path)
        return text[:400]
    except Exception:
        return ""
