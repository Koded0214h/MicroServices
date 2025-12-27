import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from email_service.service import EmailService
from email_service.core.schemas import EmailRequest, EmailRecipient

async def test_all_emails():
    """Test all email templates"""
    email_service = EmailService()
    
    tests = [
        {
            "name": "Verification Email",
            "template": "verify_email.html",
            "context": {
                "user": {"name": "Test User"},
                "verification_url": "https://app.scafld.dev/verify?token=test123"
            }
        },
        {
            "name": "Password Reset",
            "template": "reset_password.html",
            "context": {
                "user": {"name": "Test User"},
                "reset_url": "https://app.scafld.dev/reset?token=reset123",
                "expiration_hours": 1
            }
        },
        {
            "name": "Team Invite",
            "template": "invite_user.html",
            "context": {
                "inviter": {"name": "Team Admin"},
                "team": {"name": "Acme Corp"},
                "invite_url": "https://app.scafld.com/invite?token=invite123"
            }
        }
    ]
    
    for test in tests:
        print(f"\n📧 Testing: {test['name']}")
        
        email = EmailRequest(
            to=[EmailRecipient(email="test@example.com", name="Test User")],
            subject=f"Test: {test['name']}",
            template_name=test["template"],
            context=test["context"],
            category="test"
        )
        
        try:
            response = await email_service.send(email)
            print(f"✅ Success! Message ID: {response.message_id}")
        except Exception as e:
            print(f"❌ Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_all_emails())