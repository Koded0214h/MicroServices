"""
Constants for email service
"""

# Email categories
EMAIL_CATEGORIES = {
    "ONBOARDING": "onboarding",
    "VERIFICATION": "verification",
    "INVITE": "invite",
    "NOTIFICATION": "notification",
    "ALERT": "alert",
    "MARKETING": "marketing",
    "TRANSACTIONAL": "transactional",
}

# Default settings
DEFAULT_SMTP_PORT = 587
DEFAULT_SMTP_TIMEOUT = 30
DEFAULT_RATE_LIMIT = 100  # emails per hour
MAX_RECIPIENTS_PER_EMAIL = 50
MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024  # 10MB

# Template constants
DEFAULT_TEMPLATE_DIR = "email_service/templates"
HTML_CONTENT_TYPE = "text/html; charset=utf-8"
TEXT_CONTENT_TYPE = "text/plain; charset=utf-8"

# Headers
HEADER_PRIORITY_HIGH = "1 (Highest)"
HEADER_PRIORITY_NORMAL = "3 (Normal)"
HEADER_PRIORITY_LOW = "5 (Lowest)"

# Validation patterns
EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'