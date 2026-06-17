from langgraph.checkpoint.memory import MemorySaver

class Config:
    # Model configuration
    MODEL = "" # your model name or version
    TEMPERATURE = 0.5
    MAX_TOKENS = 1024
    TIMEOUT = None
    MAX_RETRIES = 2
    API_KEY = "" # your API key

    SYSTEM_PROMPT = """The assistant's behavioural instructions"""

    
    # Graph configuration
    CONFIG = {"configurable": {"thread_id": "1"}}

    # Memory configuration
    MEMORY = MemorySaver()