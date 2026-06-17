"""Hello-world / basic demo for the VITAWELD Conversational AI Agent.

Runs the agent in the console with a single neutral example tool registered,
so that the tool-calling mechanism can be demonstrated without any industrial
hardware.

Prerequisites:
    * Dependencies installed (see ``requirements.txt``).
    * ``MODEL`` and ``API_KEY`` filled in the agent configuration
      (``config.py``).

Usage:
    $ python examples/hello_world.py

    Then try asking, for example: "What time is it?"
    The agent should decide to call ``get_current_time``, execute it, and
    report the result in natural language.

    Exit with: exit / quit / bye

Note:
    Import paths below assume the recommended ``src/vitaweld_agent/`` layout.
    Adjust them if your final repository structure differs.
"""

import asyncio
import sys
from pathlib import Path

# Ensure the project root is on sys.path so that the top-level ``src`` and
# ``examples`` packages can be imported when this file is run directly
# (``python examples/hello_world.py``).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.vitaweld_agent.assistant import VitaweldAssistant
from examples.example_tool import get_current_time, run_welding_cycle


async def main():
    assistant = VitaweldAssistant()

    # Register the example tool and rebuild the conversation graph so that the
    # tool is available both to the model (bind_tools) and to the execution
    # node (RayToolNode).
    assistant.tools = [get_current_time, run_welding_cycle]
    assistant.graph = assistant._create_graph()

    await assistant.talk()


if __name__ == "__main__":
    asyncio.run(main())
