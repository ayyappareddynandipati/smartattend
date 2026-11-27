import os

from dotenv import load_dotenv
from pydantic import BaseConfig

# Load backend/.env before settings are read (see backend/.env.example)
load_dotenv()


class Settings(BaseConfig):
    PROJECT_NAME: str = "Attendance System"
    API_V1_STR: str = "/api/v1"
    # Set SECRET_KEY in backend/.env; the fallback is for local development only
    SECRET_KEY: str = os.getenv("SECRET_KEY") or "YOUR_SUPER_SECRET_KEY_CHANGE_ME"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Simple way to get settings
    class Config:
        case_sensitive = True


settings = Settings()
