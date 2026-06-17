from langchain_anthropic import ChatAnthropic

def setup_environment(config):
    """Configure the model"""
    
    model = ChatAnthropic(
        model=config.MODEL,
        temperature=config.TEMPERATURE,
        max_tokens=config.MAX_TOKENS,
        timeout=config.TIMEOUT,
        max_retries=config.MAX_RETRIES,
        api_key=config.API_KEY
    )
    
    return model