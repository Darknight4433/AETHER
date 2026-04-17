import os
import time
from loguru import logger
from core.intent import detect_intent
from core.planner import create_plan
from core.agent import execute_plan
from core.safety import is_safe
from core.memory_engine import load_memory
from core.sensors import get_time_block
from ui.state import state

logger.info("🔥 AETHER MAX TEST ARCHITECTURE INITIATED 🔥")

# TEST 1: Safety Kernel
try:
    assert is_safe("open chrome") == True, "Safety check failed!"
    assert is_safe("format c: delete everything") == False, "Safety filter breached!"
    assert is_safe("delete all files") == False, "Semantic danger bypass!"
    logger.success("✔ Safety Kernel Operational.")
except AssertionError as e:
    logger.error(f"❌ Safety Failed: {e}")

# TEST 2: Fast Determistic Intent Mappings
try:
    assert detect_intent("Hey play believer song right now") == "PLAY_SONG"
    assert detect_intent("what is on my screen today") == "READ_SCREEN"
    assert detect_intent("open chrome right now") == "OPEN_APP"
    logger.success("✔ Intent NLP Engine Operational.")
except AssertionError as e:
    logger.error("❌ Intent Engine Failed.")

# TEST 3: Action Sandbox Bounds
logger.info("Executing Sandbox Environment Plan...")
try:
    plan = {
        "steps": [
            {"action": "CREATE_FILE", "args": {"name": "test_max.txt", "content": "Aether Override"}},
            {"action": "READ_FILE", "args": {"name": "test_max.txt"}}
        ]
    }
    results = execute_plan(plan)
    assert len(results) == 2
    logger.success(f"✔ Agent Tool Executor Operational (Read verified content: {results[1][:50]})")
except Exception as e:
    logger.error(f"❌ Execution layer crashed: {e}")

# TEST 4: Telemetry & Memory Synch
try:
    tb = get_time_block()
    mem = load_memory()
    logger.success(f"✔ Sensors Active: Time Block -> {tb}")
    logger.success(f"✔ Memory State Connected. System traces detected: {len(mem.get('actions', []))}")
except Exception as e:
    logger.error(f"❌ State mapping crash: {e}")

# TEST 5: Generative Planners (Ollama)
logger.info("Pinging Ollama LLM Array (waiting for local endpoint)...")
try:
    ai_plan = create_plan("Take a screenshot and open notepad")
    if ai_plan and "steps" in ai_plan:
        logger.success(f"✔ Deep LLM Planner Active! Recognized Steps: {len(ai_plan.get('steps'))}")
    else:
        logger.warning("❌ Planner returned empty. Ensure Ollama 'llama3' is running locally.")
except Exception as e:
    logger.error(f"❌ Planner API trace disconnected: {e}")

logger.warning("🔥 ALL LOGIC TESTS FINALIZED. RUN 'python main.py' FOR FULL SYSTEM ACTIVATION. 🔥")
