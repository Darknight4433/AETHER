import os
import sys
import shutil

# Ensure the working directory is explicitly set to the directory containing main.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

import time
import threading
from dotenv import load_dotenv
from loguru import logger

# Establish permanent trace log
if sys.platform == "win32":
    try:
        import sys
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except Exception:
        pass

logger.add("aether.log", rotation="10 MB", level="INFO", encoding="utf-8")

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
from core.hud import start_hud
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

class AetherController:
    def __init__(self):
        logger.info("Initializing Aether Core...")
        
        # 1. Initialize Vision (Call Detection)
        self.vision = VisionSystem(templates_dir="assets")
        
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
        import uvicorn
        def start_dashboard():
            uvicorn.run("ui.server:app", host="127.0.0.1", port=8000, log_level="error")
        threading.Thread(target=start_dashboard, daemon=True).start()
        
        print("Aether OS v1.0 - Online")
        logger.info("Aether OS v1.0 Dashboard running on http://127.0.0.1:8000/")
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


        # DEMO BYPASS
        def auto_start():
            time.sleep(3)
            if not self.call_active:
                logger.warning("DEMO MODE: Starting Aether (Silent)...")
                self.call_active = True
                threading.Thread(target=self._conversation_loop, daemon=True).start()
        threading.Thread(target=auto_start, daemon=True).start()

        # System watchdog
        threading.Thread(target=self._system_watchdog, daemon=True).start()

        # 🧠 FINAL SYSTEM BEHAVIOR: Multi-Window Orchestration
        from core.popup import create_popup_window, start_popup_logic
        from core.hud import create_hud_window, start_hud_logic
        import webview

        # 1. Create windows (main thread)
        popup_win = create_popup_window()
        hud_win, hud_api = create_hud_window()

        def on_boot():
            """Initialization function called once the webview engine is ready."""
            logger.info("Webview engine ready. Initializing window logics...")
            start_popup_logic(popup_win)
            if hud_win:
                start_hud_logic(hud_win, hud_api)


        # 2. Start the shared event loop (blocks here)
        logger.info("Starting unified Aether UI loop...")
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
        
        # 1. 🔥 Sub-second Fast Path Intercept
        fast_action = match_fast_command(user_text)
        if fast_action:
            allowed, perm_msg = check_permission(fast_action, speaker)
            if allowed:
                trigger_intent_flash(fast_action)
                logger.success(f"⚡ FAST PATH: {fast_action}")
                response = route(fast_action, user_text)
                if response:
                    return response
            else:
                logger.warning(perm_msg)
                return perm_msg

        # 2. 🛑 Safety Check
        is_ok, block_msg = authorize("GENERAL", user_text)
        if not is_ok:
            return block_msg

        # 3. 🧠 Multi-step Planner Trigger
        if " and " in user_text.lower() or " then " in user_text.lower():
            trigger_intent_flash("PLANNING")
            logger.info("🧠 Planning multi-step execution...")
            # Caller will handle "Planning steps" speech
            
            plan = create_plan(user_text)
            results = execute_plan(plan)
            return "Tasks completed."


        # 4. ⚙️ Intent Detection & Routing
        intent = detect_intent(user_text)
        if intent != "CHAT":
            trigger_intent_flash(intent)
            logger.info(f"⚙️ Executing: {intent}")
            action_result = route(intent, user_text)
            if action_result:
                return action_result
        
        # 5. 🤖 Fallback to LLM
        trigger_intent_flash("LLM")
        logger.info("🧠 Conversing")
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
                logger.success("🎤 Listening via hotkey...")
                
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
                logger.info("📴 Call ended detected visually.")
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
    
    # Check for FFmpeg (Critical for Whisper)
    if not shutil.which("ffmpeg"):
        missing.append("FFmpeg (Required for Speech-to-Text)")
        
    # Check for Vision Assets
    if not os.path.exists("assets/accept_button.png"):
        missing.append("Vision Templates (Required for Call Auto-Answering)")
        
    if missing:
        msg = "⚠️ SETUP WARNINGS:\n" + "\n".join([f"- {m}" for m in missing])
        logger.warning(msg)
        state["assistant_text"] = "Limited setup detected. Some features may be disabled."
    else:
        logger.success("Environment Validation: ALL SYSTEMS GO")
        
    return True

if __name__ == "__main__":
    # 1. Establish Environment
    if not os.path.exists("data"):
        os.makedirs("data")
        
    instance_lock = os.path.join("data", "aether.lock")
    if os.path.exists(instance_lock):
        logger.error("Aether OS is already actively bound! Aborting duplicate boot.")
        exit(0)

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
        
    # 3. Permanent Recovery Loop
    while True:
        try:
            if not preflight():
                exit(1)
            
            logger.info("========== AETHER OS ACTIVE (SESSION START) ==========")
            
            # Native Tray & Listeners
            threading.Thread(target=run_tray, daemon=True).start()
            try:
                threading.Thread(target=start_hotkey_listener, daemon=True).start()
            except:
                pass
            
            controller = AetherController()
            controller.run()
            
        except KeyboardInterrupt:
            logger.info("User initiated soft shutdown.")
            break
        except Exception as e:
            logger.exception(f"CRITICAL SYSTEM FAILURE: {e}")
            logger.info("Initiating self-healing protocol... restarting in 5s")
            time.sleep(5)
