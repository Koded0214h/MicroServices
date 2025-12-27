import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field
from enum import Enum
from typing import Optional

# Get the absolute path to the MicroServices/email_service directory
BASE_DIR = Path(__file__).resolve().parent

class EmailProvider(str, Enum):
    GMAIL = "gmail"
    RESEND = "resend"
    SES = "ses"
    SENDGRID = "sendgrid"

class Settings(BaseSettings):
    # Provider
    email_provider: EmailProvider = Field(default=EmailProvider.GMAIL)
    
    # SMTP
    smtp_host: str = Field(default="smtp.gmail.com")
    smtp_port: int = Field(default=465) # Changed default to 465 to match your .env
    smtp_username: str = Field(default="")
    smtp_password: str = Field(default="")
    smtp_from_name: str = Field(default="Scafld")
    smtp_from_email: str = Field(default="")
    smtp_use_tls: bool = Field(default=False) # TLS here usually means STARTTLS (587)
    smtp_use_ssl: bool = Field(default=True)  # SSL here usually means Implicit (465)
    smtp_timeout: int = Field(default=10)
    
    # Templates - Now uses Absolute Path
    template_dir: str = Field(default=str(BASE_DIR / "templates"))
    
    # Frontend URLs
    frontend_url: str = Field(default="https://app.scafld.com")
    verify_email_path: str = Field(default="/auth/verify-email")
    reset_password_path: str = Field(default="/auth/reset-password")
    onboarding_path: str = Field(default="/onboarding")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore" # Prevents errors if .env has extra vars

settings = Settings()