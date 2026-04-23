import os
import sys
import threading
import time

from loguru import logger
from PIL import Image, ImageDraw
from pystray import Icon, Menu, MenuItem

from core.popup import show_popup
from core.ui_theme import get_popup_settings
from ui.state import state


def create_icon(status="idle"):
    """Generate a tray icon based on current state colors."""
    settings = get_popup_settings()
    hex_color = settings["state_colors"].get(status, settings["state_colors"]["idle"])
    color = tuple(int(hex_color[i:i + 2], 16) for i in (1, 3, 5))

    image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((10, 10, 54, 54), fill=(color[0], color[1], color[2], 32))
    draw.ellipse((16, 16, 48, 48), fill=(8, 15, 28, 230))
    draw.ellipse((22, 22, 42, 42), fill=color)
    draw.ellipse((26, 18, 34, 26), fill=(255, 255, 255, 65))
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
    logger.info("Tray panel show requested.")
    show_popup()


def toggle_dnd(icon, item):
    state["dnd"] = not state["dnd"]
    logger.info(f"DND Mode Toggled: {'ON' if state['dnd'] else 'OFF'}")
    icon.update_menu()


def toggle_autonomy(icon, item):
    state["autonomy"] = not state.get("autonomy", False)
    logger.info(f"Autonomy Mode Toggled: {'ON' if state['autonomy'] else 'OFF'}")
    icon.update_menu()


def run_tray():
    """Run the system tray with a simple hover tooltip and click-to-open panel."""
    menu = Menu(
        MenuItem("Open Aether Panel", open_aether, default=True),
        MenuItem("Autonomy", toggle_autonomy, checked=lambda item: state.get("autonomy", False)),
        MenuItem("Do Not Disturb", toggle_dnd, checked=lambda item: state.get("dnd", False)),
        MenuItem("Restart", restart_app),
        MenuItem("Quit", quit_app),
    )

    icon = Icon("Aether", create_icon("idle"), "Aether", menu=menu)

    def update_icon():
        last_status = "idle"
        last_palette = None

        while True:
            current_status = state.get("status", "idle")
            current_palette = tuple(sorted(get_popup_settings()["state_colors"].items()))

            if current_status != last_status or current_palette != last_palette:
                icon.icon = create_icon(current_status)
                icon.update_menu()
                icon.title = "Aether"
                last_status = current_status
                last_palette = current_palette
                logger.debug(f"Tray icon updated: {current_status}")

            time.sleep(1.0)

    threading.Thread(target=update_icon, daemon=True).start()

    try:
        logger.success("Aether Tray System Online")
        icon.run()
    except Exception as e:
        logger.error(f"Tray Icon System Crashed: {e}")
