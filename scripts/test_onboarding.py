#!/usr/bin/env python3
"""
Test onboarding emails for Scafld
"""
import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from email_service.service import EmailService
from email_service.core.schemas import EmailRecipient, EmailRequest
from email_service.core.exceptions import EmailDeliveryError


def create_test_templates():
    """Create minimal test templates if they don't exist"""
    templates_dir = Path(__file__).parent.parent / "email_service" / "templates"
    templates_dir.mkdir(exist_ok=True)
    
    # Create base.html
    base_html = templates_dir / "base.html"
    if not base_html.exists():
        base_html.write_text("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; }
        .container { max-width: 600px; margin: 0 auto; }
        .header { background: #7C3AED; color: white; padding: 20px; }
        .content { padding: 20px; }
        .button { background: #7C3AED; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; }
        .footer { padding: 20px; background: #F3F4F6; }
    </style>
</head>
<body>
    <div class="container">
        {% block content %}{% endblock %}
    </div>
</body>
</html>
        """)
    
    # Create welcome.html
    welcome_html = templates_dir / "welcome.html"
    if not welcome_html.exists():
        welcome_html.write_text("""
{% extends "base.html" %}

{% block content %}
<div class="header">
    <h1>Welcome to Scafld, {{ user.name }}! 🎉</h1>
</div>
<div class="content">
    <p>We're excited to have you on board!</p>
    {% if verification_url %}
    <p>Please verify your email:</p>
    <p><a href="{{ verification_url }}" class="button">Verify Email</a></p>
    {% endif %}
    
    <h2>Getting Started:</h2>
    <ul>
        {% for step in next_steps %}
        <li>{{ step }}</li>
        {% endfor %}
    </ul>
    
    <p>Best regards,<br>The Scafld Team</p>
</div>
<div class="footer">
    <p>Need help? Contact us at support@scafld.com</p>
</div>
{% endblock %}
        """)
    
    # Create verify_email.html
    verify_html = templates_dir / "verify_email.html"
    if not verify_html.exists():
        verify_html.write_text("""
{% extends "base.html" %}

{% block content %}
<div class="content">
    <h1>Verify Your Email</h1>
    <p>Hello {{ user.name }},</p>
    <p>Please verify your email address by clicking the link below:</p>
    <p><a href="{{ verification_url }}" class="button">Verify Email Address</a></p>
    <p>Or copy this link:<br><code>{{ verification_url }}</code></p>
    <p>This link expires in 24 hours.</p>
</div>
{% endblock %}
        """)
    
    # Create plain_text directory
    plain_text_dir = templates_dir / "plain_text"
    plain_text_dir.mkdir(exist_ok=True)
    
    # Create welcome.txt
    welcome_txt = plain_text_dir / "welcome.txt"
    if not welcome_txt.exists():
        welcome_txt.write_text("""Welcome to Scafld, {{ user.name }}! 🎉

We're excited to have you on board.

{% if verification_url %}
Please verify your email:
{{ verification_url }}
{% endif %}

Getting Started:
{% for step in next_steps %}
- {{ step }}
{% endfor %}

Best regards,
The Scafld Team
""")
    
    # Create verify_email.txt
    verify_txt = plain_text_dir / "verify_email.txt"
    if not verify_txt.exists():
        verify_txt.write_text("""Verify Your Email

Hello {{ user.name }},

Please verify your email address:
{{ verification_url }}

This link expires in 24 hours.

Best regards,
The Scafld Team
""")


async def test_onboarding_emails():
    """Test all onboarding-related emails"""
    print("🚀 Testing Scafld Onboarding Emails")
    print("=" * 50)
    
    # Create test templates if they don't exist
    create_test_templates()
    
    # Initialize service
    try:
        service = EmailService()
        print("✅ Email service initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize email service: {e}")
        print("\nMake sure you have a .env file with:")
        print("SMTP_USERNAME=your_email@gmail.com")
        print("SMTP_PASSWORD=your_app_password")
        print("SMTP_FROM_EMAIL=your_email@gmail.com")
        return
    
    test_email = os.getenv("TEST_EMAIL", "coder0214h@gmail.com")
    test_name = "Alex Developer"
    
    tests = [
        {
            "name": "Welcome Email with Verification",
            "func": service.send_welcome_email,
            "args": [test_email, test_name, "test_token_123"],
            "desc": "Full welcome email with verification"
        },
        {
            "name": "Welcome Email (no verification)",
            "func": service.send_welcome_email,
            "args": [test_email, test_name, None],
            "desc": "Welcome email without verification token"
        },
        {
            "name": "Verification Email",
            "func": service.send_verification_email,
            "args": [test_email, test_name, "verify_token_456"],
            "desc": "Email verification only"
        },
    ]
    
    # Also test direct email sending (no template)
    print("\n4. Testing Direct Email (No Template)")
    print("   Direct email without template")
    print(f"   To: {test_email}")
    
    try:
        direct_email = EmailRequest(
            to=[EmailRecipient(email=test_email, name=test_name)],
            subject="Test Direct Email from Scafld",
            html_body="<h1>Hello!</h1><p>This is a direct email test.</p>",
            text_body="Hello!\nThis is a direct email test.",
            category="test"
        )
        response = await service.send(direct_email)
        print(f"   ✅ Success! Message ID: {response.message_id}")
    except Exception as e:
        print(f"   ❌ Failed: {str(e)}")
    
    # Run the template-based tests
    for i, test in enumerate(tests, 1):
        print(f"\n{i}. Testing: {test['name']}")
        print(f"   {test['desc']}")
        print(f"   To: {test_email}")
        
        try:
            response = await test['func'](*test['args'])
            print(f"   ✅ Success! Message ID: {response.message_id}")
        except EmailDeliveryError as e:
            print(f"   ❌ Delivery failed: {str(e)}")
            print(f"     Check your SMTP credentials and internet connection")
        except Exception as e:
            print(f"   ❌ Unexpected error: {str(e)}")
    
    # Show statistics
    print("\n" + "=" * 50)
    stats = service.get_stats()
    print(f"\n📊 Email Statistics:")
    print(f"   Sent today: {stats.sent_today}")
    print(f"   Total sent: {stats.sent_total}")
    print(f"   Failed today: {stats.failed_today}")
    
    if stats.by_category:
        print(f"   By category:")
        for category, count in stats.by_category.items():
            print(f"     - {category}: {count}")
    
    # Show recent logs
    print(f"\n📋 Recent Logs (last 5):")
    logs = service.get_recent_logs(5)
    for log in logs:
        status_icon = "✅" if log['status'] == 'sent' else "❌"
        subject = log.get('subject', 'No subject')
        if len(subject) > 40:
            subject = subject[:37] + "..."
        print(f"   {status_icon} {subject} ({log['status']})")


def check_dependencies():
    """Check if all required packages are installed"""
    required_packages = [
        "jinja2",
        "email_validator",
        "aiosmtplib",
        "pydantic",
        "pydantic_settings",
        "structlog",
        "dotenv"
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            # Try alternative names
            alt_names = {
                "email_validator": "email_validator",
                "pydantic_settings": "pydantic_settings", 
                "dotenv": "dotenv"
            }
            try:
                __import__(alt_names.get(package, package))
            except ImportError:
                missing.append(package)
    
    if missing:
        print("❌ Missing required packages:")
        for package in missing:
            display_name = package.replace("_", "-")
            print(f"   - {display_name}")
        print(f"\nInstall them with:")
        print(f"pip install {' '.join([p.replace('_', '-') for p in missing])}")
        return False
    
    return True


if __name__ == "__main__":
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Loaded environment variables from .env")
    except ImportError:
        print("⚠️  python-dotenv not installed, using system environment variables")
    
    # Check if SMTP credentials are set
    required_vars = ['SMTP_USERNAME', 'SMTP_PASSWORD', 'SMTP_FROM_EMAIL']
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        print("\n⚠️  Missing environment variables:")
        for var in missing:
            print(f"   - {var}")
        
        # Try to get them from alternative sources
        smtp_username = input(f"\nEnter SMTP_USERNAME [{required_vars[0]}]: ") or required_vars[0]
        smtp_password = input(f"Enter SMTP_PASSWORD [{required_vars[1]}]: ") or required_vars[1]
        smtp_from_email = input(f"Enter SMTP_FROM_EMAIL [{required_vars[2]}]: ") or required_vars[2]
        
        os.environ['SMTP_USERNAME'] = smtp_username
        os.environ['SMTP_PASSWORD'] = smtp_password
        os.environ['SMTP_FROM_EMAIL'] = smtp_from_email
        
        print("\n✅ Using provided credentials (not saved to .env)")
    
    # Run tests
    try:
        asyncio.run(test_onboarding_emails())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()