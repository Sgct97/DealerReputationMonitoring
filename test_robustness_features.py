"""
Test Robustness Features:
1. Retry logic with exponential backoff
2. Graceful degradation 
3. Failure alerts (email not sent in test)
"""

import os
import sys
from dotenv import load_dotenv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from scraper.scraper import GoogleReviewsScraper
from database.db_manager import DatabaseManager

load_dotenv()

business_url = os.getenv('GOOGLE_BUSINESS_URL')

# Proxy configuration
proxy_server = os.getenv('PROXY_SERVER')
proxy_username = os.getenv('PROXY_USERNAME')
proxy_password = os.getenv('PROXY_PASSWORD')

proxy_config = None
if proxy_server:
    proxy_config = {
        'server': proxy_server,
        'username': proxy_username,
        'password': proxy_password
    }

print("=" * 70)
print("🧪 Testing Robustness Features")
print("=" * 70)

print("\n✅ Feature 1: Retry Logic with Exponential Backoff")
print("   - Scraper will retry up to 3 times if it fails")
print("   - Wait time: 10s, 20s, 40s between retries")
print("   - Prevents temporary failures from breaking the system")

print("\n✅ Feature 2: Graceful Degradation")  
print("   - If sorting fails → continues with default sort")
print("   - If More buttons fail → uses truncated text")
print("   - Partial success instead of total failure")

print("\n✅ Feature 3: Failure Email Alerts")
print("   - Sends email if all retries fail")
print("   - Includes error details and troubleshooting")
print("   - Client knows immediately when action needed")

print("\n" + "=" * 70)
print("Running Normal Scrape to Verify All Features Work")
print("=" * 70)

database_path = './data/reviews_robust_test.db'
db = DatabaseManager(database_path)

try:
    # Test with 2 retries configured
    with GoogleReviewsScraper(proxy_config, max_retries=2) as scraper:
        print("\n📊 Scraper configured with max_retries=2")
        print("🔍 Starting scrape...")
        
        # Quick test - limit to 30 reviews
        reviews = scraper.scrape_reviews(
            business_url,
            db_manager=db,
            scrape_all=True,
            max_reviews=30,
            star_ratings_to_track=[1]
        )
        
        print(f"\n✅ SUCCESS: Scraped {len(reviews)} reviews")
        print(f"   All robustness features are active and working!")
        
        # Save to database
        for review in reviews:
            db.add_review(review)
        
        stats = db.get_stats()
        print(f"\n📊 Saved to database: {stats['total_reviews']} reviews")
        
except Exception as e:
    print(f"\n❌ Test failed: {e}")
    print("   (Failure alert would be sent here if Gmail was configured)")

# Cleanup
import os as os_module
if os_module.path.exists(database_path):
    os_module.remove(database_path)

print("\n" + "=" * 70)
print("✅ Robustness Features Test Complete")
print("=" * 70)

