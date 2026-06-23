import os


class Settings:
    USE_OLLAMA = os.getenv("USE_OLLAMA", "false").lower() == "true"
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "agent-delivery-kpi")


settings = Settings()