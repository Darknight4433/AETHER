state = {
    "status": "idle",
    "last_action": "System Booting...",
    "thought": "",
    "error": "",
    "dnd": False,
    "latency": "0.00s",
    "logs": [],
    "memory": {},
    "autonomy": False
}

def update_log(entry):
    state["logs"].insert(0, entry)
    if len(state["logs"]) > 50:
        state["logs"].pop()
