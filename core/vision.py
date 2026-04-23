import cv2
import mss
import numpy as np
import pyautogui
import time
from loguru import logger
import os

class VisionSystem:
    def __init__(self, templates_dir="assets"):
        self.sct = mss.mss()
        self.templates_dir = templates_dir
        os.makedirs(self.templates_dir, exist_ok=True)
        # ROI for WhatsApp call buttons (bottom right quadrant typically)
        self.roi = {"top": 400, "left": 1000, "width": 920, "height": 680} 
        
        # We need a screenshot of the WhatsApp "Accept" button
        self.accept_template_path = os.path.join(templates_dir, "accept_button.png")
        
        if not os.path.exists(self.accept_template_path):
            logger.warning(f"Template {self.accept_template_path} not found. You need to capture a screenshot of the WhatsApp 'Accept' button to use call detection.")
            self.accept_template = None
        else:
            self.accept_template = cv2.imread(self.accept_template_path, cv2.IMREAD_COLOR)
            if self.accept_template is None:
                logger.error(f"Could not load template from {self.accept_template_path}")

        self.end_call_template_path = os.path.join(templates_dir, "end_call.png")
        if not os.path.exists(self.end_call_template_path):
            logger.warning(f"Template {self.end_call_template_path} not found. Taking a screenshot of the red 'End Call/Decline' button is required for call-end detection.")
            self.end_call_template = None
        else:
            self.end_call_template = cv2.imread(self.end_call_template_path, cv2.IMREAD_COLOR)

    def capture_screen(self, use_roi=True):
        """Captures the screen or a specific region of interest."""
        monitor = self.sct.monitors[1]
        if use_roi:
            # Shift ROI relative to monitor
            capture_area = {
                "top": monitor["top"] + self.roi["top"],
                "left": monitor["left"] + self.roi["left"],
                "width": self.roi["width"],
                "height": self.roi["height"]
            }
        else:
            capture_area = monitor

        screenshot = self.sct.grab(capture_area)
        img = np.array(screenshot)
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        return img, capture_area

    def detect_and_click_accept(self, confidence_threshold=0.75):
        """
        Scans the screen for the WhatsApp Accept button template.
        If found with sufficient confidence, clicks it.
        """
        if self.accept_template is None:
            return False

        screen_img, monitor = self.capture_screen()
        
        # Template matching
        result = cv2.matchTemplate(screen_img, self.accept_template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if max_val >= confidence_threshold:
            logger.info(f"Incoming call detected! Confidence: {max_val:.2f}")
            
            # Calculate center of the matched region
            h, w = self.accept_template.shape[:-1]
            center_x = max_loc[0] + w // 2 + monitor['left']
            center_y = max_loc[1] + h // 2 + monitor['top']
            
            # Click the accept button
            logger.info(f"Clicking Accept at ({center_x}, {center_y})")
            pyautogui.moveTo(center_x, center_y, duration=0.2)
            pyautogui.click()
            time.sleep(1) # Wait for call animation
            return True
            
        return False

    def detect_call_loop(self, check_interval=0.8, confidence=0.75):
        """Blocking loop that waits for an incoming call."""
        logger.info("Vision system active. Scanning for incoming calls...")
        while True:
            if self.detect_and_click_accept(confidence):
                return True
            time.sleep(check_interval)

    def is_call_active(self, confidence_threshold=0.75):
        """Checks if the end call button is visible. If template missing, defaults to True."""
        if self.end_call_template is None:
            return True # Fallback if user hasn't setup template yet

        screen_img, _ = self.capture_screen()
        result = cv2.matchTemplate(screen_img, self.end_call_template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        return max_val >= confidence_threshold
