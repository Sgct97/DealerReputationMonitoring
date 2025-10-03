"""
Capture actual HTML structure to find real backup selectors
"""
import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()

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
    
    page.goto(business_url, wait_until='domcontentloaded', timeout=30000)
    page.wait_for_timeout(3000)
    
    # Setup
    page.locator('button:has-text("Reviews")').first.click()
    page.wait_for_timeout(2000)
    page.locator('button:has-text("Sort")').first.click()
    page.wait_for_timeout(1000)
    page.locator('div[role="menuitemradio"]:has-text("Lowest")').first.click()
    page.wait_for_timeout(3000)
    
    # Scroll to load reviews
    for i in range(5):
        page.keyboard.press('PageDown')
        page.wait_for_timeout(1500)
    
    print("Capturing HTML structure...")
    
    # Save full page HTML
    html_content = page.content()
    with open('data/page_structure.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✓ Saved full HTML to: data/page_structure.html ({len(html_content)} bytes)")
    
    # Get first review element and save its structure
    first_review = page.query_selector('div.GHT2ce')
    if first_review:
        review_html = first_review.evaluate('el => el.outerHTML')
        with open('data/review_element.html', 'w', encoding='utf-8') as f:
            f.write(review_html)
        print(f"✓ Saved first review HTML to: data/review_element.html")
        
        # Print key attributes
        print("\n🔍 First review element attributes:")
        attrs = first_review.evaluate('''el => {
            let result = {};
            for (let attr of el.attributes) {
                result[attr.name] = attr.value;
            }
            return result;
        }''')
        for key, value in attrs.items():
            print(f"   {key}: {value[:80] if len(str(value)) > 80 else value}")
    
    browser.close()
    
print("\n✅ HTML captured - analyze data/review_element.html to find backup selectors")
