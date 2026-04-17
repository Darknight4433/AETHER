import os
import webbrowser
import pywhatkit

def open_app(text):
    text = text.lower()
    if "chrome" in text:
        os.system("start chrome")
        return "Opening Chrome"

    if "notepad" in text:
        os.system("start notepad")
        return "Opening Notepad"

    return "App not recognized"

def search_web(text):
    text = text.lower()
    # Strip keywords
    query = text.replace("search for", "").replace("search", "").replace("google", "").strip()
    if not query:
        query = "news"
        
    url = f"https://www.google.com/search?q={query}"
    webbrowser.open(url)
    return f"Searching for {query}"

def play_song(text):
    text = text.lower()
    song = text.replace("play", "").replace("song", "").strip()
    if not song:
        song = "something random"
    
    # pywhatkit will automatically open youtube and click the first video
    pywhatkit.playonyt(song)
    return f"Playing {song}"
