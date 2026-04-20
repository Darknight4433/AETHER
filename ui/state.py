state = {
    "status": "idle",
    "active": False,            # Whether Aether is engaged (post-hotkey)
    "last_action": "System Booting...",
    "thought": "",
    "error": "",
    "dnd": False,
    "latency": "0.00s",
    "logs": [],
    "memory": {},
    "autonomy": False,
    "force_listen": False,      # Trigger from hotkey
    "hotkey_active": False,
    "speaker": "unknown",       # Current speaker identified
    "speaker_confidence": 0.0,   # Speaker ID confidence (0.0-1.0)
    "audio_level": 0.0,            # Current input or output audio energy
    "audio_source": "mic",         # "mic" or "tts"
    "user_text": "",
    "assistant_text": ""
}

def update_log(entry):
    state["logs"].insert(0, entry)
    if len(state["logs"]) > 50:
        state["logs"].pop()
