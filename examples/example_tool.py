"""Neutral example tool for the VITAWELD Conversational AI Agent.

This tool is domain-neutral (no robot, welding or ROS 2 involved). Its only
purpose is to demonstrate the agent's tool-calling mechanism in the hello
world / basic demo, so that a reviewer can see *reasoning + action* without
any industrial hardware.

Tool-calling contract used by this repository
---------------------------------------------
* Tools are decorated with ``@ray.remote`` so the execution node
  (``RayToolNode``) can run them as Ray tasks. The node recovers the original
  function (and its ``__name__``) from the wrapper to bind it to the model.
* The single parameter MUST be named ``input_dict`` (not ``args``): LangChain
  treats a parameter literally named ``args`` as ``*args`` and would expose a
  bogus array schema to the model. The node unwraps the model's ``input_dict``
  and calls the tool with a single flat ``dict`` containing the model arguments
  plus the injected ``tool_call_id`` and ``thread_id`` keys.
* The return value must be JSON-serialisable (it is passed through
  ``json.dumps``), so returning a ``dict`` or a ``str`` is recommended.
"""

from datetime import datetime
import time
import ray


@ray.remote
def get_current_time(input_dict: dict = None) -> dict:
    """Return the current local date and time.

    Use this tool whenever the user asks what time or what date it is.
    This tool takes no input arguments.

    Returns:
        dict: the current date and time in ISO-8601 format and as a
        human-readable string.
    """
    now = datetime.now()
    return {
        "iso": now.isoformat(timespec="seconds"),
        "human_readable": now.strftime("%A, %d %B %Y, %H:%M:%S"),
    }


@ray.remote
def run_welding_cycle(input_dict: dict = None) -> dict:
    """Run a (simulated) long welding cycle on the workpiece.

    Use this tool when the user asks to weld a piece or to start a welding
    cycle/job. It represents a slow hardware action: it blocks for several
    seconds inside its Ray worker, but because tools are dispatched as Ray
    tasks the assistant stays free to keep chatting while it runs.

    The model may include a "piece" string (the workpiece identifier) and a
    "duration_seconds" integer (how long the cycle lasts, clamped to 1..120,
    default 15) in the call arguments.

    Returns:
        dict: a summary of the finished cycle (piece, duration and timestamps).
    """
    input_dict = input_dict or {}
    piece = input_dict.get("piece", "?")
    duration = input_dict.get("duration_seconds", 15)
    try:
        duration = int(duration)
    except (TypeError, ValueError):
        duration = 15
    duration = max(1, min(duration, 120))

    started_at = datetime.now()
    # Simulated hardware work. This runs in a Ray worker process, so it does
    # NOT block the assistant's event loop.
    time.sleep(duration)
    finished_at = datetime.now()

    return {
        "status": "completed",
        "piece": piece,
        "duration_seconds": duration,
        "started_at": started_at.isoformat(timespec="seconds"),
        "finished_at": finished_at.isoformat(timespec="seconds"),
        "message": f"Part welding cycle '{piece}' completed correctly.",
    }
