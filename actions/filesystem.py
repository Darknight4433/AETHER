import os
from core.safety_guard import BASE_DIR, is_path_safe, ensure_base

ensure_base()

def create_file(name, content=""):
    path = os.path.join(BASE_DIR, name)
    if not is_path_safe(path):
        return "❌ Unsafe path"
    with open(path, "w") as f:
        f.write(content)
    return f"📄 Created {name}"

def read_file(name):
    path = os.path.join(BASE_DIR, name)
    if not os.path.exists(path):
        return "❌ File not found"
    with open(path, "r") as f:
        return f.read()[:500]
