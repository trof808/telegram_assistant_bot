from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    TELEGRAM_BOT_TOKEN: str
    WEBHOOK_URL: str = ""
    GIGACHAT_API_KEY: str
    
    # Settings for Local LLM (e.g., Ollama)
    OLLAMA_BASE_URL: str = "http://88.218.170.42:11434"
    LOCAL_LLM_MODEL_NAME: str = "gemma3:1b" # Default to mistral, user can change in .env
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()