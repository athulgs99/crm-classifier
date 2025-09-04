import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # LLM Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    
    # Email Configuration
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    EMAIL_USERNAME = os.getenv("EMAIL_USERNAME")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
    MANAGER_EMAIL = os.getenv("MANAGER_EMAIL")
    
    # Application Settings
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this")
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    
    # SLA Configuration
    SLA_THRESHOLDS = {
        "P1": 2,    # 2 hours
        "P2": 4,    # 4 hours
        "P3": 24,   # 24 hours
        "P4": 48    # 48 hours
    }
    
    # GitHub Configuration
    GITHUB_REPO = "microsoft/vscode"  # Default repo for sample issues
    
    # Agent Configuration
    ENABLE_LEARNING = os.getenv("ENABLE_LEARNING", "True").lower() == "true"
    ENABLE_RESPONSE_PROCESSING = os.getenv("ENABLE_RESPONSE_PROCESSING", "True").lower() == "true"
    LEARNING_THRESHOLD = float(os.getenv("LEARNING_THRESHOLD", "0.7"))
    MIN_SAMPLES_FOR_LEARNING = int(os.getenv("MIN_SAMPLES_FOR_LEARNING", "10"))
    
    # Knowledge Base Configuration
    KNOWLEDGE_DB_PATH = os.getenv("KNOWLEDGE_DB_PATH", "database/knowledge.db")
    KNOWLEDGE_CLEANUP_DAYS = int(os.getenv("KNOWLEDGE_CLEANUP_DAYS", "90"))
    
    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    ENABLE_STRUCTURED_LOGGING = os.getenv("ENABLE_STRUCTURED_LOGGING", "True").lower() == "true"

settings = Settings()
