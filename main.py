import asyncio
from assistant import VitaweldAssistant

async def main():
    assistant = VitaweldAssistant()
    await assistant.talk()
    
if __name__ == "__main__":
    asyncio.run(main())
