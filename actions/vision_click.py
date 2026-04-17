import pyautogui
import os

def click_ui(target):
    """
    Attempts to locate and click a target element.
    In a real implementation, 'target' might route to specific templates (e.g., 'assets/{target}.png').
    """
    template_path = f"assets/{target.strip().lower()}.png"
    
    if not os.path.exists(template_path):
        return f"No template found for {target}."

    try:
        location = pyautogui.locateOnScreen(template_path, confidence=0.7)
        if location:
            pyautogui.click(location)
            return f"Clicked {target}"
    except Exception as e:
        return f"Error clicking UI: {str(e)}"
        
    return f"Could not see {target} on screen right now."
