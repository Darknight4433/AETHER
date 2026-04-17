import ollama
import json
import os
from loguru import logger
from ui.state import state, update_log

SYSTEM_PROMPT = """
You are Aether Planner.
Convert user requests into JSON steps using:
CREATE_FILE {"name": string, "content": string}
READ_FILE {"name": string}
OPEN_APP {"app": string}
SEARCH_WEB {"query": string}
TAKE_SCREENSHOT {}

Rules:
- Output ONLY JSON array wrapped in {"steps": ...}
- Use minimal steps
"""

def create_plan(user_input):
    state["thought"] = f"Planning structure for: {user_input}"
    update_log(f"Planner processing query: {user_input[:40]}")
    state["error"] = ""

    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    model = os.getenv("OLLAMA_MODEL", "llama3")
    client = ollama.Client(host=host)

    try:
        response = client.generate(
            model=model,
            prompt=SYSTEM_PROMPT + "\nUser: " + user_input,
            format="json", # Force json structured output
            stream=False
        )

        text = response['response']
        return json.loads(text)
    except Exception as e:
        error_str = f"Plan parse failed: {e}"
        logger.error(f"⚠️ {error_str}")
        state["error"] = error_str
        return {"steps": []}
