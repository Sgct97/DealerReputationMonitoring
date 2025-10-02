"""
Test Script for Email Notification Module
Tests that the Gmail SMTP email integration works correctly.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from notifications.emailer import EmailNotifier
from dotenv import load_dotenv
import os

def test_email_notifier():
    """Test the email notification functionality."""
    
    print("=" * 60)
    print("🧪 Testing Email Notification Module (Gmail SMTP)")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    # Get configuration
    gmail_address = os.getenv('GMAIL_ADDRESS')
    gmail_app_password = os.getenv('GMAIL_APP_PASSWORD')
    to_email = os.getenv('TO_EMAIL')
    
    # Validate configuration
    missing = []
    if not gmail_address or gmail_address == 'your_gmail@gmail.com':
        missing.append('GMAIL_ADDRESS')
    if not gmail_app_password or gmail_app_password == 'your_16_char_app_password':
        missing.append('GMAIL_APP_PASSWORD')
    if not to_email or to_email == 'recipient@example.com':
        missing.append('TO_EMAIL')
    
    if missing:
        print(f"\n❌ Error: Missing configuration: {', '.join(missing)}")
        print("Please update your .env file with valid values")
        print("\nTo get a Gmail App Password:")
        print("1. Go to https://myaccount.google.com/apppasswords")
        print("2. Generate a new app password for 'Mail'")
        print("3. Copy the 16-character password to your .env file")
        return False
    
    print("✓ Email configuration loaded")
    print(f"   Gmail: {gmail_address}")
    print(f"   To: {to_email}")
    
    # Initialize email notifier
    print("\n1️⃣  Initializing email notifier...")
    notifier = EmailNotifier(gmail_address, gmail_app_password, to_email)
    print("✓ Email notifier initialized")
    
    # Create sample review and analysis data
    sample_review = {
        'reviewer_name': 'Test Reviewer',
        'star_rating': 1,
        'review_text': 'This is a test review for the email notification system.',
        'review_date': 'Just now',
        'review_url': 'https://www.google.com/maps'
    }
    
    sample_analysis = {
        'category': 'Spam',
        'reasoning': 'This is a test analysis for demonstration purposes.'
    }
    
    print("\n2️⃣  Sending test email...")
    print("   (Check your inbox at: " + to_email + ")")
    
    try:
        success = notifier.send_review_alert(sample_review, sample_analysis)
        
        if success:
            print("✓ Email sent successfully!")
            print("\n📧 Check your email inbox to verify the message arrived.")
            print("   Subject: 🚨 New 1-Star Review Alert - Test Reviewer")
        else:
            print("❌ Failed to send email")
            print("   This could mean:")
            print("   - Invalid Gmail App Password")
            print("   - Gmail address not correct")
            print("   - Less secure apps not enabled (if needed)")
            print("   - Network issue")
            return False
        
    except Exception as e:
        print(f"❌ Error sending email: {str(e)}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ Email Test Completed!")
    print("=" * 60)
    print("\n💡 Important:")
    print("   - Verify the email arrived in your inbox")
    print("   - Check spam folder if you don't see it")
    print("   - Verify the email looks professional and contains all info")
    print("\n📝 Note: Gmail SMTP is free and allows 500 emails/day")
    
    return True


if __name__ == "__main__":
    try:
        success = test_email_notifier()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
