from core.safety import is_safe
from loguru import logger
import os

# Define base directory for filesystem operations
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

def ensure_base():
    """Ensure data directory exists."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def is_path_safe(path):
    """Ensure path is within the allowed workspace."""
    abs_path = os.path.abspath(path)
    return abs_path.startswith(BASE_DIR)

def is_action_allowed(action):
    """Check if the specific tool action is authorized."""
    # For now, we trust the intent classifier and use the keyword filter
    return True 

def authorize(intent, user_text):
    """
    Single entry point for all safety and permission checks.
    Centralizing this prevents duplicate checks across the conversation loop and router.
    """
    # 1. Semantic keyword safety check
    if not is_safe(user_text):
        logger.warning(f"Safety violation blocked: {user_text}")
        return False, "I'm sorry, I cannot perform that action as it is restricted for safety reasons."
    
    # 2. Add further permission or intent-based logic here if needed
    # for example, checking speaker ID from core.permissions
    
    return True, None
