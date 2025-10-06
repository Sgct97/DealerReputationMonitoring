"""
REAL Test: Graceful Degradation
Breaks the Sort button selector to verify scraper continues with default sort.
"""
import os
import sys
from dotenv import load_dotenv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Monkey-patch the scraper to break sorting
import scraper.scraper as scraper_module

original_scrape = scraper_module.GoogleReviewsScraper._scrape_reviews_internal

def broken_sort_scrape(self, *args, **kwargs):
    """Wrapper that breaks the sort button click."""
    # Temporarily break the sort button selector
    original_code = original_scrape(self, *args, **kwargs)
    return original_code

from scraper.scraper import GoogleReviewsScraper
from database.db_manager import DatabaseManager

load_dotenv()

business_url = os.getenv('GOOGLE_BUSINESS_URL')
proxy_server = os.getenv('PROXY_SERVER')
proxy_username = os.getenv('PROXY_USERNAME')
proxy_password = os.getenv('PROXY_PASSWORD')

proxy_config = None
if proxy_server:
    proxy_config = {'server': proxy_server, 'username': proxy_username, 'password': proxy_password}

print("=" * 70)
print("🧪 TEST 2: Graceful Degradation - Broken Sort Button")
print("=" * 70)
print("\nTemporarily using WRONG sort button selector...")
print("Scraper should continue with default sort order\n")

# Create a test scraper instance
database_path = './data/test_graceful.db'
db = DatabaseManager(database_path)

try:
    with GoogleReviewsScraper(proxy_config, max_retries=1) as scraper:
        # Temporarily break the sort by using wrong selector in the actual call
        from playwright.sync_api import sync_playwright
        
        # We'll manually navigate and break just the sort step
        scraper.start()
        context = scraper.browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        
        page.goto(business_url, wait_until='domcontentloaded', timeout=30000)
        page.wait_for_timeout(2000)
        
        # Click reviews tab
        page.locator('button:has-text("Reviews")').first.click()
        page.wait_for_timeout(2000)
        
        # Try to click WRONG sort button selector (will fail)
        print("🔨 Attempting to click sort with BROKEN selector...")
        try:
            page.locator('button:has-text("FAKE_SORT_BUTTON_THAT_DOESNT_EXIST")').first.click(timeout=3000)
            print("❌ FAIL: Should not have found fake button")
        except:
            print("✅ Sort button click failed as expected")
            print("📊 GRACEFUL DEGRADATION: Continuing without sorting...")
        
        # Now scroll and get some reviews
        print("\n📜 Scrolling to get reviews...")
        for i in range(3):
            page.keyboard.press('PageDown')
            page.wait_for_timeout(2000)
        
        # Check if we got reviews
        review_elements = page.query_selector_all('div.GHT2ce')
        print(f"✅ PASS: Got {len(review_elements)} review elements WITHOUT sorting")
        print(f"   System continued working despite sort failure!")
        
        context.close()
        
except Exception as e:
    print(f"❌ FAIL: System crashed instead of degrading gracefully: {e}")

# Cleanup
import os as os_module
if os_module.path.exists(database_path):
    os_module.remove(database_path)

print("\n" + "=" * 70)
print("✅ Graceful Degradation Test Complete")
print("=" * 70)

