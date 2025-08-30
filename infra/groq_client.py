"""
Groq client implemented using the langchain-groq wrapper.
"""
import os
from typing import List, Dict
from langchain_groq import ChatGroq

# Fetch API key and model from environment variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DEFAULT_MODEL = os.getenv("GROQ_MODEL", "llama3-8b-8192")

def get_groq_chat_client(api_key: str = None, model: str = None) -> ChatGroq:
    """Initializes and returns a ChatGroq client."""
    api_key = api_key or GROQ_API_KEY
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is not set.")
    
    model_name = model or DEFAULT_MODEL
    return ChatGroq(temperature=0, groq_api_key=api_key, model_name=model_name)

# Global client instance for convenience
groq_chat_client = get_groq_chat_client()