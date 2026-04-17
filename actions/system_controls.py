import pyautogui
import os

def screenshot():
    os.makedirs("data", exist_ok=True)
    path = "data/screen_capture.png"
    pyautogui.screenshot(path)
    return "📸 Screenshot saved"

def volume_up():
    pyautogui.press("volumeup")
    return "🔊 Volume increased"
