"""
Verify EntityID Assumption
Tests if entityid is the same for multiple reviews from one business.
"""

import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from urllib.parse import urlparse, parse_qs, unquote

load_dotenv()

business_url = os.getenv('GOOGLE_BUSINESS_URL')
proxy_server = os.getenv('PROXY_SERVER')
proxy_username = os.getenv('PROXY_USERNAME')
proxy_password = os.getenv('PROXY_PASSWORD')

print("=" * 70)
print("🧪 Testing EntityID Assumption")
print("=" * 70)
print("\nHypothesis: entityid is the SAME for all reviews from one business\n")

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
    
    page.goto(business_url, wait_until='domcontentloaded', timeout=30000)
    page.wait_for_timeout(3000)
    
    # Setup
    page.locator('button:has-text("Reviews")').first.click()
    page.wait_for_timeout(2000)
    page.locator('button:has-text("Sort")').first.click()
    page.wait_for_timeout(1000)
    page.locator('div[role="menuitemradio"]:has-text("Lowest")').first.click()
    page.wait_for_timeout(3000)
    
    # Get first 2 reviews' report URLs
    action_buttons = page.query_selector_all('button[aria-label*="Actions for"]')
    
    report_urls = []
    
    for i in range(min(2, len(action_buttons))):
        print(f"\n🔍 Capturing report URL for review #{i+1}...")
        
        try:
            # Click 3-dot menu
            action_buttons[i].click()
            page.wait_for_timeout(1000)
            
            # Click Report and capture URL
            with context.expect_page() as new_page_info:
                page.locator('[role="menuitemradio"]:has-text("Report review")').first.click(timeout=5000)
            
            new_page = new_page_info.value
            signin_url = new_page.url
            new_page.close()
            
            # Extract real URL
            parsed = urlparse(signin_url)
            params = parse_qs(parsed.query)
            
            if 'continue' in params:
                real_url = unquote(params['continue'][0])
                report_parsed = urlparse(real_url)
                report_params = parse_qs(report_parsed.query)
                
                post_id = report_params.get('postId', ['N/A'])[0]
                entity_id = report_params.get('entityid', ['N/A'])[0]
                
                report_urls.append({
                    'review_num': i+1,
                    'postId': post_id,
                    'entityid': entity_id
                })
                
                print(f"✓ PostId: {post_id[:40]}...")
                print(f"✓ EntityId: {entity_id[:40]}...")
            
            page.wait_for_timeout(1000)
            
        except Exception as e:
            print(f"❌ Failed: {e}")
    
    browser.close()
    
    # Compare
    print("\n" + "=" * 70)
    print("🔬 Analysis")
    print("=" * 70)
    
    if len(report_urls) >= 2:
        postId_1 = report_urls[0]['postId']
        postId_2 = report_urls[1]['postId']
        entityid_1 = report_urls[0]['entityid']
        entityid_2 = report_urls[1]['entityid']
        
        print(f"\nReview 1 PostId:   {postId_1[:60]}...")
        print(f"Review 2 PostId:   {postId_2[:60]}...")
        print(f"PostIds Match: {'❌ NO (correct - each review unique)' if postId_1 != postId_2 else '⚠️ YES (unexpected)'}")
        
        print(f"\nReview 1 EntityId: {entityid_1[:60]}...")
        print(f"Review 2 EntityId: {entityid_2[:60]}...")
        print(f"EntityIds Match: {'✅ YES (can reuse for all reviews!)' if entityid_1 == entityid_2 else '❌ NO (must capture each time)'}")
        
        if entityid_1 == entityid_2:
            print("\n✅ CONFIRMED: EntityID is the same for all reviews from one business!")
            print("   → We can capture it ONCE and reuse it for all reviews")
            print("   → This saves time (only 1 click-through needed per business)")
        else:
            print("\n❌ HYPOTHESIS FALSE: EntityID is different per review")
            print("   → Must click Report for EACH review to get URL")
            print("   → This will be slow (~2s per review)")
    
print("\n" + "=" * 70)
