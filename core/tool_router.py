from actions.filesystem import create_file, read_file
from actions.processes import open_app
from actions.web import search
from actions.system_controls import screenshot
from core.safety_guard import is_action_allowed
from core.memory_engine import log_action
from core.preferences import set_preference

def execute_tool(action, args):
    if not is_action_allowed(action):
        return "❌ Action blocked"
        
    # Log memory action context (Phase 15 Tracker)
    log_action(action, args)
        
    if action == "CREATE_FILE":
        return create_file(args.get("name"), args.get("content", ""))
    if action == "READ_FILE":
        return read_file(args.get("name"))
    if action == "OPEN_APP":
        return open_app(args.get("app"))
    if action == "SEARCH_WEB":
        return search(args.get("query"))
    if action == "TAKE_SCREENSHOT":
        return screenshot()
    if action == "PLAY_SONG":
        song = args.get("song")
        if song:
            set_preference("favorite_song", song)
        from actions.system import play_song
        return play_song(song)
        
    return "❌ Unknown action"
