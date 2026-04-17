import webbrowser

def open_url(url):
    webbrowser.open(url)
    return f"Opened {url}"

def search(query):
    webbrowser.open(f"https://www.google.com/search?q={query}")
    return f"🔎 Searching {query}"
