from core.router import route as execute_tool
from loguru import logger
from ui.state import state, update_log

def execute_plan(plan):
    results = []
    
    steps = plan.get("steps", [])
    if steps:
        update_log(f"Executor received {len(steps)} planned steps.")

    for step in steps:
        action = step.get("action")
        args = step.get("args", {})

        logger.info(f"⚙️ {action} → {args}")
        state["last_action"] = f"{action} {args}"
        state["thought"] = f"Executing: {action}"
        update_log(f"Executing step action: {action}")
        state["error"] = ""

        try:
            result = execute_tool(action, args)
            logger.success(f"✅ {result}")
            update_log(f"Execution complete: {result}")
            results.append(result)
        except Exception as e:
            state["error"] = f"Tool failure: {str(e)}"
            logger.error(f"Execution logic crash: {e}")
            break

    return results
