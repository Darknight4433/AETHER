import os

from core.safety_guard import BASE_DIR, ensure_base, is_path_safe

ensure_base()


def create_file(name, content=""):
    path = os.path.join(BASE_DIR, name)
    if not is_path_safe(path):
        return "Unsafe path"

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Created {name}"


def read_file(name):
    path = os.path.join(BASE_DIR, name)
    if not is_path_safe(path):
        return "Unsafe path"
    if not os.path.exists(path):
        return "File not found"

    with open(path, "r", encoding="utf-8") as f:
        return f.read()[:500]
