"""
Test Selector Fallbacks
Tests each fallback selector individually to prove robustness.
"""

import os
import sys
from dotenv import load_dotenv
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from playwright.sync_api import sync_playwright

# Load environment variables
load_dotenv()

# Get proxy config
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

business_url = os.getenv('GOOGLE_BUSINESS_URL')

# Import selectors
from scraper.scraper import SELECTORS

print("=" * 70)
print("🧪 Testing Selector Fallbacks - Proving Robustness")
print("=" * 70)

with sync_playwright() as p:
    # Launch browser
    launch_options = {'headless': False}
    if proxy_config:
        launch_options['proxy'] = {
            'server': f"http://{proxy_config['server']}" if not proxy_config['server'].startswith('http') else proxy_config['server'],
            'username': proxy_config['username'],
            'password': proxy_config['password']
        }
    
    browser = p.chromium.launch(**launch_options)
    context = browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        locale='en-US'
    )
    page = context.new_page()
    
    print(f"\n📍 Navigating to: {business_url}")
    page.goto(business_url, wait_until='domcontentloaded', timeout=30000)
    page.wait_for_timeout(3000)
    
    # Click reviews tab
    print("\n🔍 Clicking Reviews tab...")
    page.locator('button:has-text("Reviews")').first.click()
    page.wait_for_timeout(2000)
    
    # Click sort and select lowest
    print("🔽 Sorting by lowest rating...")
    page.locator('button:has-text("Sort")').first.click()
    page.wait_for_timeout(1000)
    page.locator('div[role="menuitemradio"]:has-text("Lowest")').first.click()
    page.wait_for_timeout(3000)
    
    print("\n" + "=" * 70)
    print("Testing Each Selector Type")
    print("=" * 70)
    
    # Test each selector category
    for category, selectors in SELECTORS.items():
        print(f"\n📊 Testing {category} selectors:")
        print(f"   Total fallbacks configured: {len(selectors)}")
        
        results = []
        for i, selector in enumerate(selectors, 1):
            try:
                elements = page.query_selector_all(selector)
                count = len(elements) if elements else 0
                if count > 0:
                    results.append(f"✅ #{i} '{selector}' → Found {count} elements")
                else:
                    results.append(f"⚠️  #{i} '{selector}' → Found 0 elements")
            except Exception as e:
                results.append(f"❌ #{i} '{selector}' → Error: {str(e)[:50]}")
        
        for result in results:
            print(f"   {result}")
    
    print("\n" + "=" * 70)
    print("📈 Robustness Analysis")
    print("=" * 70)
    
    # Count how many selectors work for each category
    for category, selectors in SELECTORS.items():
        working_count = 0
        for selector in selectors:
            try:
                elements = page.query_selector_all(selector)
                if elements and len(elements) > 0:
                    working_count += 1
            except:
                pass
        
        percentage = (working_count / len(selectors)) * 100
        status = "✅ EXCELLENT" if working_count >= 2 else "⚠️ WARNING" if working_count == 1 else "❌ CRITICAL"
        print(f"{status} {category}: {working_count}/{len(selectors)} selectors working ({percentage:.0f}%)")
    
    print("\n✅ Test complete - Check results above")
    print("=" * 70)
    
    browser.close()
