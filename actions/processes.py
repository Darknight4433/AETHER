import os

def open_app(app):
    app = app.lower()
    if "chrome" in app:
        os.system("start chrome")
        return "🌐 Chrome opened"
    if "notepad" in app:
        os.system("start notepad")
        return "📝 Notepad opened"
    return "❌ App not recognized"
