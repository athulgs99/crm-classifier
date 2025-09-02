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

settings = Settings()
