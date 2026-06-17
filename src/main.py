import asyncio
import sys
from pathlib import Path

# Ensure the project root is on sys.path so the top-level ``src`` package can be
# imported when this file is run directly (``python src/main.py``).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.vitaweld_agent.assistant import VitaweldAssistant

async def main():
    assistant = VitaweldAssistant()
    await assistant.talk()
    
if __name__ == "__main__":
    asyncio.run(main())
