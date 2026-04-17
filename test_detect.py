import time
from loguru import logger
from core.vision import VisionSystem

logger.info("Initializing Call Detect Test...")
vision_sys = VisionSystem(templates_dir="assets")

logger.info("Please have someone call you on WhatsApp Desktop (make sure it's visible!).")
logger.info("Waiting 30 seconds for a call...")

timeout = time.time() + 30
success = False

while time.time() < timeout:
    if vision_sys.detect_and_click_accept(confidence_threshold=0.75):
        logger.success("✅ Call detected and Accept button clicked successfully!")
        success = True
        break
    time.sleep(0.5)

if not success:
    logger.warning("❌ Timed out. No call detected in the last 30 seconds. Check the Accept button screenshot.")
