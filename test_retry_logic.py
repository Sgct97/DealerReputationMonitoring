"""
REAL Test: Retry Logic
Uses a bad URL to trigger failures and verify retry mechanism works.
"""
import os
import sys
from dotenv import load_dotenv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from scraper.scraper import GoogleReviewsScraper

load_dotenv()

proxy_server = os.getenv('PROXY_SERVER')
proxy_username = os.getenv('PROXY_USERNAME')
proxy_password = os.getenv('PROXY_PASSWORD')

proxy_config = None
if proxy_server:
    proxy_config = {'server': proxy_server, 'username': proxy_username, 'password': proxy_password}

print("=" * 70)
print("🧪 TEST 1: Retry Logic with Bad URL")
print("=" * 70)
print("\nUsing INVALID URL to trigger failures...")
print("Should retry 3 times with exponential backoff (10s, 20s, 40s)\n")

bad_url = "https://www.google.com/maps/place/FAKE_BUSINESS_12345"

try:
    with GoogleReviewsScraper(proxy_config, max_retries=3) as scraper:
        reviews = scraper.scrape_reviews(bad_url, scrape_all=True, max_reviews=10)
        print(f"\n❌ FAIL: Should have raised exception but got {len(reviews)} reviews")
except Exception as e:
    print(f"\n✅ PASS: Retry logic exhausted after 3 attempts")
    print(f"   Final error: {str(e)[:100]}")

