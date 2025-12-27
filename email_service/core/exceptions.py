"""
Custom exceptions for email service
"""

class EmailServiceError(Exception):
    """Base exception for email service errors"""
    pass


class EmailDeliveryError(EmailServiceError):
    """Raised when email delivery fails"""
    pass


class TemplateError(EmailServiceError):
    """Raised when template rendering fails"""
    pass


class ConfigurationError(EmailServiceError):
    """Raised when configuration is invalid"""
    pass


class RateLimitError(EmailServiceError):
    """Raised when rate limit is exceeded"""
    pass


class ValidationError(EmailServiceError):
    """Raised when email validation fails"""
    pass


class ProviderError(EmailServiceError):
    """Raised when email provider fails"""
    pass