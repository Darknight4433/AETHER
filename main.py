import os
import sys

# Ensure the working directory is explicitly set to the directory containing main.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

import time
import threading
from dotenv import load_dotenv
from loguru import logger

# Establish permanent trace log
logger.add("aether.log", rotation="10 MB", level="INFO")

# Import Core Systems
from core.vision import VisionSystem
from core.audio_io import AudioInterface
from core.llm import Brain
from core.tts import SpeechEngine
from core.intent import detect_intent
from core.router import route
from core.planner import create_plan
from core.agent import execute_plan
from core.safety import is_safe
from core.autonomy import autonomy_loop
from ui.state import state, update_log
from core.tray import run_tray

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
        
        print("Aether OS v1.0 — Online ⚡")
        logger.info("Aether OS v1.0 Dashboard running on http://127.0.0.1:8000/ ⚡")
        update_log("Aether Core Online")
        
        # Start detector thread
        threading.Thread(target=self._detector_loop, daemon=True).start()
        
        # Start autonomy thread (Phase 14)
        threading.Thread(target=autonomy_loop, args=(self.speech_engine, self.audio_interface), daemon=True).start()

        # DEMO BYPASS: Auto-start conversation without waiting for a WhatsApp call
        def auto_start():
            time.sleep(3)
            if not self.call_active:
                logger.warning("DEMO MODE: Bypassing WhatsApp detector. Starting Aether...")
                self.call_active = True
                threading.Thread(target=self._conversation_loop, daemon=True).start()
        threading.Thread(target=auto_start, daemon=True).start()

        # Keep main thread alive
        try:
            pulse_clock = 0
            while True:
                pulse_clock += 5
                if pulse_clock >= 30:
                    logger.debug("Heartbeat: Native daemon is alive and polling actively.")
                    pulse_clock = 0
                    
                if os.path.exists("STOP_AETHER"):
                    logger.warning("💀 STOP_AETHER hardware kill switch detected! Hard aborting daemon.")
                    logger.info("========== AETHER MODULE OFFLINE (SESSION SHUTDOWN) ==========")
                    os.remove("STOP_AETHER")  # Reset switch for next boot
                    os._exit(0)
                time.sleep(5)
        except KeyboardInterrupt:
            logger.info("========== AETHER MODULE OFFLINE (SESSION TERMINATED) ==========")
            logger.info("Aether shutting down manually.")

    def _detector_loop(self):
        """Background thread that continuously scans for an incoming call."""
        while True:
            if not self.call_active:
                if self.vision.detect_and_click_accept(confidence_threshold=0.75):
                    logger.success("📞 Call matched and accepted! Initializing conversation thread...")
                    self.call_active = True
                    threading.Thread(target=self._conversation_loop, daemon=True).start()
            time.sleep(0.5)

    def _conversation_loop(self):
        """The dedicated thread that runs during an active call."""
        self.brain.reset_memory()
        
        # Give WhatsApp a moment to connect
        time.sleep(1.5) 
        greeting = "Hello, Aether here. How can I help you?"
        logger.info(f"Aether: {greeting}")
        self.speech_engine.speak_async(greeting) # Using async voice!
        
        consecutive_silences = 0
        
        while self.call_active:
            start_time = time.time()
            state["status"] = "listening"
            
            # Check if call is still active (Phase 9 capability)
            if not self.vision.is_call_active():
                logger.info("📴 Call ended detected visually.")
                break
            
            # Listen for user speech (Phase 3 interruptible trigger passed here)
            user_text = self.audio_interface.listen_and_transcribe(
                on_speech_start=self.speech_engine.stop_speaking
            )
            
            if not user_text:
                consecutive_silences += 1
                if consecutive_silences > 6: # 6 * 1.5s = ~10s of silence
                    logger.warning("Prolonged silence. Hanging up... (breaking loop)")
                    break
                continue
                
            consecutive_silences = 0 # Reset silence counter
            logger.info(f"User: {user_text}")
            
            # Simple keyword heuristic to exit
            if any(word in user_text.lower() for word in ["bye", "goodbye", "talk to you later"]):
                logger.info("Ending call due to user goodbye.")
                self.speech_engine.speak_async("Goodbye.")
                break

            # Safety Check (Phase 11)
            if not is_safe(user_text):
                logger.warning(f"Restricted action blocked: {user_text}")
                self.speech_engine.speak_async("That action is restricted.")
                continue

            # 🔥 Multi-step Planner Trigger (Phase 11)
            if " and " in user_text.lower() or " then " in user_text.lower():
                logger.info("🧠 Planning multi-step execution...")
                self.speech_engine.speak_async("Planning steps.")
                
                plan = create_plan(user_text)
                results = execute_plan(plan)
                
                self.speech_engine.speak_async("Task completed.")
                continue

            # 🔥 Sub-second Fast Path Intercept
            from core.fast_router import match_fast_command
            from actions.environments import deep_work, start_dev
            from actions.system_fast import mute, screenshot, get_time
            
            fast_action = match_fast_command(user_text)
            if fast_action:
                logger.success(f"⚡ FAST PATH ACTIVATED: {fast_action}")
                response = ""
                if fast_action == "DEEP_WORK": response = deep_work()
                elif fast_action == "START_DEV": response = start_dev()
                elif fast_action == "MUTE": response = mute()
                elif fast_action == "SCREENSHOT": response = screenshot()
                elif fast_action == "TIME": response = get_time()
                
                if response:
                    self.speech_engine.speak_async(response)
                continue

            # Intent Detection & Routing (Phase 10 / Single-step)
            intent = detect_intent(user_text)
            
            if intent != "CHAT":
                logger.info(f"⚙️ Executing: {intent}")
                action_result = route(intent, user_text)
                
                if action_result:
                    self.speech_engine.speak_async(action_result)
                    continue
            
            # Fallback out of actions -> AI Generation
            logger.info("🧠 Conversing")
            reply_text = self.brain.generate_response(user_text)
            
            # Speak the reply
            self.speech_engine.speak_async(reply_text)
            
            state["latency"] = f"{(time.time() - start_time):.2f}s"
            state["status"] = "idle"
            
        logger.info("Call ended or conversation loop exited. Resetting state.")
        self.call_active = False

def preflight():
    """Initial hardware and network polling sequence."""
    required = [".env", "config", "data"]
    for r in required:
        if not os.path.exists(r):
            logger.error(f"Missing required component: {r}. Aborting boot.")
            print(f"Missing: {r}")
            return False
    return True

if __name__ == "__main__":
    import socket
    def is_running():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Prevent ghost locks
        try:
            s.bind(("127.0.0.1", 65432))
            return False, s # Keep socket open during process lifetime
        except Exception:
            return True, None

    running, lock_sock = is_running()
    if running:
        logger.error("Aether OS is already actively bound! Aborting duplicate boot.")
        exit(0)

    logger.info("Initiating 10-second pre-boot delay awaiting hardware network attachments...")
    time.sleep(10)

    if not preflight():
        exit(1)
        
    logger.success("Aether Booted via Startup Hook ⚡")
    
    # Start tray in background
    threading.Thread(target=run_tray, daemon=True).start()
        
    if os.path.exists("SAFE_MODE"):
        logger.info("SAFE_MODE File Detected! Overriding system intelligence to Safe State (Autonomy: OFF)")
        state["autonomy"] = False
        
    logger.info("========== AETHER OS ACTIVE (SESSION START) ==========")    
    while True:
        try:
            logger.info("Spooling up Aether Core Runtime...")
            aether = AetherController()
            aether.run()
        except Exception as e:
            logger.error(f"CRITICAL SYSTEM CRASH: {e}. Initiating daemon auto-restart...")
            time.sleep(5)
