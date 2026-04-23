"""
Aether Neural Dashboard — Fullscreen system overview using pywebview.
Replaces the FastAPI-served dashboard with a native, port-less window.
"""

import os
import threading
import time
import webview
import psutil
from loguru import logger
from core.paths import resource_path
from ui.state import state

_window = None

class DashboardApi:
    def __init__(self, window=None):
        self.window = window

    def toggle_autonomy(self):
        state["autonomy"] = not state.get("autonomy", False)
        logger.info(f"Dashboard: Autonomy toggled to {state['autonomy']}")
        return state["autonomy"]

    def toggle_dnd(self):
        state["dnd"] = not state.get("dnd", False)
        logger.info(f"Dashboard: DND toggled to {state['dnd']}")
        return state["dnd"]

    def get_state(self):
        return state


def _dashboard_updater():
    """Background thread to push state to the dashboard UI."""
    global _window
    while True:
        if _window:
            try:
                # Prepare state for JS (handling non-serializable objects if any)
                # We'll just pass the whole state as a JS object
                import json
                
                # Update transient stats
                state["cpu"] = psutil.cpu_percent()
                state["ram"] = psutil.virtual_memory().percent
                
                # Push to UI
                js_state = json.dumps(state)
                _window.evaluate_js(f"if(window.updateDashboard) window.updateDashboard({js_state});")
            except Exception as e:
                logger.error(f"Dashboard Update Error: {e}")
        
        time.sleep(1)


def create_dashboard_window():
    global _window
    
    ui_path = resource_path("ui", "index.html")
    if not os.path.exists(ui_path):
        logger.error(f"Dashboard HTML not found: {ui_path}")
        return None

    api = DashboardApi()
    _window = webview.create_window(
        'Aether Neural Dashboard',
        ui_path,
        js_api=api,
        width=1200,
        height=800,
        resizable=True,
        min_size=(800, 600)
    )
    api.window = _window
    
    # Start updater thread
    threading.Thread(target=_dashboard_updater, daemon=True).start()
    
    return _window
