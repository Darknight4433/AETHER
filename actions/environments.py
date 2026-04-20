import os
import pyautogui
from loguru import logger

def deep_work():
    logger.info("⚡ Fast Path: Initializing Deep Work Environment...")
    os.system("taskkill /IM discord.exe /F 2>nul")
    os.system("taskkill /IM whatsapp.exe /F 2>nul")
    # Soften audio
    for _ in range(15):
        pyautogui.press("volumedown")
    # Open key references
    os.system("start chrome https://github.com/Darknight4433")
    return "Focus mode activated. Distractions killed."

def start_dev():
    logger.info("⚡ Fast Path: Booting Developer Environment...")
    project_path = "C:\\Users\\Vaishnavi L\\OneDrive\\Desktop\\Aether"
    os.system(f"start code \"{project_path}\"")
    return "Dev environment ready."
