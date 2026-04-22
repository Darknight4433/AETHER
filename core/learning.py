"""
Aether Learning Engine — Pattern detection and habit recognition.

Analyzes the usage log to find recurring patterns in the user's behavior.
Uses recency-weighted scoring so recent habits rank higher than old ones.
"""

import json
import math
from datetime import datetime, timedelta
from collections import defaultdict
from loguru import logger

from core.usage_logger import get_log


# ─────────────────────────────────────────────
# PATTERN DETECTION
# ─────────────────────────────────────────────

def _recency_weight(timestamp_str):
    """
    Calculate a recency weight for a log entry.
    Actions from today score 3x, yesterday 2x, this week 1.5x, older 1x.
    """
    try:
        ts = datetime.fromisoformat(timestamp_str)
        age_hours = (datetime.now() - ts).total_seconds() / 3600

        if age_hours < 24:
            return 3.0    # Today
        elif age_hours < 48:
            return 2.0    # Yesterday
        elif age_hours < 168:
            return 1.5    # This week
        else:
            return 1.0    # Older
    except Exception:
        return 1.0


def get_patterns(min_count=2):
    """
    Extract behavioral patterns from the usage log.
    
    Returns a list of dicts sorted by weighted score:
    [
        {
            "app": "code.exe",
            "hour": 17,
            "action": "open_terminal",
            "count": 5,
            "score": 12.5,
            "day_type": "weekday"
        },
        ...
    ]
    """
    data = get_log()
    if not data:
        return []

    # Aggregate by (app, hour_block, action, day_type)
    buckets = defaultdict(lambda: {"count": 0, "score": 0.0, "timestamps": []})

    for entry in data:
        app = entry.get("app", "unknown")
        hour = entry.get("hour", 0)
        action = entry.get("action", "unknown")
        day_type = entry.get("day_type", "weekday")
        ts = entry.get("timestamp", "")

        # Group hours into 2-hour blocks for fuzzier matching
        hour_block = (hour // 2) * 2

        key = (app, hour_block, action, day_type)
        weight = _recency_weight(ts)

        buckets[key]["count"] += 1
        buckets[key]["score"] += weight
        buckets[key]["timestamps"].append(ts)

    # Build sorted pattern list
    patterns = []
    for (app, hour_block, action, day_type), info in buckets.items():
        if info["count"] >= min_count:
            patterns.append({
                "app": app,
                "hour_block": hour_block,
                "action": action,
                "day_type": day_type,
                "count": info["count"],
                "score": round(info["score"], 1),
            })

    # Sort by score (highest first)
    patterns.sort(key=lambda p: p["score"], reverse=True)
    return patterns


def get_top_patterns(n=10):
    """Get the top N strongest patterns."""
    return get_patterns()[:n]


# ─────────────────────────────────────────────
# SUGGESTION ENGINE
# ─────────────────────────────────────────────

# Track what we've already suggested this session to avoid nagging
_suggested_this_session = set()


def suggest_action(current_app, current_hour, day_type="weekday"):
    """
    Check if there's a learned pattern that matches the current context.
    
    Returns:
        tuple: (action, confidence) if a suggestion exists, else (None, 0)
        
    confidence levels:
        0.9+ = strong habit (done 5+ times in this context)
        0.7  = moderate pattern (done 3-4 times)
        0.5  = weak signal (done 2 times)
    """
    patterns = get_patterns(min_count=2)
    if not patterns:
        return None, 0

    hour_block = (current_hour // 2) * 2

    for pattern in patterns:
        # Match context
        if (pattern["app"] == current_app and
                pattern["hour_block"] == hour_block and
                pattern["day_type"] == day_type):

            action = pattern["action"]
            count = pattern["count"]

            # Skip if already suggested this session
            suggestion_key = f"{action}_{current_app}_{hour_block}"
            if suggestion_key in _suggested_this_session:
                continue

            # Calculate confidence
            if count >= 5:
                confidence = 0.9
            elif count >= 3:
                confidence = 0.7
            else:
                confidence = 0.5

            # Boost if recent
            if pattern["score"] / max(count, 1) > 2.0:
                confidence = min(confidence + 0.1, 1.0)

            # Mark as suggested
            _suggested_this_session.add(suggestion_key)

            return action, confidence

    return None, 0


def reset_session_suggestions():
    """Clear the session suggestion tracker (call on new session/call)."""
    global _suggested_this_session
    _suggested_this_session = set()


# ─────────────────────────────────────────────
# HUMAN-READABLE SUGGESTIONS
# ─────────────────────────────────────────────

ACTION_PHRASES = {
    "open_browser": "open your browser",
    "search_web": "search the web",
    "open_terminal": "open the terminal",
    "run_command": "run a command",
    "play_pause": "play some music",
    "mute": "mute the audio",
    "screenshot": "take a screenshot",
    "open_file": "open a file",
    "git_commit": "commit your changes",
    "send_message": "send a message",
    "make_call": "make a call",
}


def get_suggestion_text(action, confidence):
    """
    Convert a raw action + confidence into a natural voice suggestion.
    """
    phrase = ACTION_PHRASES.get(action, action.replace("_", " "))

    if confidence >= 0.9:
        return f"You usually {phrase} around this time. Want me to do it?"
    elif confidence >= 0.7:
        return f"I've noticed you often {phrase} now. Should I?"
    else:
        return f"Would you like me to {phrase}?"
