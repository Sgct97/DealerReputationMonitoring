"""
Google Reviews Scraper
Uses Playwright to scrape reviews from a Google Business Profile.
"""

from playwright.sync_api import sync_playwright, Browser, Page
from typing import List, Dict, Optional
import time
import random


# SELECTOR CONFIGURATION - Update here if Google changes their UI
# 
# HOW TO TEST FALLBACKS:
# To test a fallback selector, simply comment out the ones above it.
# Example: To test if 'div[data-review-id]' works as backup:
#   Comment out 'div.GHT2ce' and run the scraper
#   If it still works, the fallback is good!
#
SELECTORS = {
    'REVIEW_CONTAINER': [
        'div.GHT2ce',                    # PRIMARY - Verified working
    ],
    'REVIEWER_NAME': [
        'button.al6Kxe div.d4r55',       # PRIMARY - Verified working
    ],
    'REVIEW_TEXT': [
        'span.wiI7pd',                   # PRIMARY - Verified working
    ],
    'STAR_RATING': [
        'span.kvMYJc[aria-label]',       # PRIMARY
        'span[role="img"][aria-label]',  # BACKUP - VERIFIED WORKING ✅
        'span[aria-label*="star"]'       # BACKUP - VERIFIED WORKING ✅
    ],
    'REVIEW_DATE': [
        'span.rsqaWe',                   # PRIMARY
    ],
    'MORE_BUTTON': [
        'button.w8nwRe',                 # PRIMARY
        'button:has-text("More")'        # BACKUP - VERIFIED WORKING ✅
    ]
}

# TO TEST A FALLBACK:
# 1. Comment out selectors above the one you want to test
# 2. Run: ./venv/bin/python3 test_scraping_only.py
# 3. Check if it still works - if yes, that fallback is valid!
# 4. Uncomment the selectors you commented out


class GoogleReviewsScraper:
    """Scrapes reviews from a Google Business Profile."""
    
    def __init__(self, proxy_config: Optional[Dict] = None, max_retries: int = 3):
        """
        Initialize the scraper.
        
        Args:
            proxy_config: Dictionary with proxy settings (server, username, password)
            max_retries: Maximum number of retry attempts if scraping fails (default: 3)
        """
        self.proxy_config = proxy_config
        self.max_retries = max_retries
        self.playwright = None
        self.browser = None
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def start(self):
        """Start the browser."""
        self.playwright = sync_playwright().start()
        
        # Configure browser launch options
        launch_options = {
            'headless': True,  # Must be True for Docker/server environments
            'args': [
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
            ]
        }
        
        # Add proxy if configured
        if self.proxy_config:
            launch_options['proxy'] = {
                'server': self.proxy_config['server'],
                'username': self.proxy_config.get('username'),
                'password': self.proxy_config.get('password')
            }
        
        self.browser = self.playwright.chromium.launch(**launch_options)
    
    def close(self):
        """Close the browser and cleanup."""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
    
    def _random_delay(self, min_seconds: float = 1.0, max_seconds: float = 3.0):
        """Add a random delay to mimic human behavior."""
        time.sleep(random.uniform(min_seconds, max_seconds))
    
    def _try_selectors(self, element, selector_list: List[str], get_text: bool = True):
        """
        Try multiple selectors in order until one works.
        
        Args:
            element: Playwright element to search within
            selector_list: List of selectors to try
            get_text: If True, return inner_text(), else return the element
        
        Returns:
            Text content or element if found, None otherwise
        """
        for selector in selector_list:
            try:
                found = element.query_selector(selector)
                if found:
                    if get_text:
                        text = found.inner_text().strip()
                        if text:
                            return text
                    else:
                        return found
            except:
                continue
        return None
    
    def scrape_reviews(self, business_url: str, db_manager=None, dealership_id: int = None, stop_at_seen: int = 3, scrape_all: bool = False, max_reviews: int = 75, star_ratings_to_track: list = [1], skip_report_urls: bool = False) -> List[Dict]:
        """
        Scrape reviews with automatic retry logic and graceful degradation.
        
        Args:
            business_url: URL of the Google Business Profile
            db_manager: Optional DatabaseManager to check for existing reviews
            dealership_id: Optional dealership ID for duplicate checking (used with db_manager)
            stop_at_seen: Stop scrolling after finding this many consecutive seen reviews (default: 3)
            scrape_all: If True, scrape ALL reviews regardless of database (for initial run). Default: False
            max_reviews: Maximum reviews to scrape in initial run. 0 = unlimited. Default: 75
            star_ratings_to_track: List of star ratings to track (e.g., [1], [1,2], [1,2,3]). Default: [1]
            skip_report_urls: If True, skip Pass 2 (don't click report URLs). Useful for initial runs. Default: False
        
        Returns:
            List of dictionaries, each containing review data
        """
        # Retry logic with exponential backoff and proxy fallback
        proxy_failed = False
        for attempt in range(self.max_retries):
            try:
                if attempt > 0:
                    wait_time = (2 ** attempt) * 5  # 10s, 20s, 40s
                    print(f"\n🔄 Retry attempt {attempt + 1}/{self.max_retries} (waiting {wait_time}s first...)")
                    time.sleep(wait_time)
                
                # If proxy failed and this is the last attempt, try without proxy
                if proxy_failed and attempt == self.max_retries - 1:
                    print("⚠️  Proxy connection failed on all attempts. Trying final attempt WITHOUT proxy...")
                    original_proxy = self.proxy_config
                    self.proxy_config = None
                    if self.browser:
                        self.close()
                    self.start()
                    
                    try:
                        reviews = self._scrape_reviews_internal(business_url, db_manager, dealership_id, stop_at_seen, scrape_all, max_reviews, star_ratings_to_track, skip_report_urls)
                    finally:
                        # Restore proxy config for next run
                        self.proxy_config = original_proxy
                        if self.browser:
                            self.close()
                        self.start()
                else:
                    reviews = self._scrape_reviews_internal(business_url, db_manager, dealership_id, stop_at_seen, scrape_all, max_reviews, star_ratings_to_track, skip_report_urls)
                
                if reviews:  # Success!
                    return reviews
                elif attempt < self.max_retries - 1:
                    print(f"⚠️ Got 0 reviews - retrying...")
                    
            except Exception as e:
                error_msg = str(e)
                print(f"❌ Attempt {attempt + 1} failed: {error_msg}")
                
                # Check if it's a proxy connection error
                if "ERR_TUNNEL_CONNECTION_FAILED" in error_msg:
                    print("🚫 Detected proxy connection failure")
                    proxy_failed = True
                
                if attempt == self.max_retries - 1:
                    # Last attempt failed - log and raise
                    print(f"💥 All {self.max_retries} attempts failed")
                    raise
        
        return []
    
    def _scrape_reviews_internal(self, business_url: str, db_manager=None, dealership_id: int = None, stop_at_seen: int = 3, scrape_all: bool = False, max_reviews: int = 75, star_ratings_to_track: list = [1], skip_report_urls: bool = False) -> List[Dict]:
        """
        Internal scraping logic (called by scrape_reviews with retry wrapper).
        """
        if not self.browser:
            self.start()
        
        # Create a new context with realistic settings
        context = self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/New_York'
        )
        
        # Enable stealth mode
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        page = context.new_page()
        
        try:
            from datetime import datetime
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Navigating to: {business_url}")
            page.goto(business_url, wait_until='domcontentloaded', timeout=60000)  # 60s timeout for slower Docker environments
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ Page loaded")
            
            self._random_delay(2, 4)
            
            # Click on the reviews tab
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Looking for reviews tab...")
            try:
                reviews_button = page.locator('button:has-text("Reviews")').first
                reviews_button.click()
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ Clicked reviews tab")
                self._random_delay(2, 3)
            except Exception as e:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Could not click reviews tab: {e}")
            
            # Wait for reviews to load using fallback selectors
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Waiting for reviews to load...")
            reviews_loaded = False
            for selector in SELECTORS['REVIEW_CONTAINER']:
                try:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}]   Trying selector: {selector}")
                    page.wait_for_selector(selector, timeout=10000)
                    reviews_loaded = True
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ Reviews loaded using: {selector}")
                    break
                except Exception as selector_error:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}]   ✗ Failed: {selector_error}")
                    continue
            
            if not reviews_loaded:
                # Comprehensive diagnostics before failing
                print(f"\n{'='*60}")
                print(f"❌ FAILURE DIAGNOSTICS")
                print(f"{'='*60}")
                print(f"Current URL: {page.url}")
                print(f"Page title: {page.title()}")
                
                # Take screenshot for debugging
                try:
                    screenshot_path = 'data/failure_screenshot.png'
                    page.screenshot(path=screenshot_path)
                    print(f"Screenshot saved: {screenshot_path}")
                except Exception as screenshot_error:
                    print(f"Could not save screenshot: {screenshot_error}")
                
                # Check for error messages on page
                try:
                    error_texts = page.locator('text=/error|blocked|captcha|unusual traffic/i').all()
                    if error_texts:
                        print(f"Error messages found on page: {len(error_texts)}")
                        for i, err in enumerate(error_texts[:3]):  # Show first 3
                            try:
                                print(f"  - {err.text_content()[:100]}")
                            except:
                                pass
                except:
                    pass
                
                print(f"{'='*60}\n")
                raise Exception("Reviews did not load - all selectors failed")
            
            # Click the sort button
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Clicking sort button...")
            try:
                sort_button = page.locator('button:has-text("Sort")').first
                sort_button.click(timeout=10000)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ Clicked sort button")
                self._random_delay(1, 2)
                
                # Click "Lowest rating" option from the dropdown
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Selecting 'Lowest rating' option...")
                lowest_rating_option = page.locator('div[role="menuitemradio"]:has-text("Lowest")').first
                lowest_rating_option.click(timeout=10000)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ Selected lowest rating")
                self._random_delay(2, 3)
                
            except Exception as e:
                print(f"⚠️ Could not sort by lowest rating: {e}")
                print("📊 GRACEFUL DEGRADATION: Continuing with default sort (newest first)")
                print("   Will still capture reviews, just not sorted by lowest rating")
            
            # Simple aggressive scrolling - just keep scrolling until we hit the limit or max scrolls
            mode_text = f"scrape all mode - limit: {'UNLIMITED' if max_reviews == 0 else max_reviews}" if scrape_all else "stop at known reviews"
            print(f"Scrolling to load reviews... ({mode_text})")
            
            scroll_count = 0
            
            print(f"Will scroll until all 1-star reviews are loaded...")
            
            while True:
                # Use keyboard to scroll
                page.keyboard.press('PageDown')
                page.keyboard.press('PageDown')
                page.keyboard.press('PageDown')
                
                # Wait 2-3 seconds
                self._random_delay(2, 3)
                scroll_count += 1
                
                # Get current reviews using first available selector
                current_elements = page.query_selector_all(SELECTORS['REVIEW_CONTAINER'][0])
                
                # Progress update
                if scroll_count % 5 == 0:
                    print(f"   Progress: {scroll_count} scrolls, ~{len(current_elements) // 2} reviews loaded...")
                
                # SMART DETECTION: Check if we've moved past tracked star ratings
                # Determine the max rating we're tracking
                max_tracked_rating = max(star_ratings_to_track) if star_ratings_to_track else 1
                
                # Look at the last 10 review elements
                above_threshold_count = 0
                for elem in current_elements[-10:]:
                    try:
                        star_rating = self._parse_star_rating(elem)
                        if star_rating > max_tracked_rating:  # Above our threshold
                            above_threshold_count += 1
                    except:
                        pass
                
                # If we see 5+ reviews above our threshold in the last 10, we've passed our target section
                if scroll_count % 10 == 0:  # Debug every 10 scrolls
                    print(f"   [Star check: {above_threshold_count}/10 recent reviews are above {max_tracked_rating}-star]")
                
                if above_threshold_count >= 5:
                    ratings_str = ','.join(map(str, sorted(star_ratings_to_track)))
                    print(f"✓ Reached end of {ratings_str}-star reviews (found {above_threshold_count}/10 recent reviews above threshold)")
                    break
                
                # Check if we hit review limit (for capped mode)
                if scrape_all and max_reviews > 0:
                    approx_reviews = len(current_elements) // 2
                    if approx_reviews >= max_reviews:
                        print(f"✓ Reached review limit ({max_reviews} reviews)")
                        break
            
            # Get final count using first available selector
            current_elements = page.query_selector_all(SELECTORS['REVIEW_CONTAINER'][0])
            print(f"Scrolled {scroll_count} times, found {len(current_elements)} review elements")
            
            # Expand all "More" buttons to get full review text using robust fallback
            print("[DIAG] Starting More button expansion phase...")
            print("Expanding reviews to get full text...")
            more_buttons = None
            for selector in SELECTORS['MORE_BUTTON']:
                try:
                    buttons = page.query_selector_all(selector)
                    if buttons and len(buttons) > 0:
                        more_buttons = buttons
                        print(f"✓ Found {len(more_buttons)} 'More' buttons using: {selector}")
                        break
                except:
                    continue
            
            if not more_buttons:
                print("⚠️ No 'More' buttons found")
                print("📊 GRACEFUL DEGRADATION: Reviews might be collapsed - will use truncated text")
                more_buttons = []
            
            expanded_count = 0
            failed_count = 0
            not_visible_count = 0
            for idx, button in enumerate(more_buttons):
                try:
                    # Scroll button into view before checking visibility/clicking
                    button.scroll_into_view_if_needed()
                    self._random_delay(0.1, 0.2)  # Small delay after scroll
                    
                    if button.is_visible():
                        button.click()
                        expanded_count += 1
                        self._random_delay(0.2, 0.5)
                    else:
                        not_visible_count += 1
                except Exception as e:
                    # Some buttons might not be clickable - log for debugging
                    failed_count += 1
                    if failed_count <= 5:  # Show first 5 failures for debugging
                        print(f"  ⚠️ More button {idx+1} failed: {type(e).__name__}: {str(e)}")
            
            print(f"📊 More button expansion summary:")
            print(f"   - Total buttons found: {len(more_buttons)}")
            print(f"   - Successfully clicked: {expanded_count}")
            print(f"   - Not visible: {not_visible_count}")
            print(f"   - Failed to click: {failed_count}")
            
            if expanded_count > 0:
                print(f"✓ Expanded {expanded_count}/{len(more_buttons)} reviews")
            else:
                print("⚠️ Could not expand reviews - using truncated text")
            
            # Wait for DOM to stabilize after all More button clicks
            print("[DIAG] More expansion done, waiting for render...")
            print("⏳ Waiting for text expansion to complete...")
            # Docker/Render environments need more time for JS rendering
            # Min 20s base + 1s per expansion (max 45s total)
            wait_time = min(45, max(20, expanded_count * 1.0))
            print(f"   (waiting {wait_time:.1f} seconds for {expanded_count} expansions to render)")
            time.sleep(wait_time)
            
            print("[DIAG] Starting review extraction...")
            # Extract review data (will capture report URL for each review unless skip_report_urls=True)
            reviews_from_lowest = self._extract_reviews(page, context, db_manager, dealership_id, star_ratings_to_track, skip_report_urls)
            
            print(f"[DIAG] Extraction complete, got {len(reviews_from_lowest)} reviews from 'Lowest rating' sort")
            
            # FINAL SAFETY CHECK: Switch to "Newest" sort to catch reviews stuck in moderation/indexing
            print(f"\n{'='*60}")
            print(f"🔍 FINAL CHECK: Scanning 'Newest' sort for missed low-star reviews")
            print(f"{'='*60}")
            
            try:
                # Click sort button to open dropdown
                print("📋 Switching to 'Newest' sort...")
                sort_button = page.locator("button[data-value='Sort']").first
                if sort_button.is_visible():
                    sort_button.click()
                    self._random_delay(1, 2)
                    
                    # Click "Newest" option
                    newest_option = page.locator("div[data-index='1']").first  # "Newest" is typically index 1
                    if newest_option.is_visible():
                        newest_option.click()
                        print("✓ Switched to 'Newest' sort")
                        self._random_delay(2, 3)  # Initial wait for sort to trigger
                        
                        # CRITICAL: Wait for review containers to load after sort change
                        print("⏳ Waiting for reviews to reload after sort change...")
                        print(f"   [DEBUG] Looking for selector: {SELECTORS['REVIEW_CONTAINER'][0]}")
                        try:
                            page.wait_for_selector(SELECTORS['REVIEW_CONTAINER'][0], timeout=30000)
                            print("   ✓ Review containers found via wait_for_selector")
                        except Exception as wait_err:
                            print(f"   ⚠️ wait_for_selector failed: {wait_err}")
                            print(f"   → Attempting manual check...")
                        
                        # Verify containers are actually present
                        test_elements = page.query_selector_all(SELECTORS['REVIEW_CONTAINER'][0])
                        print(f"   [DEBUG] Found {len(test_elements)} review containers after sort switch")
                        
                        if len(test_elements) == 0:
                            print(f"   ⚠️ WARNING: No review containers found!")
                            print(f"   [DEBUG] Page URL: {page.url}")
                            print(f"   [DEBUG] Taking diagnostic screenshot...")
                            page.screenshot(path='data/newest_sort_failed.png')
                        
                        self._random_delay(2, 3)  # Additional stabilization time
                        print("✓ Reviews reloaded, proceeding with scroll")
                        
                        # Limited scroll (covers ~50-100 most recent reviews)
                        print("📜 Scrolling to load recent reviews...")
                        newest_scroll_count = 10  # Fixed limit
                        for i in range(newest_scroll_count):
                            page.keyboard.press('PageDown')
                            page.keyboard.press('PageDown')
                            self._random_delay(1, 2)
                        
                        print(f"✓ Scrolled {newest_scroll_count} times in 'Newest' sort")
                        
                        # Verify containers again after scrolling
                        test_elements_after = page.query_selector_all(SELECTORS['REVIEW_CONTAINER'][0])
                        print(f"   [DEBUG] Found {len(test_elements_after)} review containers after scrolling")
                        
                        # Expand "More" buttons for these reviews
                        print("🔽 Expanding 'More' buttons for recent reviews...")
                        more_buttons_newest = page.query_selector_all(SELECTORS['MORE_BUTTON'][0])
                        expanded_newest = 0
                        for button in more_buttons_newest[:100]:  # Limit to first 100
                            try:
                                if button.is_visible():
                                    button.scroll_into_view_if_needed()
                                    button.click()
                                    expanded_newest += 1
                            except:
                                pass
                        
                        if expanded_newest > 0:
                            print(f"✓ Expanded {expanded_newest} reviews from 'Newest' sort")
                            # Wait for expansion
                            wait_time = min(30, max(10, expanded_newest * 0.5))
                            print(f"   (waiting {wait_time:.1f} seconds for expansions to render)")
                            time.sleep(wait_time)
                        
                        # Extract reviews from "Newest" sort (WITH Pass 2 for new reviews)
                        print("📊 Extracting reviews from 'Newest' sort...")
                        print(f"   [DEBUG] Calling _extract_reviews for 'Newest' sort")
                        print(f"   [DEBUG] star_ratings_to_track: {star_ratings_to_track}")
                        print(f"   [DEBUG] skip_report_urls: {skip_report_urls}")
                        reviews_from_newest = self._extract_reviews(page, context, db_manager=None, dealership_id=None, star_ratings_to_track=star_ratings_to_track, skip_report_urls=skip_report_urls)
                        print(f"   [DEBUG] _extract_reviews returned {len(reviews_from_newest)} total reviews")
                        
                        # Filter to only low-star reviews
                        reviews_from_newest = [r for r in reviews_from_newest if r['star_rating'] in star_ratings_to_track]
                        print(f"✓ Found {len(reviews_from_newest)} low-star reviews from 'Newest' sort")
                        
                        # Merge with "Lowest rating" results (dedupe by reviewer name, keep longest text)
                        if reviews_from_newest:
                            print("🔄 Merging with 'Lowest rating' results...")
                            seen_reviewers = {}
                            
                            # Add all from "Lowest rating" first (priority)
                            for review in reviews_from_lowest:
                                name = review['reviewer_name']
                                seen_reviewers[name] = review
                            
                            # Add from "Newest" only if not seen, or if text is longer
                            added_from_newest = 0
                            for review in reviews_from_newest:
                                name = review['reviewer_name']
                                if name not in seen_reviewers:
                                    seen_reviewers[name] = review
                                    added_from_newest += 1
                                else:
                                    # Keep version with more text
                                    old_len = len(seen_reviewers[name].get('review_text', ''))
                                    new_len = len(review.get('review_text', ''))
                                    if new_len > old_len:
                                        seen_reviewers[name] = review
                            
                            reviews_from_lowest = list(seen_reviewers.values())
                            
                            if added_from_newest > 0:
                                print(f"✅ Added {added_from_newest} NEW low-star reviews from 'Newest' sort")
                            else:
                                print(f"✓ No new reviews found in 'Newest' sort (all already captured)")
                        else:
                            print("✓ No additional low-star reviews found in 'Newest' sort")
                    else:
                        print("⚠️ Could not find 'Newest' option - skipping final check")
                else:
                    print("⚠️ Could not find sort button - skipping final check")
                    
            except Exception as newest_error:
                print(f"⚠️ 'Newest' sort check failed: {newest_error}")
                print(f"   → Continuing with {len(reviews_from_lowest)} reviews from 'Lowest rating' sort")
            
            print(f"\n✓ Total reviews after final check: {len(reviews_from_lowest)}")
            
            return reviews_from_lowest
            
        except Exception as e:
            print(f"Error during scraping: {str(e)}")
            # Take a screenshot for debugging
            page.screenshot(path='data/error_screenshot.png')
            raise
        
        finally:
            context.close()
    
    def _extract_reviews(self, page: Page, context, db_manager=None, dealership_id: int = None, star_ratings_to_track: list = [1], skip_report_urls: bool = False) -> List[Dict]:
        """
        Extract review data from the page using two-pass approach:
        Pass 1: Extract all text data while DOM is stable
        Pass 1.5: Check which reviews already exist in database (OPTIMIZATION)
        Pass 2: Add report URLs by clicking (ONLY for new reviews)
        
        Args:
            page: Playwright page object
            context: Playwright context object
            db_manager: Optional DatabaseManager to check for existing reviews
            dealership_id: Optional dealership ID for duplicate checking
            star_ratings_to_track: List of star ratings to track (for filtering before duplication check)
        
        Returns:
            List of review dictionaries
        """
        # Find all review containers using multiple fallback selectors
        review_elements = None
        print(f"[DEBUG] Attempting to find review containers...")
        print(f"[DEBUG] Available selectors: {SELECTORS['REVIEW_CONTAINER']}")
        
        for idx, selector in enumerate(SELECTORS['REVIEW_CONTAINER']):
            try:
                print(f"[DEBUG] Trying selector {idx+1}/{len(SELECTORS['REVIEW_CONTAINER'])}: {selector}")
                elements = page.query_selector_all(selector)
                print(f"[DEBUG] Selector returned {len(elements)} elements")
                if elements and len(elements) > 0:
                    review_elements = elements
                    print(f"✓ Using review container selector: {selector}")
                    break
                else:
                    print(f"[DEBUG] Selector found 0 elements, trying next...")
            except Exception as sel_err:
                print(f"[DEBUG] Selector failed with error: {sel_err}")
                continue
        
        if not review_elements:
            print(f"[DEBUG] FAILURE: No selectors found any review containers")
            print(f"[DEBUG] Page URL: {page.url}")
            print(f"[DEBUG] Page title: {page.title()}")
            raise Exception("Could not find review containers with any known selector")
        
        print(f"Found {len(review_elements)} review elements")
        
        # PASS 1: Extract all text data (NO clicking report URLs)
        print("📝 Pass 1: Extracting text data...")
        print(f"[DIAG] Processing {len(review_elements)} elements...")
        reviews = []
        
        for idx, element in enumerate(review_elements):
            # Log progress every 50 elements to track where it crashes
            if idx > 0 and idx % 50 == 0:
                print(f"[DIAG] Processed {idx}/{len(review_elements)} elements, {len(reviews)} valid reviews so far...")
            try:
                # Extract reviewer name using robust fallback selectors
                reviewer_name = self._try_selectors(element, SELECTORS['REVIEWER_NAME'])
                
                # If no name found, try previous element (reviews come in pairs)
                if not reviewer_name and idx > 0:
                    reviewer_name = self._try_selectors(review_elements[idx - 1], SELECTORS['REVIEWER_NAME'])
                
                if not reviewer_name:
                    reviewer_name = "Anonymous"
                
                # Extract star rating using robust fallback
                star_rating = self._parse_star_rating(element)
                
                # Extract review text using robust fallback
                review_text = self._try_selectors(element, SELECTORS['REVIEW_TEXT'])
                if not review_text:
                    review_text = ""
                
                # Extract review date using robust fallback
                review_date = self._try_selectors(element, SELECTORS['REVIEW_DATE'])
                if not review_date:
                    review_date = "Unknown date"
                
                # Only add if we have the essential data
                if reviewer_name and review_text:
                    # Log text length to verify More button expansion worked
                    text_len = len(review_text)
                    # Log ALL reviews with short text (likely truncated)
                    if text_len < 300:
                        print(f"  ⚠️ SHORT TEXT: {reviewer_name}: {text_len} chars")
                    
                    review = {
                        'reviewer_name': reviewer_name,
                        'star_rating': star_rating,
                        'review_text': review_text,
                        'review_date': review_date,
                        'review_url': None,  # Will be filled in Pass 2
                        'element': element   # Keep reference for Pass 2
                    }
                    reviews.append(review)
                else:
                    # Log skipped reviews for debugging
                    reason = []
                    if not reviewer_name:
                        reason.append("no name")
                    if not review_text:
                        reason.append("no text")
                    print(f"⊘ Skipped review #{idx}: {', '.join(reason)} | Rating: {star_rating}-star")
                    
            except Exception as e:
                print(f"Error extracting review #{idx}: {e}")
                continue
        
        print(f"✓ Pass 1 complete: Extracted {len(reviews)} reviews")
        
        # FILTER: Only keep reviews with tracked star ratings BEFORE checking duplicates
        # This prevents wasting time clicking report URLs for ratings we don't track
        if star_ratings_to_track:
            pre_filter_count = len(reviews)
            reviews = [r for r in reviews if r['star_rating'] in star_ratings_to_track]
            filtered_count = pre_filter_count - len(reviews)
            if filtered_count > 0:
                ratings_str = ','.join(map(str, sorted(star_ratings_to_track)))
                print(f"🔽 Filtered out {filtered_count} reviews with ratings not in [{ratings_str}]")
        
        # PASS 1.5: Check which reviews already exist in database (OPTIMIZATION)
        # This allows us to skip clicking report URLs for reviews we already have
        reviews_needing_urls = []
        
        if db_manager and dealership_id:
            print(f"\n🔍 Pass 1.5: Checking for duplicates in database...")
            
            # First, identify which star ratings are NEW for this dealership
            # This prevents clicking report URLs for reviews when user adds new ratings to track
            new_star_ratings_for_dealership = []
            for rating in star_ratings_to_track:
                if not db_manager.has_reviews_with_rating(dealership_id, rating):
                    new_star_ratings_for_dealership.append(rating)
            
            if new_star_ratings_for_dealership:
                # Only show message if we actually found reviews with these new ratings
                found_new_ratings = [r['star_rating'] for r in reviews if r['star_rating'] in new_star_ratings_for_dealership]
                if found_new_ratings:
                    unique_found = sorted(set(found_new_ratings))
                    new_ratings_str = ','.join(map(str, unique_found))
                    print(f"   📌 First time seeing {new_ratings_str}-star reviews for this dealership")
                    print(f"   → Skipping report URL collection for all {new_ratings_str}-star reviews (baseline data)")
            
            existing_count = 0
            new_count = 0
            skipped_new_rating_count = 0
            
            for review in reviews:
                # Check if this review's star rating is new to this dealership
                is_new_rating = review['star_rating'] in new_star_ratings_for_dealership
                
                if db_manager.review_exists(
                    review['reviewer_name'],
                    review['review_text'],
                    review['review_date'],
                    dealership_id
                ):
                    # Review already exists - skip clicking report URL
                    existing_count += 1
                    # Still include in results but mark as existing (no need to click)
                    review['review_url'] = None  # Will use business URL as fallback in main.py
                    del review['element']  # Don't need element reference
                elif is_new_rating:
                    # New star rating being tracked - treat as baseline (skip report URL)
                    skipped_new_rating_count += 1
                    review['review_url'] = None  # Will use business URL as fallback in main.py
                    del review['element']  # Don't need element reference
                else:
                    # New review with existing star rating - needs report URL
                    new_count += 1
                    reviews_needing_urls.append(review)
            
            print(f"✓ Found {existing_count} existing reviews (skipping URL clicks)")
            if skipped_new_rating_count > 0:
                print(f"✓ Found {skipped_new_rating_count} reviews with new star ratings (skipping URL clicks - baseline)")
            print(f"✓ Found {new_count} new reviews (will get report URLs)")
        else:
            # No db_manager or dealership_id - get URLs for all reviews (backward compatible)
            print(f"\n⚠️  No database checking - will get report URLs for all reviews")
            reviews_needing_urls = reviews
        
        # PASS 2: Add report URLs (ONLY for new reviews - OPTIMIZED!)
        # Skip Pass 2 if requested (e.g., for initial runs building baseline)
        if skip_report_urls:
            print(f"\n⏭️  Pass 2: SKIPPED (skip_report_urls=True)")
            print(f"   Note: Report URLs will be collected during incremental runs for NEW reviews only")
            # Clean up element references
            for review in reviews:
                if 'element' in review:
                    del review['element']
        else:
            print(f"\n🔗 Pass 2: Getting report URLs for {len(reviews_needing_urls)} NEW reviews...")
            
            for idx, review in enumerate(reviews_needing_urls):
                try:
                    print(f"\n  [{idx+1}/{len(reviews_needing_urls)}] Processing {review['reviewer_name']}...")
                    
                    element = review['element']
                    reviewer_name = review['reviewer_name']
                    
                    # Note: We skip element validation because is_visible() can hang on stale elements
                    # Instead, we'll catch exceptions in _get_report_url_by_clicking
                    print(f"      Calling _get_report_url_by_clicking...")
                    # Get direct report URL by clicking through the UI
                    review_url = self._get_report_url_by_clicking(element, page, context, reviewer_name)
                    review['review_url'] = review_url
                    
                    # Remove element reference (don't need it anymore)
                    del review['element']
                    
                    print(f"      ✓ Got report URL for {reviewer_name}")
                    
                except Exception as e:
                    print(f"      ❌ ERROR for {reviewer_name}: {type(e).__name__}: {str(e)}")
                    # Use fallback URL
                    review['review_url'] = page.url
                    if 'element' in review:
                        del review['element']
            
            print(f"\n✓ Pass 2 complete: Added report URLs")
        
        return reviews
    
    def _parse_star_rating(self, review_element) -> int:
        """
        Parse the star rating from a review element using robust fallback selectors.
        
        Args:
            review_element: The review container element
        
        Returns:
            Star rating as an integer (1-5)
        """
        # Try multiple selectors for star rating
        for selector in SELECTORS['STAR_RATING']:
            try:
                star_elem = review_element.query_selector(selector)
                if star_elem:
                    aria_label = star_elem.get_attribute('aria-label')
                    # aria-label is like "1 star", "2 stars", "5 stars", etc.
                    if aria_label:
                        # Extract the number from the label
                        rating_str = aria_label.split()[0]  # Get first word (the number)
                        return int(rating_str)
            except:
                continue
        
        return 0  # Default if we can't parse
    
    def _get_report_url_by_clicking(self, review_element, page, context, reviewer_name: str) -> str:
        """
        Get the direct report URL by actually clicking Report review button.
        
        Args:
            review_element: The review container element
            page: Playwright page object
            context: Playwright context object
            reviewer_name: The reviewer's name to identify the correct review
        
        Returns:
            Direct report URL, or business URL as fallback
        """
        from datetime import datetime
        from urllib.parse import urlparse, parse_qs, unquote
        
        try:
            print(f"  [{datetime.now().strftime('%H:%M:%S')}] 🔗 Getting report URL for {reviewer_name[:20]}...")
            
            # First, ensure any dropdowns are closed
            try:
                page.keyboard.press('Escape')
                page.wait_for_timeout(200)
            except:
                pass
            
            # Scroll the review into view first to ensure it's not stale
            try:
                review_element.scroll_into_view_if_needed(timeout=2000)
                page.wait_for_timeout(300)
            except:
                pass
            
            # Find the 3-dot action menu button - use PAGE level query (like capture_report_url.py that works)
            # Match by reviewer name in aria-label
            action_button = page.query_selector(f'button[aria-label*="Actions for"][aria-label*="{reviewer_name[:10]}"]')
            
            if not action_button:
                print(f"  [{datetime.now().strftime('%H:%M:%S')}]   ⚠️ No action button found for {reviewer_name}")
                return page.url
            
            print(f"  [{datetime.now().strftime('%H:%M:%S')}]   ✓ Found action button, clicking...")
            # Click the 3-dot menu
            action_button.click()
            page.wait_for_timeout(800)
            print(f"  [{datetime.now().strftime('%H:%M:%S')}]   ✓ Clicked action button")
            
            # Click "Report review" and capture new tab
            print(f"  [{datetime.now().strftime('%H:%M:%S')}]   Looking for Report review option...")
            with context.expect_page(timeout=5000) as new_page_info:
                report_item = page.locator('[role="menuitemradio"]:has-text("Report review")').first
                print(f"  [{datetime.now().strftime('%H:%M:%S')}]   Clicking Report review...")
                report_item.click(timeout=3000)
            
            print(f"  [{datetime.now().strftime('%H:%M:%S')}]   ✓ Clicked Report review, getting new page...")
            # Get the new page (sign-in redirect)
            new_page = new_page_info.value
            signin_url = new_page.url
            print(f"  [{datetime.now().strftime('%H:%M:%S')}]   ✓ Got sign-in URL, closing tab...")
            
            # Close the tab immediately
            new_page.close()
            print(f"  [{datetime.now().strftime('%H:%M:%S')}]   ✓ Tab closed, parsing URL...")
            
            # Extract the real report URL from continue parameter
            parsed = urlparse(signin_url)
            params = parse_qs(parsed.query)
            
            if 'continue' in params:
                real_report_url = unquote(params['continue'][0])
                print(f"  [{datetime.now().strftime('%H:%M:%S')}]   ✓ Got report URL!")
                return real_report_url
            else:
                print(f"  [{datetime.now().strftime('%H:%M:%S')}]   ⚠️ No continue param in URL")
                    
        except Exception as e:
            print(f"  [{datetime.now().strftime('%H:%M:%S')}]   ⚠️ Error getting report URL: {e}")
        
        # Fallback: return business page URL
        print(f"  [{datetime.now().strftime('%H:%M:%S')}]   Using fallback URL")
        return page.url
    
    def filter_one_star_reviews(self, reviews: List[Dict]) -> List[Dict]:
        """
        Filter reviews to only include 1-star ratings.
        
        Args:
            reviews: List of all reviews
        
        Returns:
            List of only 1-star reviews
        """
        return [review for review in reviews if review.get('star_rating') == 1]
    
    def filter_reviews_by_rating(self, reviews: List[Dict], star_ratings: List[int]) -> List[Dict]:
        """
        Filter reviews to only include specified star ratings.
        
        Args:
            reviews: List of all reviews
            star_ratings: List of star ratings to keep (e.g., [1], [1,2])
        
        Returns:
            List of reviews matching the specified star ratings
        """
        return [review for review in reviews if review.get('star_rating') in star_ratings]
