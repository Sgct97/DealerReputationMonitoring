"""
Find Report Review Button
Clicks the 3-dot menu and captures the dropdown HTML to find "Report review" selector.
"""

import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
import time

load_dotenv()

business_url = os.getenv('GOOGLE_BUSINESS_URL')
proxy_server = os.getenv('PROXY_SERVER')
proxy_username = os.getenv('PROXY_USERNAME')
proxy_password = os.getenv('PROXY_PASSWORD')

print("=" * 70)
print("🔍 Finding Report Review Button Selector")
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
    
    # Click reviews and sort
    page.locator('button:has-text("Reviews")').first.click()
    page.wait_for_timeout(2000)
    page.locator('button:has-text("Sort")').first.click()
    page.wait_for_timeout(1000)
    page.locator('div[role="menuitemradio"]:has-text("Lowest")').first.click()
    page.wait_for_timeout(3000)
    
    print("\n🔍 Finding first review's 3-dot menu button...")
    
    # Find the first review's action menu button (3 dots)
    action_buttons = page.query_selector_all('button.PP3Y3d.S1qRNe')
    
    if action_buttons and len(action_buttons) > 0:
        print(f"✓ Found {len(action_buttons)} action menu buttons")
        
        first_button = action_buttons[0]
        print("\n📋 3-Dot Button HTML:")
        print(first_button.evaluate('el => el.outerHTML'))
        
        print("\n🖱️ Clicking first 3-dot menu...")
        first_button.click()
        page.wait_for_timeout(2000)
        
        # Capture all visible menu items
        print("\n🔍 Searching for menu items after click...")
        
        # Try different selectors for menu items
        menu_selectors = [
            'div[role="menuitem"]',
            'button[role="menuitem"]',
            'div:has-text("Report review")',
            'button:has-text("Report")',
            '[role="menu"] div',
            '[role="menu"] button'
        ]
        
        for selector in menu_selectors:
            elements = page.query_selector_all(selector)
            if elements and len(elements) > 0:
                print(f"\n✓ Selector '{selector}' found {len(elements)} elements:")
                for i, el in enumerate(elements[:3]):  # Show first 3
                    text = el.inner_text()[:50] if el.inner_text() else "No text"
                    print(f"   #{i + 1}: {text}")
        
        # Try to find specifically "Report review"
        print("\n🎯 Looking specifically for 'Report review'...")
        report_candidates = [
            'div:has-text("Report review")',
            'button:has-text("Report review")',
            '[role="menuitem"]:has-text("Report")',
            'div.xCaLbe:has-text("Report")'  # Common Google menu item class
        ]
        
        for selector in report_candidates:
            try:
                el = page.locator(selector).first
                if el:
                    print(f"✓ Found with '{selector}':")
                    html = el.evaluate('el => el.outerHTML')
                    print(f"   HTML: {html[:200]}")
            except:
                print(f"✗ Not found with '{selector}'")
        
        print("\n⏸️ Pausing 10 seconds so you can inspect the dropdown manually...")
        page.wait_for_timeout(10000)
        
    else:
        print("❌ Could not find action menu buttons")
    
    browser.close()

print("\n" + "=" * 70)
print("✅ Investigation Complete")
print("=" * 70)

