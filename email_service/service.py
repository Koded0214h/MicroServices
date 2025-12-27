from typing import Dict, Any, Optional, List
import structlog
from datetime import datetime, timedelta

from email_service.core.schemas import (
    EmailRequest, EmailResponse, EmailRecipient, 
    OnboardingContext, EmailStats
)
from email_service.core.exceptions import EmailDeliveryError
from email_service.providers.gmail import GmailProvider
from email_service.providers.base import EmailProvider
from email_service.renderer.jinja2_renderer import Jinja2Renderer
from email_service.config import settings, EmailProvider as ProviderEnum
from email_service.logger import logger


class EmailService:
    """Main email service orchestrator"""
    
    def __init__(self):
        self.provider = self._get_provider()
        self.renderer = Jinja2Renderer(settings.template_dir)
        self._logs: List[Dict[str, Any]] = []
        self._sent_count = 0
        self._failed_count = 0
        
        logger.info("Email service initialized", 
                   provider=self.provider.name)
    
    def _get_provider(self) -> EmailProvider:
        """Initialize the configured provider"""
        if settings.email_provider == ProviderEnum.GMAIL:
            return GmailProvider()
        else:
            raise ValueError(f"Unsupported provider: {settings.email_provider}")
    
    def prepare_email(self, email: EmailRequest) -> EmailRequest:
        """Prepare email with rendered templates"""
        if not email.template_name:
            # Direct email, ensure we have at least text body
            if not email.text_body and email.html_body:
                # Create text version from HTML
                email.text_body = self.renderer._html_to_text(email.html_body)
            return email
        
        # Render templates
        if not email.html_body:
            email.html_body = self.renderer.render_html(
                email.template_name,
                email.context
            )
        
        if not email.text_body:
            try:
                email.text_body = self.renderer.render_text(
                    email.template_name,
                    email.context
                )
            except Exception as e:
                logger.warning("Failed to render text template, using HTML fallback",
                             error=str(e))
                email.text_body = self.renderer._html_to_text(email.html_body)
        
        return email
    
    async def send(self, email: EmailRequest) -> EmailResponse:
        """Send an email"""
        start_time = datetime.utcnow()
        
        try:
            # Prepare email with templates
            prepared_email = self.prepare_email(email)
            
            # Validate before sending
            self._validate_email(prepared_email)
            
            # Send via provider
            response = await self.provider.send(prepared_email)
            
            # Log success
            self._log_email(prepared_email, response, None, start_time)
            self._sent_count += 1
            
            logger.info("Email sent successfully",
                       message_id=response.message_id,
                       category=email.category,
                       duration=(datetime.utcnow() - start_time).total_seconds())
            
            return response
            
        except Exception as e:
            # Log failure
            self._log_email(email, None, str(e), start_time)
            self._failed_count += 1
            
            logger.error("Email delivery failed",
                        error=str(e),
                        category=email.category)
            raise EmailDeliveryError(f"Failed to send email: {str(e)}")
    
    def _validate_email(self, email: EmailRequest):
        """Validate email before sending"""
        if not email.to:
            raise ValueError("No recipients specified")
        
        if not email.subject:
            raise ValueError("No subject specified")
        
        if not email.html_body and not email.text_body:
            raise ValueError("No email content specified")
    
    def _log_email(self, email: EmailRequest, response: Optional[EmailResponse], 
                  error: Optional[str], start_time: datetime):
        """Log email attempt"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "start_time": start_time.isoformat(),
            "recipients": [r.email for r in email.to],
            "subject": email.subject[:100],  # Truncate long subjects
            "category": email.category,
            "status": "sent" if response else "failed",
            "provider": self.provider.name,
            "message_id": response.message_id if response else None,
            "error": error,
            "duration_seconds": (datetime.utcnow() - start_time).total_seconds()
        }
        
        self._logs.append(log_entry)
    
    # ========== ONBOARDING EMAILS ==========
    
    async def send_welcome_email(self, user_email: str, user_name: str, 
                                verification_token: Optional[str] = None) -> EmailResponse:
        """Send welcome/verification email to new user"""
        context = {
            "user": {
                "name": user_name,
                "email": user_email
            },
            "verification_url": self._build_verification_url(verification_token),
            "onboarding_url": f"{settings.frontend_url}{settings.onboarding_path}",
            "next_steps": [
                "Complete your profile",
                "Connect your first repository",
                "Create your first scaffold"
            ]
        }
        
        email = EmailRequest(
            to=[EmailRecipient(email=user_email, name=user_name)],
            subject=f"Welcome to Scafld, {user_name}! 🎉",
            template_name="welcome.html",
            context=context,
            category="onboarding_welcome"
        )
        
        return await self.send(email)
    
    async def send_verification_email(self, user_email: str, user_name: str, 
                                     verification_token: str) -> EmailResponse:
        """Send email verification link"""
        context = {
            "user": {
                "name": user_name,
                "email": user_email
            },
            "verification_url": self._build_verification_url(verification_token)
        }
        
        email = EmailRequest(
            to=[EmailRecipient(email=user_email, name=user_name)],
            subject="Verify your Scafld email address",
            template_name="verify_email.html",
            context=context,
            category="verification"
        )
        
        return await self.send(email)
    
    async def send_invite_email(self, invitee_email: str, invitee_name: Optional[str],
                               inviter_name: str, team_name: str, 
                               invite_token: str) -> EmailResponse:
        """Send team invitation email"""
        context = {
            "invitee": {
                "name": invitee_name or "",
                "email": invitee_email
            },
            "inviter": {
                "name": inviter_name
            },
            "team": {
                "name": team_name
            },
            "invite_url": f"{settings.frontend_url}/invite/{invite_token}"
        }
        
        subject = f"{inviter_name} invited you to join {team_name} on Scafld"
        
        email = EmailRequest(
            to=[EmailRecipient(email=invitee_email, name=invitee_name)],
            subject=subject,
            template_name="invite_user.html",
            context=context,
            category="invite"
        )
        
        return await self.send(email)
    
    def _build_verification_url(self, token: Optional[str]) -> str:
        """Build verification URL"""
        if not token:
            return f"{settings.frontend_url}{settings.onboarding_path}"
        return f"{settings.frontend_url}{settings.verify_email_path}?token={token}"
    
    # ========== STATISTICS ==========
    
    def get_stats(self) -> EmailStats:
        """Get email service statistics"""
        today = datetime.utcnow().date()
        
        sent_today = len([
            log for log in self._logs
            if log['status'] == 'sent' and 
            datetime.fromisoformat(log['timestamp']).date() == today
        ])
        
        failed_today = len([
            log for log in self._logs
            if log['status'] == 'failed' and 
            datetime.fromisoformat(log['timestamp']).date() == today
        ])
        
        # Group by category
        by_category = {}
        for log in self._logs:
            if log['category']:
                by_category[log['category']] = by_category.get(log['category'], 0) + 1
        
        return EmailStats(
            sent_today=sent_today,
            sent_total=self._sent_count,
            failed_today=failed_today,
            by_category=by_category
        )
    
    def get_recent_logs(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent email logs"""
        return self._logs[-limit:] if self._logs else []