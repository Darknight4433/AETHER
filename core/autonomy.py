import time
from loguru import logger
from core.sensors import get_time_block, screen_text_sample
from core.rules import evaluate_rules
from core.tool_router import execute_tool
from core.confirm import confirm_and_execute
from core.memory_engine import load_memory
from ui.state import state, update_log

def autonomy_loop(speech_engine, audio_interface):
    logger.info("🧠 Autonomous mode active")
    while True:
        state["memory"] = load_memory()
        
        if state.get("dnd", False):
            time.sleep(5)
            continue
            
        if not state["autonomy"]:
            time.sleep(5)
            continue
            
        import datetime
        env_state = {
            "time_block": get_time_block(),
            "screen_text": screen_text_sample(),
            "hour": datetime.datetime.now().hour
        }
        
        suggestions = evaluate_rules(env_state)
        
        for s in suggestions:
            logger.info(f"💡 Autonomous Suggestion Block: {s['reason']}")
            update_log(f"[Autonomy] Triggering Suggestion: {s['action']}")
            result = confirm_and_execute(s, execute_tool, speech_engine, audio_interface)
            logger.info(f"🤖 Autonomy Decision: {result}")
            update_log(f"[Autonomy] Result: {result}")
            
        time.sleep(30)
