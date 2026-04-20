def detect_emotion(text: str) -> str:
    if not text:
        return "calm"
        
    t = text.lower()

    if any(w in t for w in ["error", "fail", "failed", "problem", "issue", "sorry", "cannot", "can't"]):
        return "error"

    if any(w in t for w in ["done", "completed", "success", "ok", "got it", "finished", "ready"]):
        return "success"

    if any(w in t for w in ["wait", "checking", "processing", "let me", "planning", "searching"]):
        return "thinking"

    if any(w in t for w in ["urgent", "warning", "immediately", "alert", "attention"]):
        return "urgent"

    return "calm"
