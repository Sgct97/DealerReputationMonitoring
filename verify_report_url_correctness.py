"""
Verify that captured report URLs match the correct reviews.
Manually clicks report for a specific reviewer and compares the postId.
"""

import os
import sqlite3
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from urllib.parse import urlparse, parse_qs, unquote

load_dotenv()

# Get the first review from database to verify
conn = sqlite3.connect('./data/reviews.db')
cursor = conn.cursor()
cursor.execute('SELECT reviewer_name, review_text, review_url FROM reviews LIMIT 1')
test_review = cursor.fetchone()
conn.close()

if not test_review:
    print("❌ No reviews in database to test")
    exit(1)

reviewer_name = test_review[0]
review_text = test_review[1]
captured_url = test_review[2]

# Extract postId from captured URL
captured_parsed = urlparse(captured_url)
captured_params = parse_qs(captured_parsed.query)
captured_postid = captured_params.get('postId', ['N/A'])[0]

print("=" * 80)
print("🔍 VERIFYING REPORT URL CORRECTNESS")
print("=" * 80)
print(f"\n📋 Test Review:")
print(f"   Reviewer: {reviewer_name}")
print(f"   Review: {review_text[:80]}...")
print(f"\n📌 Captured PostID: {captured_postid[:60]}...")

business_url = os.getenv('GOOGLE_BUSINESS_URL')
proxy_server = os.getenv('PROXY_SERVER')
proxy_username = os.getenv('PROXY_USERNAME')
proxy_password = os.getenv('PROXY_PASSWORD')

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
    
    print(f"\n🌐 Loading Google Business page...")
    page.goto(business_url, wait_until='domcontentloaded', timeout=30000)
    page.wait_for_timeout(3000)
    
    # Setup
    page.locator('button:has-text("Reviews")').first.click()
    page.wait_for_timeout(2000)
    page.locator('button:has-text("Sort")').first.click()
    page.wait_for_timeout(1000)
    page.locator('div[role="menuitemradio"]:has-text("Lowest")').first.click()
    page.wait_for_timeout(3000)
    
    print(f"\n🔍 Looking for {reviewer_name}'s review...")
    
    # Find the action button for this specific reviewer
    action_button = page.query_selector(f'button[aria-label*="Actions for"][aria-label*="{reviewer_name[:10]}"]')
    
    if not action_button:
        print(f"❌ Could not find action button for {reviewer_name}")
        browser.close()
        exit(1)
    
    print(f"✓ Found action button for {reviewer_name}")
    print(f"\n🖱️ Clicking 3-dot menu...")
    action_button.click()
    page.wait_for_timeout(1500)
    
    print(f"🖱️ Clicking 'Report review'...")
    
    # Listen for popup/new tab
    with context.expect_page() as new_page_info:
        report_button = page.locator('[role="menuitemradio"]:has-text("Report review")').first
        report_button.click()
    
    # Get the new page
    new_page = new_page_info.value
    signin_url = new_page.url
    
    # Extract the real report URL
    parsed = urlparse(signin_url)
    params = parse_qs(parsed.query)
    
    if 'continue' in params:
        real_report_url = unquote(params['continue'][0])
        manual_parsed = urlparse(real_report_url)
        manual_params = parse_qs(manual_parsed.query)
        manual_postid = manual_params.get('postId', ['N/A'])[0]
        
        print(f"\n📌 Manual PostID:  {manual_postid[:60]}...")
        
        print("\n" + "=" * 80)
        print("🎯 VERIFICATION RESULT:")
        print("=" * 80)
        
        if captured_postid == manual_postid:
            print("✅ SUCCESS! PostIDs MATCH!")
            print("✅ The captured report URL is for the CORRECT review")
        else:
            print("❌ FAILURE! PostIDs DO NOT MATCH!")
            print("❌ There's a problem with the report URL capture logic")
            print(f"\n   Captured: {captured_postid[:60]}...")
            print(f"   Manual:   {manual_postid[:60]}...")
        
    else:
        print(f"⚠️ Could not extract continue parameter")
    
    print("\n⏸️ Pausing 5 seconds so you can see the report page...")
    new_page.wait_for_timeout(5000)
    
    browser.close()

print("\n✅ Verification complete")

