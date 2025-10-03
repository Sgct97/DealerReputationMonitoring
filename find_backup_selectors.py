"""
Find REAL Backup Selectors
Analyzes the actual HTML to find alternative selectors that work independently.
"""

import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()

business_url = os.getenv('GOOGLE_BUSINESS_URL')
proxy_server = os.getenv('PROXY_SERVER')
proxy_username = os.getenv('PROXY_USERNAME')
proxy_password = os.getenv('PROXY_PASSWORD')

print("=" * 70)
print("🔍 Finding REAL Backup Selectors")
print("=" * 70)

with sync_playwright() as p:
    launch_opts = {'headless': False}
    if proxy_server:
        launch_opts['proxy'] = {
            'server': f"http://{proxy_server}" if not proxy_server.startswith('http') else proxy_server,
            'username': proxy_username,
            'password': proxy_password
        }
    
    browser = p.chromium.launch(**launch_opts)
    context = browser.new_context(viewport={'width': 1920, 'height': 1080})
    page = context.new_page()
    
    print(f"\n📍 Loading: {business_url}")
    page.goto(business_url, wait_until='domcontentloaded', timeout=30000)
    page.wait_for_timeout(3000)
    
    # Setup
    page.locator('button:has-text("Reviews")').first.click()
    page.wait_for_timeout(2000)
    page.locator('button:has-text("Sort")').first.click()
    page.wait_for_timeout(1000)
    page.locator('div[role="menuitemradio"]:has-text("Lowest")').first.click()
    page.wait_for_timeout(3000)
    
    # Scroll a few times to load reviews
    print("\n📜 Scrolling to load reviews...")
    for i in range(3):
        page.keyboard.press('PageDown')
        page.wait_for_timeout(2000)
    
    print("\n🔬 Analyzing HTML structure to find stable selectors...\n")
    
    # Test potential backup selectors for REVIEW_CONTAINER
    print("=" * 70)
    print("REVIEW_CONTAINER Candidates:")
    print("=" * 70)
    
    candidates = [
        'div.GHT2ce',                           # Current
        'div[data-review-id]',                  # Has data-review-id attribute
        'div.jftiEf',                           # Parent container
        'div[jsaction*="review"]',              # Has review in jsaction
        'div:has(span.kvMYJc)',                 # Contains star rating
        'div:has(span.wiI7pd)',                 # Contains review text
        '[class*="review"]:has(span[aria-label*="star"])'  # Semantic combo
    ]
    
    for selector in candidates:
        try:
            elements = page.query_selector_all(selector)
            count = len(elements) if elements else 0
            # Get a sample to verify it's actually a review
            if count > 0 and elements[0]:
                has_text = elements[0].query_selector('span.wiI7pd') is not None
                has_stars = elements[0].query_selector('span[aria-label*="star"]') is not None
                validity = "✅ VALID REVIEW" if (has_text or has_stars) else "⚠️ WRONG ELEMENT"
                print(f"{validity} '{selector}' → {count} elements")
            else:
                print(f"❌ NONE   '{selector}' → 0 elements")
        except Exception as e:
            print(f"❌ ERROR  '{selector}' → {str(e)[:40]}")
    
    print("\n" + "=" * 70)
    print("Recommendations:")
    print("=" * 70)
    print("\n✅ Use selectors marked 'VALID REVIEW' as fallbacks")
    print("⚠️ Test each one by commenting out primary and running scraper")
    print("❌ Avoid selectors that returned 0 or wrong elements\n")
    
    browser.close()
