"""
Scafld Email Service
A production-grade email service for microservices
"""

__version__ = "1.0.0"
__author__ = "Scafld Team"
__email__ = "scafldhq@gmail.com"

from email_service.service import EmailService
from email_service.core.schemas import (
    EmailRequest,
    EmailRecipient,
    EmailResponse,
    OnboardingContext,
    EmailStats
)
from email_service.core.exceptions import (
    EmailServiceError,
    EmailDeliveryError,
    TemplateError,
    ConfigurationError
)

__all__ = [
    "EmailService",
    "EmailRequest",
    "EmailRecipient",
    "EmailResponse",
    "OnboardingContext",
    "EmailStats",
    "EmailServiceError",
    "EmailDeliveryError",
    "TemplateError",
    "ConfigurationError",
]