import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.utils import formataddr, make_msgid, formatdate
from typing import List
import structlog
from datetime import datetime

from email_service.providers.base import EmailProvider
from email_service.core.schemas import EmailRequest, EmailResponse
from email_service.core.exceptions import EmailDeliveryError
from email_service.config import settings

logger = structlog.get_logger(__name__)

class GmailProvider(EmailProvider):
    """Gmail SMTP provider"""
    
    def __init__(self):
        self.host = settings.smtp_host
        self.port = settings.smtp_port
        self.username = settings.smtp_username
        self.password = settings.smtp_password
        self.timeout = settings.smtp_timeout
        self.from_email = settings.smtp_from_email
        self.from_name = settings.smtp_from_name
        
    @property
    def name(self) -> str:
        return "gmail"
    
    @property
    def max_recipients(self) -> int:
        return 100
    
    @property
    def rate_limit(self) -> int:
        return 500
    
    def validate_credentials(self) -> bool:
        return bool(self.username and self.password)
    
    def _create_message(self, email: EmailRequest) -> MIMEMultipart:
        msg = MIMEMultipart('alternative')
        msg['From'] = formataddr((self.from_name, self.from_email))
        msg['To'] = ', '.join([formataddr((r.name or '', r.email)) for r in email.to])
        
        if email.cc:
            msg['Cc'] = ', '.join([formataddr((r.name or '', r.email)) for r in email.cc])
        
        msg['Subject'] = email.subject
        msg['Date'] = formatdate(localtime=True)
        msg['Message-ID'] = make_msgid(domain='scafld.com')
        
        priority_map = {'high': '1', 'normal': '3', 'low': '5'}
        msg['X-Priority'] = priority_map.get(email.priority.value, '3')
        msg['X-Mailer'] = 'Scafld Email Service'
        
        if email.category:
            msg['X-Scafld-Category'] = email.category
        
        if email.text_body:
            msg.attach(MIMEText(email.text_body, 'plain', 'utf-8'))
        if email.html_body:
            msg.attach(MIMEText(email.html_body, 'html', 'utf-8'))
        
        for attachment in email.attachments:
            part = MIMEApplication(attachment.content, Name=attachment.filename)
            part['Content-Disposition'] = f'attachment; filename="{attachment.filename}"'
            part['Content-Type'] = attachment.content_type
            msg.attach(part)
        
        return msg
    
    async def send(self, email: EmailRequest) -> EmailResponse:
        """Send email via Gmail SMTP with dynamic SSL/TLS handling"""
        try:
            message = self._create_message(email)
            
            # 465 uses Implicit SSL (use_tls=True)
            # 587 uses STARTTLS (use_tls=False, then call .starttls())
            is_ssl = (self.port == 465)
            
            smtp_client = aiosmtplib.SMTP(
                hostname=self.host,
                port=self.port,
                use_tls=is_ssl,
                timeout=self.timeout
            )
            
            await smtp_client.connect()
            
            # If we are using port 587, we must upgrade to TLS manually
            if self.port == 587:
                await smtp_client.starttls()
            
            await smtp_client.login(self.username, self.password)
            
            all_recipients = [r.email for r in (email.to + email.cc + email.bcc)]
            
            await smtp_client.send_message(
                message,
                sender=self.from_email,
                recipients=all_recipients
            )
            
            await smtp_client.quit()
            
            message_id = message['Message-ID'].strip('<>')
            
            return EmailResponse(
                message_id=message_id,
                status="sent",
                provider=self.name,
                sent_at=datetime.utcnow()
            )
            
        except aiosmtplib.SMTPException as e:
            logger.error("SMTP error sending email", provider=self.name, error=str(e))
            raise EmailDeliveryError(f"SMTP error: {str(e)}")
        except Exception as e:
            logger.error("Unexpected error", provider=self.name, error=str(e))
            raise EmailDeliveryError(f"Failed to send email: {str(e)}")