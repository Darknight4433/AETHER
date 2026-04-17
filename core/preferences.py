from core.memory_engine import load_memory, save_memory

def set_preference(key, value):
    data = load_memory()
    data.setdefault("preferences", {})
    data["preferences"][key] = value
    save_memory(data)

def get_preference(key):
    data = load_memory()
    return data.get("preferences", {}).get(key)
