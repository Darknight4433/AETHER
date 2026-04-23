import os
import sys
import shutil

import time
import threading
from dotenv import load_dotenv
from loguru import logger
from core.paths import data_path, get_install_root

# Ensure a stable working directory in both source and bundled builds.
os.chdir(get_install_root())

def _safe_console_sink(message):
    try:
        sys.stderr.buffer.write(str(message).encode("utf-8", errors="backslashreplace"))
    except Exception:
        pass


def _notify_user(title, message):
    if sys.platform == "win32":
        try:
            ctypes = __import__("ctypes")
            ctypes.windll.user32.MessageBoxW(0, message, title, 0x40)
            return
        except Exception:
            pass
    logger.error(f"{title}: {message}")

# Establish permanent trace log
if sys.platform == "win32":
    try:
        import sys
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except Exception:
        pass

logger.remove()
logger.add(_safe_console_sink, level="INFO")
logger.add(data_path("aether.log"), rotation="10 MB", level="INFO", encoding="utf-8")

# Import Core Systems
from core.vision import VisionSystem
from core.audio_io import AudioInterface
from core.llm import Brain
from core.tts import SpeechEngine
from core.intent import detect_intent
from core.router import route
from core.planner import create_plan
from core.agent import execute_plan
from core.safety_guard import authorize, is_safe
from core.autonomy import autonomy_loop
from core.hotkey import start_hotkey_listener
from core.intent_visuals import trigger_intent_flash
from ui.state import state, update_log
from core.tray import run_tray
import socket

# Load Environment Variables
load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
AUDIO_INPUT_DEVICE = os.getenv("AUDIO_INPUT_DEVICE", None)
if AUDIO_INPUT_DEVICE is not None:
    AUDIO_INPUT_DEVICE = int(AUDIO_INPUT_DEVICE)
AETHER_SYSTEM_PROMPT = os.getenv("AETHER_SYSTEM_PROMPT", "You are Aether, a helpful assistant on a voice call. Keep responses very short.")
SILENCE_THRESHOLD = int(os.getenv("SILENCE_THRESHOLD", "500"))
SILENCE_DURATION = float(os.getenv("SILENCE_DURATION", "1.5"))
DEMO_AUTO_START = os.getenv("AETHER_DEMO_AUTO_START", "").strip().lower() in {"1", "true", "yes", "on"}
ENABLE_HUD = os.getenv("AETHER_ENABLE_HUD", "").strip().lower() in {"1", "true", "yes", "on"}
FIRST_RUN_FILE = data_path("first_run.flag")

class AetherController:
    def __init__(self):
        logger.info("Initializing Aether Core...")
        
        # 1. Initialize Vision (Call Detection)
        self.vision = VisionSystem(templates_dir=data_path("assets"))
        
        # 2. Initialize STT (Whisper)
        self.audio_interface = AudioInterface(
            model_size=WHISPER_MODEL, 
            device_index=AUDIO_INPUT_DEVICE,
            silence_threshold=SILENCE_THRESHOLD,
            silence_duration=SILENCE_DURATION
        )
        
        # 3. Initialize Brain (Ollama)
        self.brain = Brain(
            host=OLLAMA_HOST, 
            model=OLLAMA_MODEL, 
            system_prompt=AETHER_SYSTEM_PROMPT
        )
        
        # 4. Initialize TTS (ElevenLabs)
        self.speech_engine = SpeechEngine(
            api_key=ELEVENLABS_API_KEY,
            voice_id=ELEVENLABS_VOICE_ID
        )

        self.call_active = False

        logger.success("Aether Systems Online.")

    def run(self):
        print("Aether OS v1.0 - Online")
        update_log("Aether Core Online")

        
        # Start detector thread
        threading.Thread(target=self._detector_loop, daemon=True).start()
        
        # Start hotkey listener daemon
        threading.Thread(target=self._hotkey_daemon, daemon=True).start()

        # Start autonomy thread
        threading.Thread(target=autonomy_loop, args=(self.speech_engine, self.audio_interface), daemon=True).start()

        # Start app tracker thread
        from core.app_tracker import start_app_tracker
        start_app_tracker()


        if DEMO_AUTO_START:
            def auto_start():
                time.sleep(3)
                if not self.call_active:
                    logger.warning("DEMO MODE: Starting Aether (Silent)...")
                    self.call_active = True
                    threading.Thread(target=self._conversation_loop, daemon=True).start()
            threading.Thread(target=auto_start, daemon=True).start()

        # System watchdog
        threading.Thread(target=self._system_watchdog, daemon=True).start()

        # Popup-first UI orchestration
        from core.popup import create_popup_window, show_popup, start_popup_logic
        import webview

        # 1. Create windows (main thread)
        popup_win = create_popup_window()
        hud_win = None
        hud_api = None
        if ENABLE_HUD:
            from core.hud import create_hud_window, start_hud_logic
            hud_win, hud_api = create_hud_window()

        def on_boot():
            """Initialization function called once the webview engine is ready."""
            logger.info("Webview engine ready. Initializing window logics...")
            start_popup_logic(popup_win)
            if hud_win:
                start_hud_logic(hud_win, hud_api)
            if not os.path.exists(FIRST_RUN_FILE):
                state["assistant_text"] = "Aether is running. Click the tray icon to begin."
                show_popup()
                if self.speech_engine.client:
                    self.speech_engine.speak_async("Aether is now running. Click the tray icon to begin.")
                with open(FIRST_RUN_FILE, "w", encoding="utf-8") as first_run:
                    first_run.write("done")


        # 2. Start the shared event loop (blocks here)
        logger.info(f"Starting Aether UI loop in {'popup+hud' if ENABLE_HUD else 'minimal'} mode...")
        webview.start(on_boot, gui='edgechromium')


    def _system_watchdog(self):
        tick = 0
        last_audio_change = time.time()
        last_known_status = state["status"]
        
        while True:
            tick += 1
            current_status = state["status"]
            
            # Reset deadlock timer if status changes
            if current_status != last_known_status:
                last_audio_change = time.time()
                last_known_status = current_status
            
            # 1. State Deadlock Protection: If stuck in 'thinking', 'listening', or 'speaking' for >20s, force reset
            if current_status != "idle" and (time.time() - last_audio_change > 20):
                logger.warning(f"[WATCHDOG] Detecting state deadlock ({current_status}). Forcing state recovery...")
                self.reset_state()
                last_audio_change = time.time()

            # 2. Kill-switch check (~10s)
            if tick % 2 == 0:
                if os.path.exists("STOP_AETHER"):
                    logger.warning("STOP_AETHER hardware kill switch detected! Hard aborting daemon.")
                    os.remove("STOP_AETHER")
                    os._exit(0)
            
            # 3. Heartbeat
            if tick % 6 == 0: # Every 30s
                logger.debug(f"Heartbeat: Controller OK | State: {current_status}")
                tick = 0

            time.sleep(5)

    def reset_state(self):
        """Force system back to a clean idle state."""
        state["status"] = "idle"
        state["audio_level"] = 0.0
        state["waveform"] = [0]*64
        state["intent_flash"] = False
        state["assistant_text"] = ""
        logger.info("[RECOVERY] System state has been forcibly reset.")

    def _detector_loop(self):
        """Background thread that continuously scans for an incoming call."""
        while True:
            if not self.call_active:
                if self.vision.detect_and_click_accept(confidence_threshold=0.75):
                    logger.success("Call matched and accepted! Initializing conversation thread...")
                    self.call_active = True
                    threading.Thread(target=self._conversation_loop, daemon=True).start()
            time.sleep(0.5)

    def process_input(self, user_text, speaker="unknown"):
        """
        Unified processing logic for any user input (voice or hotkey).
        Fast Path -> Planning -> Intent -> LLM
        """
        from core.fast_router import match_fast_command
        from core.permissions import check_permission
        from core.safety_guard import authorize, is_safe
        
        state["user_text"] = user_text
        state["status"] = "thinking"
        
        # 1. Fast path intercept
        fast_action = match_fast_command(user_text)
        if fast_action:
            allowed, perm_msg = check_permission(fast_action, speaker)
            if allowed:
                trigger_intent_flash(fast_action)
                logger.success(f"FAST PATH: {fast_action}")
                response = route(fast_action, user_text)
                if response:
                    return response
            else:
                logger.warning(perm_msg)
                return perm_msg

        # 2. Safety check
        is_ok, block_msg = authorize("GENERAL", user_text)
        if not is_ok:
            return block_msg

        # 3. Multi-step planner trigger
        if " and " in user_text.lower() or " then " in user_text.lower():
            trigger_intent_flash("PLANNING")
            logger.info("Planning multi-step execution...")
            # Caller will handle "Planning steps" speech
            
            plan = create_plan(user_text)
            results = execute_plan(plan)
            return "Tasks completed."


        # 4. Intent detection and routing
        intent = detect_intent(user_text)
        if intent != "CHAT":
            trigger_intent_flash(intent)
            logger.info(f"Executing: {intent}")
            action_result = route(intent, user_text)
            if action_result:
                return action_result
        
        # 5. Fallback to LLM
        trigger_intent_flash("LLM")
        logger.info("Conversing")
        return self.brain.generate_response(user_text)

    def _hotkey_daemon(self):
        """On-demand activation daemon with speaker identification."""
        while True:
            try:
                if not state.get("active") or not state.get("force_listen"):
                    time.sleep(0.1)
                    continue
                
                state["force_listen"] = False
                state["status"] = "listening"
                logger.success("Listening via hotkey...")
                
                user_text = self.audio_interface.listen_and_transcribe()
                
                if user_text:
                    logger.info(f"User (hotkey): {user_text}")
                    # In a real scenario, speaker ID would happen here
                    response = self.process_input(user_text, speaker="vaish") 
                    
                    if response:
                        state["status"] = "speaking"
                        state["assistant_text"] = response
                        self.speech_engine.speak(response) # Blocking speak here for hotkey flow
                
                state["active"] = False
                state["status"] = "idle"
                state["hotkey_active"] = False
                
            except Exception as e:
                logger.error(f"Hotkey daemon error: {e}")
                state["status"] = "idle"
                state["active"] = False
                time.sleep(1)

    def _conversation_loop(self):
        """The dedicated thread that runs during an active call."""
        self.brain.reset_memory()
        time.sleep(1.5) 
        greeting = "Hello, Aether here. How can I help you?"
        self.speech_engine.speak_async(greeting)
        
        consecutive_silences = 0
        while self.call_active:
            state["status"] = "listening"
            if not self.vision.is_call_active():
                logger.info("Call ended detected visually.")
                break
            
            user_text = self.audio_interface.listen_and_transcribe(
                on_speech_start=self.speech_engine.stop_speaking
            )
            
            if not user_text:
                consecutive_silences += 1
                if consecutive_silences > 6:
                    logger.warning("Prolonged silence. Hanging up...")
                    break
                continue
                
            consecutive_silences = 0
            logger.info(f"User: {user_text}")
            
            if any(word in user_text.lower() for word in ["bye", "goodbye", "talk to you later"]):
                self.speech_engine.speak("Goodbye.")
                break

            # Centralized Processing
            response = self.process_input(user_text)
            
            if response:
                state["assistant_text"] = response
                self.speech_engine.speak_async(response)
            
            state["status"] = "idle"
            
        logger.info("Call ended or conversation loop exited. Resetting state.")
        self.call_active = False

def preflight():

    """Initial hardware and network polling sequence."""
    logger.info("Running Dependency Audit...")
    missing = []
    warnings = []
    
    # Check for Vision Assets
    assets_dir = data_path("assets")
    if not os.path.exists(os.path.join(assets_dir, "accept_button.png")):
        missing.append("Vision Templates (Required for Call Auto-Answering)")

    try:
        import sounddevice as sd

        devices = sd.query_devices()
        if not any(device.get("max_input_channels", 0) > 0 for device in devices):
            warnings.append("No microphone input device detected")
    except Exception as e:
        warnings.append(f"Microphone check failed: {e}")

    try:
        with open(data_path("healthcheck.tmp"), "w", encoding="utf-8") as health_file:
            health_file.write("ok")
    except Exception as e:
        warnings.append(f"Data directory is not writable: {e}")
        
    if missing or warnings:
        items = [*missing, *warnings]
        msg = "SETUP WARNINGS:\n" + "\n".join([f"- {m}" for m in items])
        logger.warning(msg)
        state["assistant_text"] = "Limited setup detected. Some features may be disabled."
    else:
        logger.success("Environment Validation: ALL SYSTEMS GO")
        
    return True

if __name__ == "__main__":
    # 1. Establish Environment — Singleton via Windows Named Mutex
    os.makedirs(data_path(), exist_ok=True)

    # Kernel-level singleton: mutex auto-releases on process death, survives crashes
    _mutex_handle = None
    if sys.platform == "win32":
        import ctypes
        from ctypes import wintypes
        _kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        ERROR_ALREADY_EXISTS = 183
        _mutex_handle = _kernel32.CreateMutexW(None, True, "Global\\AetherOSSingleton")
        if ctypes.get_last_error() == ERROR_ALREADY_EXISTS:
            logger.error("Aether OS is already running! Aborting duplicate boot.")
            if _mutex_handle:
                _kernel32.CloseHandle(_mutex_handle)
            sys.exit(0)

    # 2. Fast Boot Readiness Gate
    def wait_for_ready(timeout=5):
        t0 = time.time()
        while time.time() - t0 < timeout:
            try:
                socket.create_connection(("127.0.0.1", 11434), timeout=0.5).close()
                return True
            except:
                time.sleep(0.5)
        return False

    logger.info("Waiting for local LLM endpoint...")
    if not wait_for_ready():
        logger.warning("LLM endpoint not detected after timeout. Attempting boot anyway...")
        
    # 3. One-time tray & hotkey initialization (BEFORE the recovery loop)
    if not preflight():
        exit(1)

    threading.Thread(target=run_tray, daemon=True).start()
    try:
        threading.Thread(target=start_hotkey_listener, daemon=True).start()
    except Exception:
        pass

    try:
        logger.info("========== AETHER OS ACTIVE (SESSION START) ==========")

        controller = AetherController()
        controller.run()

    except KeyboardInterrupt:
        logger.info("User initiated soft shutdown.")
    except Exception as e:
        logger.exception(f"CRITICAL SYSTEM FAILURE: {e}")
        _notify_user("Aether", "Aether hit an unexpected error. Open the tray panel and use Open Logs for details.")
    finally:
        # Mutex is auto-released by the OS when the process exits
        if _mutex_handle:
            _kernel32.CloseHandle(_mutex_handle)

