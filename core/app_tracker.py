"""
Aether Process Anchor — Detects the currently active application using native Win32 APIs.
This provides the process-level identification (chrome.exe, code.exe, etc.)
that powers the Context Engine.
"""

import time
import threading
import win32gui
import win32process
import psutil
from loguru import logger
from ui.state import state


def get_active_app():
    """Get the executable name of the currently focused window."""
    try:
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return "Desktop"

        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        process = psutil.Process(pid)
        return process.name()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return "unknown"
    except Exception:
        return "unknown"


def get_active_window_title():
    """Get the title of the currently focused window."""
    try:
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return ""
        return win32gui.GetWindowText(hwnd)
    except Exception:
        return ""


def app_tracker_loop():
    """Background thread that tracks the currently active window/app."""
    logger.info("Process Anchor started.")
    last_app = ""
    last_title = ""

    while True:
        try:
            app = get_active_app()
            title = get_active_window_title()

            if app != last_app:
                state["active_app"] = app
                state["active_window_title"] = title
                last_app = app
                last_title = title
                logger.debug(f"Active App: {app} | {title}")

                # Notify the context engine of the app change
                try:
                    from core.context_engine import on_app_changed
                    on_app_changed(app, title)
                except ImportError:
                    pass

            elif title != last_title:
                state["active_window_title"] = title
                last_title = title

        except Exception:
            pass

        time.sleep(1.0)


def start_app_tracker():
    """Start the background app tracking thread."""
    threading.Thread(target=app_tracker_loop, daemon=True).start()
