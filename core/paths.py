import os
import sys


APP_NAME = "Aether"


def get_bundle_root():
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_install_root():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_data_root():
    candidates = []

    appdata = os.getenv("APPDATA")
    if appdata:
        candidates.append(os.path.join(appdata, APP_NAME))

    candidates.append(os.path.join(get_install_root(), "data"))

    for root in candidates:
        try:
            os.makedirs(root, exist_ok=True)
            test_path = os.path.join(root, ".write_test")
            with open(test_path, "w", encoding="utf-8") as handle:
                handle.write("ok")
            return root
        except OSError:
            continue

    raise PermissionError(
        f"Unable to create a writable data directory for {APP_NAME}."
    )


def resource_path(*parts):
    return os.path.join(get_bundle_root(), *parts)


def install_path(*parts):
    return os.path.join(get_install_root(), *parts)


def data_path(*parts):
    return os.path.join(get_data_root(), *parts)
