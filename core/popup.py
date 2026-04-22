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
_visible = False  # Track visibility ourselves since pywebview doesn't expose it

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

def _apply_native_flags():
    """Apply WS_EX_TOOLWINDOW to remove from Alt+Tab."""
    for attempt in range(20):  # Retry for ~2 seconds
        try:
            hwnd = win32gui.FindWindow(None, 'Aether Panel')
            if hwnd:
                ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
                win32gui.SetWindowLong(
                    hwnd,
                    win32con.GWL_EXSTYLE,
                    ex_style | win32con.WS_EX_TOOLWINDOW | win32con.WS_EX_TOPMOST
                )
                logger.debug(f"Native Windows flags applied on attempt {attempt+1}")
                return True
        except Exception as e:
            logger.debug(f"Native flags attempt {attempt+1} failed: {e}")
        time.sleep(0.1)
    logger.warning("Could not apply native window flags after 20 attempts")
    return False

def _position_window():
    """Align window to bottom-right corner above system tray."""
    global _window
    try:
        user32 = ctypes.windll.user32
        sw = user32.GetSystemMetrics(0)
        sh = user32.GetSystemMetrics(1)
        x = sw - 320
        y = sh - 280
        logger.info(f"Positioning popup at ({x}, {y}) on {sw}x{sh} screen")
        _window.move(x, y)
    except Exception as e:
        logger.warning(f"Failed to position popup: {e}")

def _popup_updater():
    """Background thread to update popup stats."""
    global _window
    while True:
        try:
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent
            status = state.get("status", "idle")
            app = state.get("context_label", state.get("active_app", "Desktop"))
            context_mode = state.get("context_mode", "general")
            
            js = f"if(window.updateStats) window.updateStats({cpu}, {ram}, '{status}', '{app}', '{context_mode}');"
            _window.evaluate_js(js)


            
            time.sleep(0.5)
        except Exception:
            time.sleep(1)

def _on_boot_setup():
    """Called once when pywebview starts. Initializes flags and positioning."""
    logger.info("Initializing background popup setup...")
    _apply_native_flags()
    _position_window()
    
    # 💡 WAKE UP ENGINE: Some backends need a brief show to initialize JS
    try:
        _window.show()
        time.sleep(0.2)
        _window.hide()
        logger.info("Popup engine initialized (Show/Hide cycle complete)")
    except Exception as e:
        logger.warning(f"Initial Show/Hide cycle failed: {e}")

    threading.Thread(target=_popup_updater, daemon=True).start()
    logger.info("Popup system ready and waiting in tray.")

def create_popup_window():
    """Creates the popup window and returns it. Does NOT start the event loop."""
    global _window
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    ui_path = os.path.normpath(os.path.join(base_dir, '..', 'ui', 'popup.html'))
    
    logger.info(f"Creating popup window from: {ui_path}")

    _window = webview.create_window(
        'Aether Panel',
        ui_path,
        width=300,
        height=220,
        frameless=True,
        easy_drag=True,
        on_top=True,
        transparent=True,
        hidden=True  # START HIDDEN
    )
    
    _window.js_api = PopupApi(_window)
    return _window

def start_popup_logic(window):
    """Starts the threads for a pre-created popup window."""
    _on_boot_setup()


def toggle_popup():

    """Toggle popup visibility. Called from tray icon or hotkey."""
    global _window, _visible
    
    if not _window:
        logger.error("toggle_popup called but _window is None!")
        return

    logger.info(f"Toggle request: Current Visibility={_visible}")
    
    try:
        if _visible:
            _window.hide()
            _visible = False
            logger.info("Action: HIDDEN")
        else:
            # Force to front
            _window.show()
            _window.restore()
            _window.on_top = True
            _position_window()
            _visible = True
            logger.info("Action: SHOWN")
    except Exception as e:
        logger.error(f"Critical toggle failure: {e}")
        # Attempt emergency recovery
        try:
            _window.show()
            _visible = True
        except: pass

