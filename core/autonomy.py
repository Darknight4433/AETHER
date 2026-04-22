import time
import datetime
from loguru import logger
from core.sensors import get_time_block, screen_text_sample
from core.rules import evaluate_rules
from core.router import route as execute_tool
from core.confirm import confirm_and_execute
from core.memory_engine import load_memory
from ui.state import state, update_log

def autonomy_loop(speech_engine, audio_interface):
    logger.info("Autonomous mode active")

    while True:
        state["memory"] = load_memory()
        
        if state.get("dnd", False):
            time.sleep(5)
            continue
            
        # ─── Learning Engine: Proactive Suggestions ───
        # This runs even when autonomy is off — it's passive intelligence
        try:
            from core.learning import suggest_action, get_suggestion_text

            current_app = state.get("active_app", "unknown")
            current_hour = datetime.datetime.now().hour
            day_type = "weekend" if datetime.datetime.now().weekday() >= 5 else "weekday"

            action, confidence = suggest_action(current_app, current_hour, day_type)

            if action and confidence >= 0.5:
                suggestion_text = get_suggestion_text(action, confidence)
                state["suggestion"] = suggestion_text
                state["suggestion_action"] = action
                state["suggestion_confidence"] = confidence
                logger.info(f"Learning Engine: Suggesting '{action}' (confidence: {confidence})")
                update_log(f"[Learn] {suggestion_text}")

                # Voice suggestion only for high-confidence patterns and when idle
                if confidence >= 0.8 and state.get("status") == "idle":
                    speech_engine.speak_async(suggestion_text)
            else:
                state["suggestion"] = ""
                state["suggestion_action"] = ""
                state["suggestion_confidence"] = 0

        except Exception as e:
            logger.debug(f"Learning Engine cycle skipped: {e}")

        # ─── Rule-Based Autonomy (existing system) ───
        if not state["autonomy"]:
            time.sleep(30)
            continue
            
        env_state = {
            "time_block": get_time_block(),
            "screen_text": screen_text_sample(),
            "hour": datetime.datetime.now().hour
        }
        
        suggestions = evaluate_rules(env_state)
        
        for s in suggestions:
            logger.info(f"Autonomy Suggestion Block: {s['reason']}")
            update_log(f"[Autonomy] Triggering Suggestion: {s['action']}")
            result = confirm_and_execute(s, execute_tool, speech_engine, audio_interface)
            logger.info(f"Autonomy Decision: {result}")
            update_log(f"[Autonomy] Result: {result}")
            
        time.sleep(30)

