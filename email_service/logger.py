import structlog
import sys
import logging
from typing import Any, Dict


def setup_logger(level: str = "INFO") -> structlog.BoundLogger:
    """Configure structured logging"""
    
    # Remove existing handlers
    logging.basicConfig(level=level, format="%(message)s")
    
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    return structlog.get_logger("email_service")


# Create default logger
logger = setup_logger()