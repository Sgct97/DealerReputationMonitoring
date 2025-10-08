"""
Capture Report Review URL
Clicks Report review and captures the URL of the new tab that opens.
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
print("🔍 Capturing Report Review URL")
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
    
    print("\n🔍 Finding first review's 3-dot menu...")
    
    # Find first action button
    action_button = page.query_selector('button[aria-label*="Actions for"]')
    
    if action_button:
        reviewer_label = action_button.get_attribute('aria-label')
        print(f"✓ Found button: {reviewer_label}")
        
        # Listen for new page/tab
        print("\n🖱️ Clicking 3-dot menu...")
        action_button.click()
        page.wait_for_timeout(1500)
        
        # Click "Report review" - use the actual menu item role
        print("🖱️ Clicking 'Report review'...")
        
        # Listen for popup/new tab
        with context.expect_page() as new_page_info:
            # Click the actual menuitem that contains "Report review" text
            report_button = page.locator('[role="menuitemradio"]:has-text("Report review")').first
            report_button.click()
        
        # Get the new page
        new_page = new_page_info.value
        print(f"\n✅ New tab opened!")
        
        # Extract the real report URL from the continue parameter
        from urllib.parse import urlparse, parse_qs, unquote
        
        signin_url = new_page.url
        parsed = urlparse(signin_url)
        params = parse_qs(parsed.query)
        
        if 'continue' in params:
            real_report_url = unquote(params['continue'][0])
            print(f"\n✅ EXTRACTED REAL REPORT URL:")
            print(f"{real_report_url}\n")
            
            print("=" * 70)
            print("URL Breakdown:")
            print("=" * 70)
            report_parsed = urlparse(real_report_url)
            report_params = parse_qs(report_parsed.query)
            print(f"postId: {report_params.get('postId', ['N/A'])[0]}")
            print(f"entityid: {report_params.get('entityid', ['N/A'])[0][:80]}...")
            print(f"\n✅ This is the URL to put in the email!")
        else:
            print(f"⚠️ Could not extract continue parameter")
            print(f"Full URL: {signin_url}\n")
        
        # Wait so you can see it
        print("⏸️ Pausing 10 seconds so you can see the report page...")
        new_page.wait_for_timeout(10000)
        
    else:
        print("❌ Could not find action menu button")
    
    browser.close()

print("\n✅ Done - Check the URL format above")

