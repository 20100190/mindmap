import os
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path="/Users/usman/Downloads/0.DataScience/portfolio/mindmap/.env")


class DatabaseConfig(BaseModel):
    url: str = os.getenv("DATABASE_URL", "postgresql://localhost/mindmap")
    echo: bool = os.getenv("DB_ECHO", "false").lower() == "true"


class LLMConfig(BaseModel):
    api_key: str = os.getenv("OPENAI_API_KEY", "")
    base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    model: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    max_retries: int = int(os.getenv("OPENAI_MAX_RETRIES", "3"))
    temperature: float = float(os.getenv("OPENAI_TEMPERATURE", "0.3"))
    timeout: int = int(os.getenv("OPENAI_TIMEOUT", "100"))
    max_function_calls: int = int(os.getenv("MAX_FUNCTION_CALLS", "10"))


class GCSConfig(BaseModel):
    bucket_name: str = os.getenv("GCS_BUCKET_NAME", "")
    credentials_path: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")


class AppConfig(BaseModel):
    database: DatabaseConfig = DatabaseConfig()
    llm: LLMConfig = LLMConfig()
    gcs: GCSConfig = GCSConfig()
    log_level: str = os.getenv("LOG_LEVEL", "INFO")


# Global config instance
config = AppConfig()