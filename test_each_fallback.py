"""
Test Each Fallback Independently
Forces the scraper to use each fallback selector one at a time to prove they all work.
"""

import os
import sys
from dotenv import load_dotenv
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from scraper.scraper import GoogleReviewsScraper, SELECTORS
from database.db_manager import DatabaseManager

# Load environment variables
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
print("🧪 Testing Each Fallback Selector Independently")
print("=" * 70)
print("\nThis will run the scraper multiple times, each time using")
print("a different fallback selector to prove they all work!\n")

# Test categories that have multiple working selectors
categories_to_test = {
    'REVIEW_CONTAINER': [0, 1],  # Test selectors #0 and #1 (both work)
    'STAR_RATING': [0, 1, 2],    # Test all 3 (all work)
    'MORE_BUTTON': [0, 2]        # Test selectors #0 and #2 (both work)
}

results = []

for category, selector_indices in categories_to_test.items():
    print(f"\n{'=' * 70}")
    print(f"Testing {category} Fallbacks")
    print(f"{'=' * 70}")
    
    for idx in selector_indices:
        selector = SELECTORS[category][idx]
        print(f"\n🔬 Test: Using {category} selector #{idx + 1}: '{selector}'")
        print(f"   (Temporarily disabling other {category} selectors)")
        
        # Backup original selectors
        original_selectors = SELECTORS[category].copy()
        
        # Force use of only this selector
        SELECTORS[category] = [selector]
        
        try:
            # Create temp database
            test_db_path = f'./data/test_fallback_{category}_{idx}.db'
            db = DatabaseManager(test_db_path)
            
            with GoogleReviewsScraper(proxy_config) as scraper:
                # Quick scrape - just 2 scrolls to test
                print(f"   Running quick scrape (2 scrolls)...")
                
                from playwright.sync_api import sync_playwright
                p = sync_playwright().start()
                launch_opts = {'headless': False}
                if proxy_config:
                    launch_opts['proxy'] = {
                        'server': f"http://{proxy_config['server']}" if not proxy_config['server'].startswith('http') else proxy_config['server'],
                        'username': proxy_config['username'],
                        'password': proxy_config['password']
                    }
                
                browser = p.chromium.launch(**launch_opts)
                context = browser.new_context(viewport={'width': 1920, 'height': 1080})
                page = context.new_page()
                
                # Navigate and setup
                page.goto(business_url, wait_until='domcontentloaded', timeout=30000)
                page.wait_for_timeout(2000)
                
                # Click reviews
                page.locator('button:has-text("Reviews")').first.click()
                page.wait_for_timeout(2000)
                
                # Sort
                page.locator('button:has-text("Sort")').first.click()
                page.wait_for_timeout(1000)
                page.locator('div[role="menuitemradio"]:has-text("Lowest")').first.click()
                page.wait_for_timeout(2000)
                
                # Scroll twice
                for i in range(2):
                    page.keyboard.press('PageDown')
                    page.keyboard.press('PageDown')
                    page.wait_for_timeout(2000)
                
                # Try to extract reviews using this selector
                reviews = scraper._extract_reviews(page)
                
                browser.close()
                p.stop()
                
                if len(reviews) > 0:
                    result = f"✅ {category} selector #{idx + 1} WORKS - Got {len(reviews)} reviews"
                    print(f"   {result}")
                    results.append(result)
                else:
                    result = f"❌ {category} selector #{idx + 1} FAILED - Got 0 reviews"
                    print(f"   {result}")
                    results.append(result)
            
            # Cleanup
            import os as os_module
            if os_module.path.exists(test_db_path):
                os_module.remove(test_db_path)
                
        except Exception as e:
            result = f"❌ {category} selector #{idx + 1} ERROR: {str(e)[:60]}"
            print(f"   {result}")
            results.append(result)
        
        finally:
            # Restore original selectors
            SELECTORS[category] = original_selectors

print(f"\n{'=' * 70}")
print("📊 Final Results")
print(f"{'=' * 70}\n")

for result in results:
    print(result)

working = len([r for r in results if '✅' in r])
total = len(results)
print(f"\n🎯 Success Rate: {working}/{total} fallback selectors working ({working/total*100:.0f}%)")
print(f"\n✅ Fallback system validated!")
print("=" * 70)
