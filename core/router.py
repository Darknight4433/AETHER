from actions.system import open_app, search_web, play_song
from datetime import datetime
from vision.screen import capture_screen
from vision.ocr import extract_text

def route(intent, text):
    if intent == "OPEN_APP":
        return open_app(text)

    elif intent == "SEARCH_WEB":
        return search_web(text)

    elif intent == "PLAY_SONG":
        return play_song(text)

    elif intent == "GET_TIME":
        return f"The time is {datetime.now().strftime('%I:%M %p')}"

    elif intent == "READ_SCREEN":
        img_path = capture_screen()
        text = extract_text(img_path)
        if text:
            # truncate context overload for ElevenLabs to speak
            return f"I can see the following on your screen: {text[:300]}" 
        return "I can't read any clear text on the screen right now."

    elif intent == "CLICK_UI":
        # Extract target from 'click the button'
        target = text.lower().replace("click", "").replace("the", "").strip()
        from actions.vision_click import click_ui
        return click_ui(target)

    return None
