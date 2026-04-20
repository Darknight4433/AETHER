import keyboard
from loguru import logger
from ui.state import state


def on_hotkey_listen():
    """Trigger forced listening mode via Ctrl+Alt+A"""
    if state.get("dnd"):
        logger.warning("[DND] mode active. Hotkey ignored.")
        return
    
    # Set both flags: activate Aether + request listening
    state["active"] = True
    state["force_listen"] = True
    state["hotkey_active"] = True
    logger.success("[HOTKEY] TRIGGERED: Aether Waking Up (Listening)")


def on_hotkey_screenshot():
    """Trigger screenshot via Ctrl+Alt+S"""
    from actions.system_fast import screenshot
    
    logger.info("Hotkey: Screenshot triggered")
    result = screenshot()
    logger.info(f"Screenshot result: {result}")


def on_hotkey_mute():
    """Trigger mute via Ctrl+Alt+M"""
    from actions.system_fast import mute
    
    logger.info("Hotkey: Mute triggered")
    result = mute()
    logger.info(f"Mute result: {result}")


def on_hotkey_time():
    """Get time via Ctrl+Alt+T"""
    from actions.system_fast import get_time
    
    logger.info("Hotkey: Time requested")
    result = get_time()
    logger.info(f"Time: {result}")


def start_hotkey_listener():
    """Initialize global hotkey listeners in a blocking fashion."""
    try:
        logger.info("Initializing hotkey system...")
        
        # Main listening hotkey
        keyboard.add_hotkey("ctrl+alt+a", on_hotkey_listen)
        logger.success("+ Hotkey registered: Ctrl+Alt+A (Force Listen)")
        
        # Optional system hotkeys
        keyboard.add_hotkey("ctrl+alt+s", on_hotkey_screenshot)
        logger.debug("+ Hotkey registered: Ctrl+Alt+S (Screenshot)")
        
        keyboard.add_hotkey("ctrl+alt+m", on_hotkey_mute)
        logger.debug("+ Hotkey registered: Ctrl+Alt+M (Mute)")
        
        keyboard.add_hotkey("ctrl+alt+t", on_hotkey_time)
        logger.debug("+ Hotkey registered: Ctrl+Alt+T (Time)")
        
        logger.success("Hotkey Listener Running (Press Ctrl+Alt+A to wake Aether)")
        
        # This blocks indefinitely, listening for hotkeys
        keyboard.wait()
        
    except Exception as e:
        logger.error(f"Hotkey system initialization failed: {e}")
        logger.warning("Continuing without hotkey support (non-critical)")
