"""
Aether Context Engine — Adapts behavior based on the active application.

This is the intelligence layer that makes Aether context-aware.
Each app profile defines what shortcuts, actions, and suggestions
are available when that application is in focus.
"""

from loguru import logger
from ui.state import state, update_log


# ─────────────────────────────────────────────
# SECURITY: Only known-safe apps get special treatment
# ─────────────────────────────────────────────
SAFE_APPS = {
    "chrome.exe",
    "msedge.exe",
    "firefox.exe",
    "brave.exe",
    "opera.exe",
    "code.exe",
    "spotify.exe",
    "explorer.exe",
    "notepad.exe",
    "WindowsTerminal.exe",
    "cmd.exe",
    "powershell.exe",
    "Discord.exe",
    "Telegram.exe",
    "WhatsApp.exe",
    "vlc.exe",
    "EXCEL.EXE",
    "WINWORD.EXE",
    "POWERPNT.EXE",
}


# ─────────────────────────────────────────────
# APP PROFILES: Context-specific capabilities
# ─────────────────────────────────────────────
APP_PROFILES = {
    # ── Browsers ──
    "chrome.exe": {
        "mode": "browser",
        "label": "Chrome",
        "actions": ["search_web", "open_tab", "close_tab", "bookmark"],
        "voice_hints": [
            "search for...",
            "open a new tab",
            "go to...",
            "read this page",
        ],
    },
    "msedge.exe": {
        "mode": "browser",
        "label": "Edge",
        "actions": ["search_web", "open_tab", "close_tab", "bookmark"],
        "voice_hints": ["search for...", "open a new tab"],
    },
    "firefox.exe": {
        "mode": "browser",
        "label": "Firefox",
        "actions": ["search_web", "open_tab", "close_tab"],
        "voice_hints": ["search for...", "open a new tab"],
    },
    "brave.exe": {
        "mode": "browser",
        "label": "Brave",
        "actions": ["search_web", "open_tab", "close_tab"],
        "voice_hints": ["search for...", "open a new tab"],
    },

    # ── Development ──
    "code.exe": {
        "mode": "dev",
        "label": "VS Code",
        "actions": ["run_terminal", "open_file", "search_code", "git_commit"],
        "voice_hints": [
            "run this file",
            "open terminal",
            "search in project",
            "commit changes",
        ],
    },
    "WindowsTerminal.exe": {
        "mode": "dev",
        "label": "Terminal",
        "actions": ["run_command"],
        "voice_hints": ["run...", "list files", "navigate to..."],
    },

    # ── Media ──
    "spotify.exe": {
        "mode": "media",
        "label": "Spotify",
        "actions": ["play_pause", "next_track", "previous_track", "volume"],
        "voice_hints": [
            "play music",
            "next song",
            "pause",
            "volume up",
        ],
    },
    "vlc.exe": {
        "mode": "media",
        "label": "VLC",
        "actions": ["play_pause", "volume", "fullscreen"],
        "voice_hints": ["pause", "play", "fullscreen"],
    },

    # ── Communication ──
    "Discord.exe": {
        "mode": "comms",
        "label": "Discord",
        "actions": ["mute_mic", "deafen", "leave_call"],
        "voice_hints": ["mute", "deafen", "leave voice"],
    },
    "WhatsApp.exe": {
        "mode": "comms",
        "label": "WhatsApp",
        "actions": ["send_message", "make_call"],
        "voice_hints": ["call...", "message..."],
    },
    "Telegram.exe": {
        "mode": "comms",
        "label": "Telegram",
        "actions": ["send_message"],
        "voice_hints": ["message..."],
    },

    # ── Productivity ──
    "EXCEL.EXE": {
        "mode": "office",
        "label": "Excel",
        "actions": ["save_file", "new_sheet"],
        "voice_hints": ["save", "new sheet", "format cells"],
    },
    "WINWORD.EXE": {
        "mode": "office",
        "label": "Word",
        "actions": ["save_file", "dictate"],
        "voice_hints": ["save", "dictate", "insert heading"],
    },
    "POWERPNT.EXE": {
        "mode": "office",
        "label": "PowerPoint",
        "actions": ["save_file", "start_slideshow"],
        "voice_hints": ["save", "start presentation", "next slide"],
    },

    # ── System ──
    "explorer.exe": {
        "mode": "system",
        "label": "File Explorer",
        "actions": ["open_folder", "search_files", "create_folder"],
        "voice_hints": ["open...", "search for...", "create folder"],
    },
    "notepad.exe": {
        "mode": "system",
        "label": "Notepad",
        "actions": ["save_file", "dictate"],
        "voice_hints": ["save", "dictate"],
    },
}

# Default profile for unknown/unlisted apps
DEFAULT_PROFILE = {
    "mode": "general",
    "label": "Unknown App",
    "actions": ["screenshot", "mute", "get_time"],
    "voice_hints": [],
}


# ─────────────────────────────────────────────
# CORE ENGINE
# ─────────────────────────────────────────────
_current_profile = DEFAULT_PROFILE


def get_profile(app_name):
    """Get the context profile for an application."""
    return APP_PROFILES.get(app_name, DEFAULT_PROFILE)


def get_current_profile():
    """Get the profile for the currently active application."""
    return _current_profile


def get_current_mode():
    """Get the current context mode (browser, dev, media, etc.)."""
    return _current_profile.get("mode", "general")


def get_available_actions():
    """Get the list of actions available for the current app context."""
    return _current_profile.get("actions", [])


def get_voice_hints():
    """Get context-sensitive voice command suggestions."""
    return _current_profile.get("voice_hints", [])


def is_safe_app(app_name):
    """Check if the current app is in the safety whitelist."""
    return app_name in SAFE_APPS


def on_app_changed(app_name, window_title=""):
    """Called by the Process Anchor when the active app changes."""
    global _current_profile

    if not is_safe_app(app_name):
        _current_profile = DEFAULT_PROFILE
        state["context_mode"] = "general"
        state["context_label"] = app_name
        logger.debug(f"Context Engine: Unknown app '{app_name}' — using default profile")
        return

    _current_profile = get_profile(app_name)
    mode = _current_profile["mode"]
    label = _current_profile["label"]

    state["context_mode"] = mode
    state["context_label"] = label

    logger.info(f"Context Engine: {label} ({mode} mode)")
    update_log(f"Context: {label}")


def get_context_prompt_addon():
    """
    Returns an additional system prompt fragment based on current context.
    This is injected into the LLM prompt to make responses context-aware.
    """
    mode = get_current_mode()
    label = _current_profile.get("label", "Unknown")
    hints = get_voice_hints()

    if mode == "general":
        return ""

    hint_text = ""
    if hints:
        hint_text = " The user might say things like: " + ", ".join(f'"{h}"' for h in hints[:3])

    return (
        f" The user is currently using {label} ({mode} mode).{hint_text}"
        f" Tailor your responses accordingly."
    )
