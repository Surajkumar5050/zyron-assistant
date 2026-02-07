from dotenv import load_dotenv
import os
from pydantic_settings import BaseSettings
load_dotenv()


class Settings(BaseSettings):
    MEDIA_PATH: str = os.getenv("MEDIA_PATH", "saved_media")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "qwen2.5-coder:7b")
    OFFLINE_MODE: bool = os.getenv("OFFLINE_MODE", "false").lower() == "true"

settings = Settings()