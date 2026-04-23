import ctypes
import json
import os
import threading
import time
from ctypes import wintypes

import psutil
import webview
import win32con
import win32gui
from loguru import logger

from core.paths import resource_path
from core.paths import data_path
from core.ui_theme import (
    get_popup_settings,
    reset_popup_settings,
    update_popup_settings,
)
from ui.state import state


POPUP_WIDTH = 344
POPUP_HEIGHT = 352
POPUP_MARGIN = 12
TOGGLE_DEBOUNCE_SECONDS = 0.22
SHOW_GRACE_PERIOD_SECONDS = 0.8

_window = None
_visible = False
_hwnd = None
_last_toggle_at = 0.0
_last_shown_at = 0.0


def _build_payload():
    cpu = round(psutil.cpu_percent(interval=None), 1)
    vm = psutil.virtual_memory()
    return {
        "cpu": cpu,
        "ram_percent": round(vm.percent, 1),
        "ram_used_gb": round((vm.total - vm.available) / (1024 ** 3), 1),
        "status": state.get("status", "idle"),
        "app": state.get("context_label", state.get("active_app", "Desktop")),
        "window_title": state.get("active_window_title", ""),
        "context_mode": state.get("context_mode", "general"),
        "autonomy": state.get("autonomy", False),
        "dnd": state.get("dnd", False),
        "active": state.get("active", False),
        "latency": state.get("latency", "0.00s"),
        "last_action": state.get("last_action", "Waiting for input"),
        "settings": get_popup_settings(),
    }


def _push_popup_state():
    if _window is None:
        return
    payload = _build_payload()
    _window.evaluate_js(
        f"if(window.updateStats) window.updateStats({json.dumps(payload)});"
    )

    suggestion = state.get("suggestion", "")
    if suggestion:
        _window.evaluate_js(
            f"if(window.showSuggestion) window.showSuggestion({json.dumps(suggestion)});"
        )
    else:
        _window.evaluate_js("if(window.hideSuggestion) window.hideSuggestion();")


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

    def accept_suggestion(self):
        action = state.get("suggestion_action", "")
        if action:
            logger.info(f"User accepted suggestion: {action}")
            try:
                from core.router import route
                route(action.upper())
            except Exception as e:
                logger.error(f"Suggestion execution failed: {e}")
            state["suggestion"] = ""
            state["suggestion_action"] = ""
            state["suggestion_confidence"] = 0

    def toggle_autonomy(self):
        state["autonomy"] = not state.get("autonomy", False)
        logger.info(f"Autonomy toggled: {state['autonomy']}")
        return state["autonomy"]

    def toggle_dnd(self):
        state["dnd"] = not state.get("dnd", False)
        logger.info(f"DND toggled: {state['dnd']}")
        return state["dnd"]

    def get_popup_settings(self):
        return get_popup_settings()

    def update_popup_settings(self, settings):
        updated = update_popup_settings(settings)
        logger.info("Popup settings updated.")
        return updated

    def reset_popup_settings(self):
        updated = reset_popup_settings()
        logger.info("Popup settings reset to defaults.")
        return updated

    def open_logs(self):
        log_path = data_path("aether.log")
        try:
            if not os.path.exists(log_path):
                with open(log_path, "a", encoding="utf-8"):
                    pass
            os.startfile(log_path)
            return True
        except Exception as e:
            logger.error(f"Failed to open logs: {e}")
            return False


def _find_popup_hwnd():
    global _hwnd
    if _hwnd and win32gui.IsWindow(_hwnd):
        return _hwnd

    try:
        hwnd = win32gui.FindWindow(None, "Aether Panel")
        if hwnd:
            _hwnd = hwnd
            return hwnd
    except Exception:
        pass
    return None


def _apply_native_flags():
    """Remove the popup from Alt+Tab and keep it topmost."""
    for attempt in range(20):
        try:
            hwnd = _find_popup_hwnd()
            if hwnd:
                ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
                win32gui.SetWindowLong(
                    hwnd,
                    win32con.GWL_EXSTYLE,
                    ex_style | win32con.WS_EX_TOOLWINDOW | win32con.WS_EX_TOPMOST,
                )
                logger.debug(f"Native popup flags applied on attempt {attempt + 1}")
                return True
        except Exception as e:
            logger.debug(f"Native flags attempt {attempt + 1} failed: {e}")
        time.sleep(0.1)

    logger.warning("Could not apply native popup flags.")
    return False


def _get_work_area():
    rect = wintypes.RECT()
    SPI_GETWORKAREA = 0x0030
    ctypes.windll.user32.SystemParametersInfoW(
        SPI_GETWORKAREA, 0, ctypes.byref(rect), 0
    )
    return rect


def _position_window():
    """Anchor the popup to the bottom-right work area above the taskbar."""
    global _window
    if _window is None:
        return

    try:
        rect = _get_work_area()
        x = rect.right - POPUP_WIDTH - POPUP_MARGIN
        y = rect.bottom - POPUP_HEIGHT - POPUP_MARGIN
        _window.move(x, y)
        logger.debug(f"Popup positioned at ({x}, {y}) within work area.")
    except Exception as e:
        logger.warning(f"Failed to position popup: {e}")


def _show_popup():
    global _visible, _last_shown_at
    if _window is None:
        return

    _last_shown_at = time.time()
    _apply_native_flags()
    _window.show()
    try:
        _window.restore()
    except Exception:
        pass

    _position_window()
    try:
        _window.on_top = True
    except Exception:
        pass

    try:
        hwnd = _find_popup_hwnd()
        if hwnd:
            win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
            win32gui.SetForegroundWindow(hwnd)
    except Exception:
        pass

    try:
        _push_popup_state()
        _window.evaluate_js(
            "if(window.playEntryAnimation) window.playEntryAnimation();"
        )
    except Exception:
        pass

    _visible = True


def _hide_popup():
    global _visible
    if _window is None:
        return

    try:
        _window.hide()
    except Exception:
        pass
    _visible = False


def _popup_updater():
    while True:
        try:
            if _window is None:
                time.sleep(1)
                continue

            if _visible:
                _push_popup_state()
                time.sleep(0.8)
            else:
                time.sleep(1.2)
        except Exception:
            time.sleep(1)


def _focus_watchdog():
    """Hide the popup when focus moves away, mimicking a tray flyout."""
    global _visible
    while True:
        try:
            if _visible:
                if time.time() - _last_shown_at < SHOW_GRACE_PERIOD_SECONDS:
                    time.sleep(0.05)
                    continue
                hwnd = _find_popup_hwnd()
                if hwnd:
                    foreground = win32gui.GetForegroundWindow()
                    if foreground and foreground != hwnd:
                        _hide_popup()
        except Exception:
            pass
        time.sleep(0.15)


def _on_boot_setup():
    logger.info("Initializing popup flyout...")
    threading.Thread(target=_popup_updater, daemon=True).start()
    threading.Thread(target=_focus_watchdog, daemon=True).start()
    logger.info("Popup engine initialized.")
    logger.info("Popup flyout ready in tray.")


def create_popup_window():
    global _window

    ui_path = resource_path("ui", "popup.html")

    logger.info(f"Creating popup window from: {ui_path}")

    api = PopupApi()
    _window = webview.create_window(
        "Aether Panel",
        ui_path,
        js_api=api,
        width=POPUP_WIDTH,
        height=POPUP_HEIGHT,
        frameless=True,
        easy_drag=True,
        on_top=True,
        transparent=True,
        hidden=True,
    )
    api.window = _window
    return _window


def start_popup_logic(window):
    _on_boot_setup()


def show_popup():
    global _last_toggle_at
    _last_toggle_at = time.time()
    _show_popup()


def toggle_popup():
    """Toggle popup visibility from tray or hotkey without duplicate flashes."""
    global _last_toggle_at

    if not _window:
        logger.error("toggle_popup called but popup window is not ready.")
        return

    now = time.time()
    if now - _last_toggle_at < TOGGLE_DEBOUNCE_SECONDS:
        return
    _last_toggle_at = now

    try:
        if _visible:
            _hide_popup()
            logger.info("Popup hidden.")
        else:
            _show_popup()
            logger.info("Popup shown.")
    except Exception as e:
        logger.error(f"Critical popup toggle failure: {e}")
        try:
            _show_popup()
        except Exception:
            pass
