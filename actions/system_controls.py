import pyautogui

from core.paths import data_path


def screenshot():
    path = data_path("screen_capture.png")
    pyautogui.screenshot(path)
    return "Screenshot saved"


def volume_up():
    pyautogui.press("volumeup")
    return "Volume increased"
