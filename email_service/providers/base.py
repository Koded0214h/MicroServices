from abc import ABC, abstractmethod
from typing import Optional
from email_service.core.schemas import EmailRequest, EmailResponse


class EmailProvider(ABC):
    """Abstract base class for all email providers"""
    
    @abstractmethod
    async def send(self, email: EmailRequest) -> EmailResponse:
        """Send an email"""
        pass
    
    @abstractmethod
    def validate_credentials(self) -> bool:
        """Validate provider credentials"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name"""
        pass
    
    @property
    @abstractmethod
    def max_recipients(self) -> int:
        """Maximum recipients per email"""
        pass
    
    @property
    @abstractmethod
    def rate_limit(self) -> int:
        """Rate limit per day"""
        pass