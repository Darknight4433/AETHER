from copy import deepcopy

from core.preferences import get_preference, set_preference


DEFAULT_POPUP_SETTINGS = {
    "state_colors": {
        "idle": "#22c55e",
        "listening": "#38bdf8",
        "thinking": "#ef4444",
        "speaking": "#2563eb",
    },
    "surface_tint": "#09111f",
    "accent": "#8b5cf6",
}


def _normalize_settings(settings):
    merged = deepcopy(DEFAULT_POPUP_SETTINGS)
    if not isinstance(settings, dict):
        return merged

    state_colors = settings.get("state_colors", {})
    if isinstance(state_colors, dict):
        merged["state_colors"].update(
            {
                key: value
                for key, value in state_colors.items()
                if key in merged["state_colors"] and isinstance(value, str) and value
            }
        )

    for key in ("surface_tint", "accent"):
        value = settings.get(key)
        if isinstance(value, str) and value:
            merged[key] = value

    return merged


def get_popup_settings():
    return _normalize_settings(get_preference("popup_settings"))


def save_popup_settings(settings):
    normalized = _normalize_settings(settings)
    set_preference("popup_settings", normalized)
    return normalized


def update_popup_settings(patch):
    current = get_popup_settings()
    if not isinstance(patch, dict):
        return current

    if isinstance(patch.get("state_colors"), dict):
        current["state_colors"].update(patch["state_colors"])

    for key in ("surface_tint", "accent"):
        value = patch.get(key)
        if isinstance(value, str) and value:
            current[key] = value

    return save_popup_settings(current)


def reset_popup_settings():
    return save_popup_settings(DEFAULT_POPUP_SETTINGS)


def get_status_color(status):
    settings = get_popup_settings()
    return settings["state_colors"].get(status, settings["state_colors"]["idle"])
