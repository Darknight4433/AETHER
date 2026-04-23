import datetime

import pyautogui
from loguru import logger

from core.paths import data_path


def mute():
    logger.info("Fast Path: Muting system volume.")
    pyautogui.press("volumemute")
    return "Audio muted."


def screenshot():
    logger.info("Fast Path: Capturing screenshot...")
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    pyautogui.screenshot(data_path(f"shot_{stamp}.png"))
    return "Screenshot captured."


def get_time():
    current_time = datetime.datetime.now().strftime("%I:%M %p")
    logger.info(f"Fast Path: Time is {current_time}.")
    return f"It is currently {current_time}."
