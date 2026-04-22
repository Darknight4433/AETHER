import time
import threading
import pygetwindow as gw
from loguru import logger
from ui.state import state

def app_tracker_loop():
    """Background thread that tracks the currently active window/app."""
    logger.info("Application Tracker started.")
    last_app = ""
    
    while True:
        try:
            window = gw.getActiveWindow()
            if window:
                title = window.title
                # Simple extraction of app name from title (e.g., "Main.py - Visual Studio Code" -> "Visual Studio Code")
                if " - " in title:
                    app_name = title.split(" - ")[-1]
                else:
                    app_name = title
                
                if app_name != last_app:
                    state["active_app"] = app_name
                    last_app = app_name
                    logger.debug(f"Active App: {app_name}")
            else:
                if last_app != "Desktop":
                    state["active_app"] = "Desktop"
                    last_app = "Desktop"
        except Exception as e:
            pass
            
        time.sleep(1.0)

def start_app_tracker():
    threading.Thread(target=app_tracker_loop, daemon=True).start()
