"""
Diagnose truncation by inspecting the actual HTML structure of reviews
"""
import sys
import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
import time

# Load environment variables
load_dotenv()

def diagnose():
    url = "https://www.google.com/maps/place/Koons+Tysons+Toyota/@38.9219439,-77.2290154,17z/data=!4m8!3m7!1s0x89b64ba5bfa5ba59:0xc0ffafdb6e0e866f!8m2!3d38.9219439!4d-77.2264405!9m1!1b1!16s%2Fg%2F1thx3bw8"
    
    # Get proxy config from environment (same as scraper)
    proxy_server = os.getenv('PROXY_SERVER')
    proxy_username = os.getenv('PROXY_USERNAME')
    proxy_password = os.getenv('PROXY_PASSWORD')
    
    with sync_playwright() as p:
        launch_options = {'headless': False}
        
        # Add proxy if configured (same as scraper)
        if proxy_server:
            print(f"🔒 Using proxy: {proxy_server}")
            launch_options['proxy'] = {
                'server': proxy_server,
                'username': proxy_username,
                'password': proxy_password
            }
        
        browser = p.chromium.launch(**launch_options)
        
        # Create context with same settings as scraper
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US'
        )
        page = context.new_page()
        
        print("🌐 Loading Google Business page with 1920x1080 viewport...")
        page.goto(url, wait_until='domcontentloaded', timeout=30000)
        time.sleep(3)
        
        # Click Reviews tab (use locator like scraper does)
        print("📊 Clicking 'Reviews' tab...")
        try:
            reviews_button = page.locator('button:has-text("Reviews")').first
            reviews_button.click()
            time.sleep(2)
            print("   ✓ Reviews tab clicked")
        except Exception as e:
            print(f"   ❌ Could not click Reviews button: {e}")
        
        # Sort by lowest
        print("🔽 Sorting by 'Lowest rating'...")
        sort_button = page.query_selector('button[aria-label*="Sort reviews"]')
        if sort_button:
            sort_button.click()
            time.sleep(1)
            lowest_option = page.query_selector('div[role="menuitemradio"]:has-text("Lowest rating")')
            if lowest_option:
                lowest_option.click()
                time.sleep(3)
        else:
            print("   ⚠️  Could not find sort button")
        
        # Wait for reviews to load (like scraper does)
        print("⏳ Waiting for reviews to load...")
        try:
            page.wait_for_selector('div.GHT2ce', timeout=10000)
            print("   ✓ Reviews loaded")
        except:
            print("   ⚠️  Reviews didn't load in time")
        
        time.sleep(2)  # Extra wait
        
        # Take screenshot for debugging
        page.screenshot(path='data/diagnostic_screenshot.png')
        print("   📸 Screenshot saved to data/diagnostic_screenshot.png")
        
        # Get first few review containers
        print("\n🔍 Inspecting first 5 reviews BEFORE clicking More buttons...\n")
        containers = page.query_selector_all('div.GHT2ce')
        print(f"   Found {len(containers)} review containers")
        
        for i in range(min(5, len(containers))):
            container = containers[i]
            
            # Get reviewer name
            name_elem = container.query_selector('button.al6Kxe div.d4r55')
            name = name_elem.inner_text() if name_elem else "Unknown"
            
            # Get ALL span.wiI7pd elements
            text_spans = container.query_selector_all('span.wiI7pd')
            print(f"Review #{i+1}: {name}")
            print(f"  Number of span.wiI7pd elements: {len(text_spans)}")
            
            for j, span in enumerate(text_spans):
                text = span.inner_text()
                print(f"    Span {j+1}: {len(text)} chars - '{text[:100]}...'")
            
            # Check for More button
            more_btn = container.query_selector('button.w8nwRe')
            has_more = more_btn is not None
            is_visible = more_btn.is_visible() if has_more else False
            print(f"  Has More button: {has_more}, Visible: {is_visible}")
            print("-" * 80)
        
        # Now click More buttons
        print("\n🖱️  Clicking all More buttons...\n")
        more_buttons = page.query_selector_all('button.w8nwRe')
        clicked_count = 0
        for btn in more_buttons:
            try:
                if btn.is_visible():
                    btn.scroll_into_view_if_needed()
                    time.sleep(0.1)
                    btn.click()
                    clicked_count += 1
            except:
                pass
        
        print(f"   Clicked {clicked_count} More buttons")
        time.sleep(5)
        
        # Check AFTER clicking
        print("\n🔍 Inspecting same 5 reviews AFTER clicking More buttons...\n")
        containers = page.query_selector_all('div.GHT2ce')
        
        for i in range(min(5, len(containers))):
            container = containers[i]
            
            # Get reviewer name
            name_elem = container.query_selector('button.al6Kxe div.d4r55')
            name = name_elem.inner_text() if name_elem else "Unknown"
            
            # Get ALL span.wiI7pd elements
            text_spans = container.query_selector_all('span.wiI7pd')
            print(f"Review #{i+1}: {name}")
            print(f"  Number of span.wiI7pd elements: {len(text_spans)}")
            
            for j, span in enumerate(text_spans):
                text = span.inner_text()
                print(f"    Span {j+1}: {len(text)} chars - '{text[:100]}...'")
            
            print("-" * 80)
        
        print("\n✓ Diagnostic complete. Check screenshot at data/diagnostic_screenshot.png")
        time.sleep(2)
        browser.close()

if __name__ == "__main__":
    diagnose()
