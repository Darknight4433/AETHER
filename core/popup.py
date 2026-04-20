import os
import threading
import time
import webview
import psutil
import ctypes
import win32gui
import win32con
from loguru import logger
from ui.state import state

# Shared popup window instance
_window = None

class PopupApi:
    def __init__(self, window=None):
        self.window = window

    def start_drag(self):
        if self.window:
            self.window.drag_move()

    def start_aether(self):
        logger.info("Starting Aether session from popup")
        state["active"] = True
        state["force_listen"] = True

    def stop_aether(self):
        logger.info("Stopping Aether session from popup")
        state["status"] = "idle"
        state["active"] = False

def _apply_native_flags(window):
    """Apply WS_EX_TOOLWINDOW to remove from Alt+Tab and fix to topmost."""
    try:
        # Find window handle
        hwnd = win32gui.FindWindow(None, 'Aether Panel')
        if not hwnd:
            return
            
        ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        win32gui.SetWindowLong(
            hwnd,
            win32con.GWL_EXSTYLE,
            ex_style | win32con.WS_EX_TOOLWINDOW | win32con.WS_EX_TOPMOST
        )
        logger.debug("Native Windows flags applied (Hidden from Alt+Tab)")
    except Exception as e:
        logger.warning(f"Failed to apply native window flags: {e}")

def _position_window(window):
    """Align window to bottom-right corner above system tray."""
    try:
        user32 = ctypes.windll.user32
        sw = user32.GetSystemMetrics(0)
        sh = user32.GetSystemMetrics(1)
        # Position 320px from right, 250px from bottom
        window.move(sw - 320, sh - 280)
    except Exception:
        pass

def _popup_updater(window):
    """Background thread to update popup stats."""
    while True:
        try:
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent
            status = state.get("status", "idle")
            
            js = f"if(window.updateStats) window.updateStats({cpu}, {ram}, '{status}');"
            window.evaluate_js(js)
            
            time.sleep(0.5)
        except Exception:
            break

def on_focus_lost():
    """Auto-hide when user clicks away."""
    global _window
    if _window:
        logger.debug("Popup focus lost, auto-hiding.")
        _window.hide()

def init_popup():
    """Initialize the hidden singleton window on start."""
    global _window
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    ui_path = os.path.normpath(os.path.join(base_dir, '..', 'ui', 'popup.html'))

    _window = webview.create_window(
        'Aether Panel',
        ui_path,
        width=300,
        height=220,
        frameless=True,
        easy_drag=True,
        on_top=True,
        transparent=True,
        hidden=True # Start hidden
    )
    
    _window.js_api = PopupApi(_window)
    
    def setup():
        _apply_native_flags(_window)
        _position_window(_window)
        threading.Thread(target=_popup_updater, args=(_window,), daemon=True).start()

    _window.events.shown += setup
    
    # pywebview doesn't have a direct blur event easily exposed via window.events
    # we'll use evaluate_js with a callback or window.hide() from the tray toggle.
    
    webview.start(gui='edgechromium')

def toggle_popup():
    """Toggle visibility from tray icon."""
    global _window
    if not _window:
        logger.error("Popup window not initialized!")
        return

    # Check visible state - pywebview doesn't expose .visible, 
    # we track it or just show it (on_top handles the rest)
    try:
        # Simple toggle - if it fails, it means it's likely hidden or needs focus
        _window.show()
        _window.restore() 
    except Exception:
        pass
