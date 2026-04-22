import threading
import time
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw
import os
import sys
from loguru import logger
from ui.state import state

from core.popup import toggle_popup

def create_icon(status="idle"):
    """Generate dynamic icon based on current status with user-requested colors."""
    color_map = {
        "idle": (34, 197, 94),      # Green
        "listening": (56, 189, 248), # Blue
        "thinking": (168, 85, 247), # Purple
        "speaking": (239, 68, 68)   # Red
    }
    
    color = color_map.get(status, (34, 197, 94))
    
    # Create smooth rounded icon
    image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    # Draw glow
    draw.ellipse((8, 8, 56, 56), fill=(color[0], color[1], color[2], 40))
    # Draw main dot
    draw.ellipse((20, 20, 44, 44), fill=color)
    
    return image

def quit_app(icon, item):
    logger.info("Shutting down Aether from tray...")
    icon.stop()
    os._exit(0)

def restart_app(icon, item):
    logger.info("Restarting Aether from tray...")
    icon.stop()
    python = sys.executable
    os.execl(python, python, *sys.argv)

def open_aether(icon, item):
    logger.info(f"Tray Menu Clicked: {item}")
    toggle_popup()

def toggle_dnd(icon, item):
    """Toggle Do Not Disturb mode."""
    state["dnd"] = not state["dnd"]
    dnd_status = "ON" if state["dnd"] else "OFF"
    logger.info(f"DND Mode Toggled: {dnd_status}")

def run_tray():
    """Run system tray with reactive icon updates based on state."""
    menu = Menu(
        MenuItem("Open Aether Panel", open_aether, default=True),
        MenuItem("DND: OFF", toggle_dnd),
        MenuItem("Restart", restart_app),
        MenuItem("Quit", quit_app)
    )
    
    icon = Icon("Aether", create_icon("idle"), "Aether OS", menu=menu)
    
    def update_icon():
        """Background thread that updates tray icon based on state changes."""
        last_status = "idle"
        while True:
            current_status = state.get("status", "idle")
            
            if current_status != last_status:
                icon.icon = create_icon(current_status)
                icon.title = f"Aether - {current_status.upper()}"
                last_status = current_status
                logger.debug(f"Tray icon updated: {current_status}")
            
            time.sleep(0.5)
    
    # Start icon updater thread
    updater_thread = threading.Thread(target=update_icon, daemon=True)
    updater_thread.start()
    
    try:
        logger.success("Aether Tray System Online")
        icon.run()
    except Exception as e:
        logger.error(f"Tray Icon System Crashed: {e}")
