from actions.system import open_app, search_web, play_song
from actions.filesystem import create_file, read_file
from actions.system_controls import screenshot, volume_up
from actions.vision_click import click_ui
from vision.screen import capture_screen
from vision.ocr import extract_text
from datetime import datetime
from loguru import logger

def route(intent, text=None, args=None):
    """
    Unified routing system for Aether.
    Handles both direct intents (from voice) and planned actions (from LLM planner).
    """
    from ui.state import state
    from core.usage_logger import log_action

    args = args or {}
    
    # Normalize inputs
    if not text and args:
        text = args.get("query") or args.get("name") or args.get("app") or ""

    logger.info(f"Routing intent: {intent}")

    # Log every routed action for the learning engine
    active_app = state.get("active_app", "unknown")
    log_action(intent.lower(), app=active_app, metadata={"text": text[:100] if text else ""})

    if intent == "OPEN_APP":
        app_name = text or args.get("app")
        return open_app(app_name)

    elif intent == "SEARCH_WEB" or intent == "SEARCH":
        query = text or args.get("query")
        return search_web(query)

    elif intent == "PLAY_SONG":
        song = text or args.get("song")
        return play_song(song)

    elif intent == "GET_TIME" or intent == "TIME":
        return f"The time is {datetime.now().strftime('%I:%M %p')}"

    elif intent == "READ_SCREEN" or intent == "TAKE_SCREENSHOT":
        if intent == "TAKE_SCREENSHOT":
            return screenshot()
            
        img_path = capture_screen()
        text_on_screen = extract_text(img_path)
        if text_on_screen:
            return f"I can see the following on your screen: {text_on_screen[:300]}" 
        return "I can't read any clear text on the screen right now."

    elif intent == "CLICK_UI":
        target = text.lower().replace("click", "").replace("the", "").strip() if text else args.get("target")
        return click_ui(target)

    elif intent == "CREATE_FILE":
        return create_file(args.get("name"), args.get("content", ""))

    elif intent == "READ_FILE":
        return read_file(args.get("name"))
        
    elif intent == "MUTE":
        from actions.system_fast import mute
        return mute()

    return None


