import time
from core.habits import detect_habits

LAST_SUGGESTIONS = {}

def evaluate_rules(state):
    global LAST_SUGGESTIONS
    suggestions = []
    now = time.time()
    
    # Time-based habits
    if state.get("time_block") == "morning":
        if now - LAST_SUGGESTIONS.get("morning_chrome", 0) > 14400: # Wait 4 hours
            suggestions.append({
                "action": "OPEN_APP",
                "args": {"app": "chrome"},
                "reason": "Start your usual morning browser session"
            })
            LAST_SUGGESTIONS["morning_chrome"] = now
            
    # Screen-based hints
    if "error" in state.get("screen_text", "").lower():
        if now - LAST_SUGGESTIONS.get("screen_error", 0) > 300: # Wait 5 minutes
            suggestions.append({
                "action": "SEARCH_WEB",
                "args": {"query": "fix error shown on screen"},
                "reason": "I noticed an error on your screen"
            })
            LAST_SUGGESTIONS["screen_error"] = now
            
    # 🧠 Habit-based suggestions
    habits = detect_habits()
    current_hour = state.get("hour", 0)

    if current_hour in habits:
        for action in habits[current_hour]:
            habit_key = f"habit_{action}_{current_hour}"
            # Ensure we only suggest once per day so it isn't annoying
            if now - LAST_SUGGESTIONS.get(habit_key, 0) > 86400:
                suggestions.append({
                    "action": action,
                    "args": {}, # We'd inject learned args here sequentially but empty dictates intent
                    "reason": f"You usually run {action} around this time"
                })
                LAST_SUGGESTIONS[habit_key] = now
            
    return suggestions
