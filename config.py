"""
Configuration Template
Copy this to .env and fill in your actual values.
"""

CONFIG_TEMPLATE = """
# Google Business Profile URL
# Example: https://www.google.com/maps/place/Your+Business+Name/@latitude,longitude,17z/data=...
GOOGLE_BUSINESS_URL=https://www.google.com/maps/place/YOUR_BUSINESS_HERE

# OpenAI API Key
# Get this from: https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-your-api-key-here

# SendGrid API Key
# Get this from: https://app.sendgrid.com/settings/api_keys
SENDGRID_API_KEY=SG.your-sendgrid-api-key-here

# Email Configuration
FROM_EMAIL=alerts@yourdomain.com
TO_EMAIL=client@example.com

# Residential Proxy Configuration (HIGHLY RECOMMENDED)
# Example providers: BrightData, Smartproxy, Oxylabs
PROXY_SERVER=http://proxy-provider.com:port
PROXY_USERNAME=your_proxy_username
PROXY_PASSWORD=your_proxy_password

# Database Path (default is fine for most cases)
DATABASE_PATH=./data/reviews.db
"""

if __name__ == "__main__":
    print("=" * 60)
    print("Configuration Template")
    print("=" * 60)
    print("\nCreate a .env file in the project root with these variables:")
    print(CONFIG_TEMPLATE)
    print("\n" + "=" * 60)
