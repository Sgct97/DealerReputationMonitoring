"""
Google Reviews Scraper
Uses Playwright to scrape reviews from a Google Business Profile.
"""

from playwright.sync_api import sync_playwright, Browser, Page
from typing import List, Dict, Optional
import time
import random


class GoogleReviewsScraper:
    """Scrapes reviews from a Google Business Profile."""
    
    def __init__(self, proxy_config: Optional[Dict] = None):
        """
        Initialize the scraper.
        
        Args:
            proxy_config: Dictionary with proxy settings (server, username, password)
        """
        self.proxy_config = proxy_config
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
            'headless': False,  # Set to False to see the browser
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
    
    def scrape_reviews(self, business_url: str, db_manager=None, stop_at_seen: int = 3, scrape_all: bool = False, max_reviews: int = 75, star_ratings_to_track: list = [1]) -> List[Dict]:
        """
        Scrape reviews from a Google Business Profile with intelligent scrolling.
        
        Args:
            business_url: URL of the Google Business Profile
            db_manager: Optional DatabaseManager to check for existing reviews
            stop_at_seen: Stop scrolling after finding this many consecutive seen reviews (default: 3)
            scrape_all: If True, scrape ALL reviews regardless of database (for initial run). Default: False
            max_reviews: Maximum reviews to scrape in initial run. 0 = unlimited. Default: 75
            star_ratings_to_track: List of star ratings to track (e.g., [1], [1,2], [1,2,3]). Default: [1]
        
        Returns:
            List of dictionaries, each containing review data
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
            print(f"Navigating to: {business_url}")
            page.goto(business_url, wait_until='domcontentloaded', timeout=30000)
            
            self._random_delay(2, 4)
            
            # Click on the reviews tab
            print("Looking for reviews tab...")
            try:
                reviews_button = page.locator('button:has-text("Reviews")').first
                reviews_button.click()
                print("✓ Clicked reviews tab")
                self._random_delay(2, 3)
            except Exception as e:
                print(f"Could not click reviews tab (might already be there): {e}")
            
            # Wait for reviews to load
            print("Waiting for reviews to load...")
            page.wait_for_selector('div.GHT2ce', timeout=10000)
            
            # Click the sort button
            print("Clicking sort button...")
            try:
                sort_button = page.locator('button:has-text("Sort")').first
                sort_button.click()
                print("✓ Clicked sort button")
                self._random_delay(1, 2)
                
                # Click "Lowest rating" option from the dropdown
                print("Selecting 'Lowest rating' option...")
                # The dropdown menu should now be visible
                lowest_rating_option = page.locator('div[role="menuitemradio"]:has-text("Lowest")').first
                lowest_rating_option.click()
                print("✓ Selected lowest rating")
                self._random_delay(2, 3)
                
            except Exception as e:
                print(f"Could not sort by lowest rating: {e}")
                print("Continuing with default sort order...")
            
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
                
                # Get current reviews
                current_elements = page.query_selector_all('div.GHT2ce')
                
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
                
                # Safety limit (very high for unlimited mode)
                safety_limit = 500 if max_reviews == 0 else 100
                if scroll_count >= safety_limit:
                    print(f"⚠️  Reached safety limit of {safety_limit} scrolls")
                    break
            
            # Get final count
            current_elements = page.query_selector_all('div.GHT2ce')
            print(f"Scrolled {scroll_count} times, found {len(current_elements)} review elements")
            
            # Expand all "More" buttons to get full review text
            print("Expanding reviews to get full text...")
            more_buttons = page.query_selector_all('button.w8nwRe')  # "More" button class
            print(f"Found {len(more_buttons)} 'More' buttons to click")
            for idx, button in enumerate(more_buttons):
                try:
                    if button.is_visible():
                        button.click()
                        self._random_delay(0.2, 0.5)  # Short delay between clicks
                except Exception as e:
                    # Some buttons might not be clickable, that's okay
                    pass
            
            print("✓ All reviews expanded")
            self._random_delay(1, 2)
            
            # Extract review data
            reviews = self._extract_reviews(page)
            
            print(f"Successfully scraped {len(reviews)} reviews")
            
            return reviews
            
        except Exception as e:
            print(f"Error during scraping: {str(e)}")
            # Take a screenshot for debugging
            page.screenshot(path='data/error_screenshot.png')
            raise
        
        finally:
            context.close()
    
    def _extract_reviews(self, page: Page) -> List[Dict]:
        """
        Extract review data from the page.
        
        Args:
            page: Playwright page object
        
        Returns:
            List of review dictionaries
        """
        reviews = []
        
        # Find all review containers
        review_elements = page.query_selector_all('div.GHT2ce')
        
        print(f"Found {len(review_elements)} review elements")
        
        for idx, element in enumerate(review_elements):
            try:
                
                # Extract reviewer name (inside button element)
                # Try multiple selectors to find the name
                name_selectors = [
                    'button.al6Kxe div.d4r55',  # More specific - the reviewer button
                    'button div.d4r55',
                    'div.d4r55.fontTitleMedium',
                    'div.d4r55'
                ]
                
                reviewer_name = "Anonymous"
                for selector in name_selectors:
                    name_elem = element.query_selector(selector)
                    if name_elem:
                        text = name_elem.inner_text().strip()
                        if text and text != "":
                            reviewer_name = text
                            break
                
                # If no name found, try to get it from the previous sibling element (reviews come in pairs)
                if reviewer_name == "Anonymous" and idx > 0:
                    prev_elem = review_elements[idx - 1]
                    for selector in name_selectors:
                        name_elem = prev_elem.query_selector(selector)
                        if name_elem:
                            text = name_elem.inner_text().strip()
                            if text and text != "":
                                reviewer_name = text
                                break
                        if reviewer_name != "Anonymous":
                            break
                
                # Extract star rating from aria-label
                star_rating = self._parse_star_rating(element)
                
                # Extract review text
                text_elem = element.query_selector('span.wiI7pd')
                review_text = text_elem.inner_text() if text_elem else ""
                
                # Extract review date
                date_elem = element.query_selector('span.rsqaWe')
                review_date = date_elem.inner_text() if date_elem else "Unknown date"
                
                # Get review URL
                review_url = page.url
                
                # Only add if we have the essential data
                if reviewer_name and review_text:
                    review = {
                        'reviewer_name': reviewer_name,
                        'star_rating': star_rating,
                        'review_text': review_text,
                        'review_date': review_date,
                        'review_url': review_url
                    }
                    reviews.append(review)
                    
            except Exception as e:
                print(f"Error extracting review: {e}")
                continue
        
        return reviews
    
    def _parse_star_rating(self, review_element) -> int:
        """
        Parse the star rating from a review element.
        
        Args:
            review_element: The review container element
        
        Returns:
            Star rating as an integer (1-5)
        """
        try:
            # Find the star rating element with aria-label
            star_elem = review_element.query_selector('span.kvMYJc[aria-label]')
            if star_elem:
                aria_label = star_elem.get_attribute('aria-label')
                # aria-label is like "1 star", "2 stars", "5 stars", etc.
                if aria_label:
                    # Extract the number from the label
                    rating_str = aria_label.split()[0]  # Get first word (the number)
                    return int(rating_str)
        except:
            pass
        
        return 0  # Default if we can't parse
    
    def _get_review_url(self, review_element, page_url: str) -> str:
        """
        Get a direct URL to the review (if possible).
        
        Args:
            review_element: The review container element
            page_url: The current page URL
        
        Returns:
            URL string
        """
        # TODO: Determine if we can get a direct link to individual reviews
        # Otherwise, return the business profile URL
        
        return page_url  # Placeholder
    
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
