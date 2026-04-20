"""
Permission system - gate critical actions by speaker identity.
Allows safe actions for anyone, but restricts dangerous operations to authorized users.
"""

from loguru import logger

# Only these speakers can execute critical/dangerous actions
AUTHORIZED_USERS = ["vaish"]

# Define what counts as a critical action
CRITICAL_ACTIONS = {
    "DELETE_FILE",
    "DELETE_FOLDER",
    "KILL_PROCESS",
    "SHUTDOWN",
    "RESTART",
    "UNINSTALL_PROGRAM",
    "MODIFY_SYSTEM_SETTINGS",
    "FORMAT_DRIVE",
}


def is_allowed(action: str, speaker: str) -> bool:
    """
    Check if speaker is allowed to perform action.
    
    Args:
        action: Action name/intent (e.g., "DELETE_FILE")
        speaker: Identified speaker name (e.g., "vaish", "unknown")
        
    Returns:
        True if allowed, False otherwise
    """
    # Unknown speakers cannot do anything critical
    if speaker == "unknown":
        if action in CRITICAL_ACTIONS:
            logger.warning(f"Denied critical action '{action}' to unknown speaker")
            return False
    
    # Only authorized users can do critical actions
    if action in CRITICAL_ACTIONS:
        if speaker not in AUTHORIZED_USERS:
            logger.warning(f"Denied critical action '{action}' to speaker '{speaker}'")
            return False
    
    # Safe actions allowed for everyone
    return True


def check_permission(intent: str, speaker: str) -> tuple:
    """
    Check permission and return (allowed, message).
    
    Args:
        intent: Action intent
        speaker: Identified speaker
        
    Returns:
        (allowed: bool, message: str)
    """
    if is_allowed(intent, speaker):
        return True, f"✓ Allowed for {speaker}"
    else:
        return False, f"Permission denied. Only {', '.join(AUTHORIZED_USERS)} can execute '{intent}'"


def add_authorized_user(name: str):
    """Add a user to authorized list (for future enrollment)."""
    if name not in AUTHORIZED_USERS:
        AUTHORIZED_USERS.append(name)
        logger.info(f"Added {name} to authorized users")


def remove_authorized_user(name: str):
    """Remove user from authorized list."""
    if name in AUTHORIZED_USERS:
        AUTHORIZED_USERS.remove(name)
        logger.info(f"Removed {name} from authorized users")


def get_authorized_users() -> list:
    """Return list of authorized users."""
    return AUTHORIZED_USERS.copy()
