"""HUD overlay for Aether using pywebview.

This provides a premium animated HUD experience replacing the simplistic orb.
"""

import os
import threading
import time
import json
import psutil

import webview
from loguru import logger
from core.paths import resource_path
from ui.state import state


def _get_hud_path():
    return resource_path("ui", "hud.html")


def get_system_stats():
    return psutil.cpu_percent(), psutil.virtual_memory().percent


class HUDApi:
    def __init__(self):
        self.window = None

    def start_drag(self):
        if self.window is None:
            return

        try:
            if hasattr(self.window, 'drag_move'):
                self.window.drag_move()
            elif hasattr(self.window, 'drag'):
                self.window.drag()
            else:
                logger.warning('HUD drag is not supported by this webview backend.')
        except Exception as e:
            logger.warning(f"HUD drag start failed: {e}")

    def start_resize(self):
        if self.window is None:
            return
        try:
            self.window.resize(self.window.width + 20, self.window.height + 20)
        except Exception:
            pass

    def set_clickthrough(self, enabled):
        if self.window is None:
            return
        try:
            import win32gui, win32con
            # Avoid duplicate calls
            if getattr(self, '_clickthrough', None) == enabled:
                return
                
            hwnd = self.window.gui.window
            style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)

            if enabled:
                win32gui.SetWindowLong(
                    hwnd,
                    win32con.GWL_EXSTYLE,
                    style | win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT
                )
            else:
                win32gui.SetWindowLong(
                    hwnd,
                    win32con.GWL_EXSTYLE,
                    style & ~win32con.WS_EX_TRANSPARENT
                )
            self._clickthrough = enabled
        except Exception:
            pass


def _hud_updater(window, api):
    logger.info("HUD Updater thread started.")
    ctx = {"last_user": "", "last_ai": ""}
    while True:
        try:
            current_status = state.get('status', 'idle')
            audio_level = float(state.get('audio_level', 0.0) or 0.0)
            audio_source = state.get('audio_source', 'mic')
            
            user_text = state.get('user_text', '')
            assistant_text = state.get('assistant_text', '')
            
            cpu, ram = get_system_stats()
            
            send_text = ""
            if user_text != ctx["last_user"]:
                ctx["last_user"] = user_text
                send_text = user_text
                
            send_reply = ""
            if assistant_text != ctx["last_ai"]:
                ctx["last_ai"] = assistant_text
                send_reply = assistant_text
                
                # Extract emotion
                from core.emotion import detect_emotion
                new_emotion = detect_emotion(assistant_text)
                
                # Cooldown to avoid jittery mood changes
                last_emo_time = state.get("last_emotion_time", 0)
                if time.time() - last_emo_time > 1.5:
                    state["emotion"] = new_emotion
                    state["last_emotion_time"] = time.time()
                    
                emotion = state.get("emotion", "calm")
                try:
                    if window is not None:
                        window.evaluate_js(
                            "if(!window.currentEmotion) window.currentEmotion='calm'; "
                            f"window.updateEmotion({json.dumps(emotion)});"
                        )
                except Exception:
                    pass

            if window is not None:
                wave = state.get('waveform', [0]*64)
                # Update HUD stats and transcript
                js = (
                    "window.updateHUD("
                    f"{json.dumps(current_status)}, {audio_level:.2f}, "
                    f"{json.dumps(audio_source)}, {cpu}, {ram}, "
                    f"{json.dumps(send_text)}, {json.dumps(send_reply)})"
                )
                window.evaluate_js(js)
                window.evaluate_js(f"window.updateWave({json.dumps(wave)})")
                window.evaluate_js(f"window.currentSource={json.dumps(audio_source)}")

                if state.get("intent_flash"):
                    visual = state.get("intent_visual", "thinking")
                    window.evaluate_js(
                        f"if(window.triggerIntent) window.triggerIntent({json.dumps(visual)});"
                    )
                    state["intent_flash"] = False
                    
            # Heartbeat update
            if api:
                api.last_heartbeat = time.time()
                
            # 🧠 FINAL SYSTEM BEHAVIOR: Automatic Visibility Logic
            if current_status == "idle":
                if getattr(api, '_visible', True):
                    window.hide()
                    api._visible = False
            else:
                if not getattr(api, '_visible', False):
                    window.show()
                    api._visible = True

            # Click-through management
            if api and current_status != "idle":
                if current_status == "speaking":
                    api.set_clickthrough(True) # Can click through while it speaks
                else:
                    api.set_clickthrough(False)


        except Exception as e:
            logger.exception(f"HUD Updater Error: {e}")

        time.sleep(0.1)

        time.sleep(0.1)


def create_hud_window():
    """Creates the HUD window and returns it. Does NOT start the event loop."""
    hud_path = _get_hud_path()
    if not os.path.exists(hud_path):
        logger.error(f"HUD HTML not found: {hud_path}")
        return None, None


    api = HUDApi()
    window = webview.create_window(
        'Aether HUD',
        hud_path,
        js_api=api,
        frameless=True,
        transparent=True,
        on_top=True,
        width=500,
        height=350,
        x=1400,
        y=40,
        resizable=False,
        hidden=True # Start hidden!
    )

    api.window = window
    return window, api

def start_hud_logic(window, api):
    """Starts the threads for a pre-created HUD window."""
    threading.Thread(target=_hud_updater, args=(window, api), daemon=True).start()
    
    def monitor_hud():
        while True:
            if hasattr(api, 'last_heartbeat'):
                if time.time() - api.last_heartbeat > 10:
                    logger.warning("HUD Window Heartbeat Lost!")
            time.sleep(5)
    threading.Thread(target=monitor_hud, daemon=True).start()
    logger.success("HUD background logic initialized.")
