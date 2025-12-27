from pydantic import BaseModel, EmailStr, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum
import re


class EmailPriority(str, Enum):
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class EmailRecipient(BaseModel):
    email: EmailStr
    name: Optional[str] = None


class EmailAttachment(BaseModel):
    filename: str
    content: bytes
    content_type: str = "application/octet-stream"


class OnboardingContext(BaseModel):
    """Context specific to onboarding emails"""
    user_name: str
    user_email: str
    verification_token: Optional[str] = None
    invite_token: Optional[str] = None
    team_name: Optional[str] = None
    inviter_name: Optional[str] = None
    next_steps: List[str] = Field(default_factory=list)
    
    @validator('next_steps')
    def validate_next_steps(cls, v):
        """Limit next steps to 5 items max"""
        if len(v) > 5:
            return v[:5]
        return v


class EmailRequest(BaseModel):
    """Main email request model"""
    to: List[EmailRecipient]
    cc: List[EmailRecipient] = Field(default_factory=list)
    bcc: List[EmailRecipient] = Field(default_factory=list)
    subject: str
    template_name: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    priority: EmailPriority = EmailPriority.NORMAL
    attachments: List[EmailAttachment] = Field(default_factory=list)
    
    # Direct content (alternative to templates)
    html_body: Optional[str] = None
    text_body: Optional[str] = None
    
    # Tracking
    category: Optional[str] = None  # "onboarding", "verification", "invite"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('subject')
    def validate_subject(cls, v):
        """Prevent spammy subjects"""
        v = v.strip()
        if len(v) > 150:
            raise ValueError("Subject too long")
        
        # Check for spam triggers
        spam_triggers = ['!!!', 'FREE', 'WINNER', 'URGENT', 'ACT NOW']
        if any(trigger in v.upper() for trigger in spam_triggers):
            raise ValueError("Subject contains spam triggers")
        
        return v
    
    @validator('to')
    def validate_recipients(cls, v):
        """Limit recipients"""
        if len(v) > 50:
            raise ValueError("Too many recipients")
        return v


class EmailResponse(BaseModel):
    """Response after sending email"""
    message_id: str
    status: str
    provider: str
    sent_at: datetime


class EmailStats(BaseModel):
    """Email statistics"""
    sent_today: int = 0
    sent_total: int = 0
    failed_today: int = 0
    by_category: Dict[str, int] = Field(default_factory=dict)