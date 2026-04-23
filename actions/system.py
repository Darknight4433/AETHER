import os
import webbrowser


def _start_command(target):
    os.system(f'start "" "{target}"')

def open_app(text):
    text = (text or "").lower()
    if "chrome" in text:
        _start_command("chrome")
        return "Opening Chrome"

    if "notepad" in text:
        _start_command("notepad")
        return "Opening Notepad"

    return "App not recognized"

def search_web(text):
    text = (text or "").lower()
    # Strip keywords
    query = text.replace("search for", "").replace("search", "").replace("google", "").strip()
    if not query:
        query = "news"
        
    url = f"https://www.google.com/search?q={query}"
    webbrowser.open(url)
    return f"Searching for {query}"

def play_song(text):
    text = (text or "").lower()
    song = text.replace("play", "").replace("song", "").strip()
    if not song:
        song = "something random"
    
    try:
        import pywhatkit
        pywhatkit.playonyt(song)
    except Exception:
        query = song.replace(" ", "+")
        webbrowser.open(f"https://www.youtube.com/results?search_query={query}")
    return f"Playing {song}"
