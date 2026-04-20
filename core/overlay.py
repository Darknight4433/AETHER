"""
Microphone LED Overlay - Visual indicator of Aether's current state.
Shows a small colored dot in the top-right corner of the screen.
"""

import threading
import tkinter as tk
from loguru import logger
from ui.state import state


class MicOverlay:
    """
    Always-on-top overlay showing Aether's current state as a colored dot.
    - Blue: Idle (faint, always visible)
    - Green: Listening
    - Yellow: Thinking
    - Red: Speaking
    """

    def __init__(self):
        """Initialize the overlay window."""
        try:
            self.root = tk.Tk()
            self.root.title("Aether Mic Indicator")
            self.root.overrideredirect(True)  # Remove window decorations
            self.root.attributes("-topmost", True)  # Always on top
            self.root.attributes("-alpha", 0.95)  # Slight transparency

            # Small dot size
            self.width, self.height = 24, 24

            # Position in top-right corner with small margin
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            x = screen_width - self.width - 15  # 15px margin from right
            y = 15  # 15px margin from top

            self.root.geometry(f"{self.width}x{self.height}+{x}+{y}")
            self.root.configure(bg="black")

            # Enable transparent background on Windows
            try:
                self.root.attributes("-transparentcolor", "black")
            except tk.TclError:
                # Fallback if transparency not supported
                pass

            # Create canvas for the dot with a transparent background
            self.canvas = tk.Canvas(
                self.root,
                width=self.width,
                height=self.height,
                highlightthickness=0,
                bd=0,
                bg='black'
            )
            self.canvas.pack()

            # Create the colored dot (circle)
            self.dot = self.canvas.create_oval(
                3, 3, self.width-3, self.height-3,
                fill="#89CFF0",
                outline=""
            )

            # Make the overlay draggable by mouse
            self.root.bind("<ButtonPress-1>", self._start_drag)
            self.root.bind("<B1-Motion>", self._do_drag)
            self.root.bind("<ButtonRelease-1>", self._stop_drag)
            self.canvas.bind("<ButtonPress-1>", self._start_drag)
            self.canvas.bind("<B1-Motion>", self._do_drag)
            self.canvas.bind("<ButtonRelease-1>", self._stop_drag)
            self.root.config(cursor="hand2")

            self.visible = True
            self.running = True

            logger.success("Mic overlay initialized")

        except Exception as e:
            logger.error(f"Failed to initialize mic overlay: {e}")
            self.running = False

    def update_color(self):
        """Update the dot color based on current state."""
        if not self.running:
            return

        try:
            current_status = state.get("status", "idle")

            # Color mapping for different states
            color_map = {
                "idle": "#7FB3F1",        # Soft blue when idle
                "listening": "#2ECC71",   # Green when microphone is active
                "thinking": "#F4D03F",    # Yellow when processing
                "speaking": "#E74C3C"     # Red when responding
            }

            color = color_map.get(current_status, "white")

            # Update the dot color
            self.canvas.itemconfig(self.dot, fill=color)

            # Add a subtle border for active states
            if current_status != "idle":
                self.canvas.itemconfig(self.dot, outline="#FFFFFF", width=1)
            else:
                self.canvas.itemconfig(self.dot, outline="", width=0)

        except Exception as e:
            logger.error(f"Error updating overlay color: {e}")

    def update_loop(self):
        """Main update loop - runs every 100ms."""
        if not self.running:
            return

        try:
            self.update_color()
            # Schedule next update
            self.root.after(100, self.update_loop)
        except Exception as e:
            logger.error(f"Overlay update loop error: {e}")
            self.running = False

    def show(self):
        """Show the overlay window."""
        if self.running:
            self.root.deiconify()
            self.visible = True

    def hide(self):
        """Hide the overlay window."""
        if self.running:
            self.root.withdraw()
            self.visible = False

    def destroy(self):
        """Clean up the overlay."""
        self.running = False
        try:
            self.root.destroy()
        except:
            pass

    def _start_drag(self, event):
        """Begin dragging the overlay window."""
        try:
            self._drag_start_x = event.x_root
            self._drag_start_y = event.y_root
            current_geometry = self.root.geometry().split('+')
            self._orig_x = int(current_geometry[1])
            self._orig_y = int(current_geometry[2])
        except Exception:
            self._drag_start_x = None
            self._drag_start_y = None

    def _do_drag(self, event):
        """Move the overlay window while dragging."""
        if not hasattr(self, '_drag_start_x') or self._drag_start_x is None:
            return

        try:
            dx = event.x_root - self._drag_start_x
            dy = event.y_root - self._drag_start_y
            new_x = self._orig_x + dx
            new_y = self._orig_y + dy
            self.root.geometry(f"{self.width}x{self.height}+{new_x}+{new_y}")
        except Exception:
            pass

    def _stop_drag(self, event):
        """Stop dragging the overlay window."""
        self._drag_start_x = None
        self._drag_start_y = None

    def run(self):
        """Start the overlay (blocking - runs the Tkinter main loop)."""
        if not self.running:
            logger.warning("Overlay not running - initialization failed")
            return

        try:
            # Start the update loop
            self.update_loop()

            # Start Tkinter main loop (blocking)
            self.root.mainloop()

        except Exception as e:
            logger.error(f"Overlay main loop error: {e}")
        finally:
            self.running = False


# Global overlay instance
_overlay_instance = None
_overlay_thread = None


def start_overlay():
    """
    Start the microphone overlay in a background thread.
    Safe to call multiple times - only creates one instance.
    """
    global _overlay_instance, _overlay_thread

    if _overlay_instance is not None:
        logger.debug("Overlay already running")
        return

    try:
        def run_overlay():
            global _overlay_instance
            _overlay_instance = MicOverlay()
            _overlay_instance.run()

        _overlay_thread = threading.Thread(target=run_overlay, daemon=True)
        _overlay_thread.start()

        logger.success("Mic overlay started in background thread")

    except Exception as e:
        logger.error(f"Failed to start overlay: {e}")


def stop_overlay():
    """Stop the overlay if running."""
    global _overlay_instance
    if _overlay_instance:
        _overlay_instance.destroy()
        _overlay_instance = None
        logger.info("Mic overlay stopped")


def toggle_overlay():
    """Toggle overlay visibility."""
    global _overlay_instance
    if _overlay_instance:
        if _overlay_instance.visible:
            _overlay_instance.hide()
        else:
            _overlay_instance.show()