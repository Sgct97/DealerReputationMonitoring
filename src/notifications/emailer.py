"""
Email Notification System
Sends alerts when new 1-star reviews are detected.
Uses Gmail SMTP for simple, free email delivery.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict
from datetime import datetime


class EmailNotifier:
    """Sends email notifications for new reviews via Gmail SMTP."""
    
    def __init__(self, gmail_address: str, gmail_app_password: str, to_email: str):
        """
        Initialize the email notifier with Gmail SMTP.
        
        Args:
            gmail_address: Your Gmail address (e.g., youremail@gmail.com)
            gmail_app_password: Gmail App Password (NOT your regular password)
            to_email: Email address to send notifications to
        """
        self.gmail_address = gmail_address
        self.gmail_app_password = gmail_app_password
        self.to_email = to_email
    
    def send_review_alert(self, review_data: Dict, ai_analysis: Dict) -> bool:
        """
        Send an email alert for a new 1-star review via Gmail SMTP.
        
        Args:
            review_data: Dictionary containing review information
            ai_analysis: Dictionary containing AI analysis results
        
        Returns:
            True if email was sent successfully, False otherwise
        """
        
        subject = f"🚨 New 1-Star Review Alert - {review_data['reviewer_name']}"
        html_content = self._create_email_html(review_data, ai_analysis)
        
        # Create message
        message = MIMEMultipart('alternative')
        message['Subject'] = subject
        message['From'] = self.gmail_address
        message['To'] = self.to_email
        
        # Attach HTML content
        html_part = MIMEText(html_content, 'html')
        message.attach(html_part)
        
        try:
            # Connect to Gmail's SMTP server
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(self.gmail_address, self.gmail_app_password)
                server.send_message(message)
            
            return True
            
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return False
    
    def _create_email_html(self, review_data: Dict, ai_analysis: Dict) -> str:
        """
        Create the HTML content for the email.
        
        Args:
            review_data: Dictionary containing review information
            ai_analysis: Dictionary containing AI analysis results
        
        Returns:
            HTML string
        """
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px 10px 0 0;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
        }}
        .content {{
            background: #f8f9fa;
            padding: 30px;
            border-radius: 0 0 10px 10px;
        }}
        .review-box {{
            background: white;
            border-left: 4px solid #dc3545;
            padding: 20px;
            margin: 20px 0;
            border-radius: 4px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .review-meta {{
            color: #666;
            font-size: 14px;
            margin-bottom: 10px;
        }}
        .review-text {{
            font-size: 16px;
            line-height: 1.6;
            color: #333;
        }}
        .ai-recommendation {{
            background: #e7f3ff;
            border-left: 4px solid #0066cc;
            padding: 20px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .ai-recommendation h3 {{
            margin-top: 0;
            color: #0066cc;
        }}
        .category {{
            display: inline-block;
            background: #0066cc;
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 14px;
            margin: 10px 0;
        }}
        .reasoning {{
            color: #555;
            font-style: italic;
        }}
        .action-button {{
            display: inline-block;
            background: #28a745;
            color: white;
            padding: 15px 30px;
            text-decoration: none;
            border-radius: 5px;
            font-weight: bold;
            margin-top: 20px;
            text-align: center;
        }}
        .action-button:hover {{
            background: #218838;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            color: #666;
            font-size: 12px;
        }}
        .stars {{
            color: #ffc107;
            font-size: 20px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚨 New 1-Star Review Detected</h1>
        <p style="margin: 10px 0 0 0;">Immediate action recommended</p>
    </div>
    
    <div class="content">
        <div class="review-box">
            <div class="review-meta">
                <strong>Reviewer:</strong> {review_data['reviewer_name']}<br>
                <strong>Rating:</strong> <span class="stars">{'★' * review_data['star_rating']}{'☆' * (5 - review_data['star_rating'])}</span><br>
                <strong>Date Posted:</strong> {review_data['review_date']}
            </div>
            <div class="review-text">
                "{review_data['review_text']}"
            </div>
        </div>
        
        <div class="ai-recommendation">
            <h3>🤖 AI Analysis & Recommendation</h3>
            <p><strong>Recommended Reporting Category:</strong></p>
            <span class="category">{ai_analysis['category']}</span>
            <p class="reasoning"><strong>Why:</strong> {ai_analysis['reasoning']}</p>
        </div>
        
        <div style="text-align: center;">
            <a href="{review_data['review_url']}" class="action-button">
                📝 Report This Review Now
            </a>
            <p style="margin-top: 10px; font-size: 14px; color: #666;">
                Click the button above to go directly to this review and report it using the recommended category.
            </p>
        </div>
        
        <div class="footer">
            <p>This is an automated alert from your Reputation Management System</p>
            <p>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
        </div>
    </div>
</body>
</html>
"""
        return html
    
    def send_failure_alert(self, subject: str, html_body: str) -> bool:
        """
        Send a failure alert email when scraping fails.
        
        Args:
            subject: Email subject
            html_body: HTML body content
        
        Returns:
            True if email was sent successfully, False otherwise
        """
        # Create message
        message = MIMEMultipart('alternative')
        message['Subject'] = subject
        message['From'] = self.gmail_address
        message['To'] = self.to_email
        
        # Attach HTML content
        html_part = MIMEText(html_body, 'html')
        message.attach(html_part)
        
        try:
            # Connect to Gmail's SMTP server
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(self.gmail_address, self.gmail_app_password)
                server.send_message(message)
            
            return True
            
        except Exception as e:
            print(f"Error sending failure alert: {str(e)}")
            return False