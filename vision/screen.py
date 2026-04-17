import pyautogui
import os

def capture_screen():
    temp_path = "temp_screen.png"
    screenshot = pyautogui.screenshot()
    screenshot.save(temp_path)
    return temp_path
