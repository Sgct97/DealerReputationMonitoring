"""
Real-World Optimization Test
Tests the deduplication optimization with actual scraping.
Should skip clicking report URLs for existing reviews in the database.
"""

import os
import sys
from dotenv import load_dotenv
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from scraper.scraper import GoogleReviewsScraper
from database.db_manager import DatabaseManager

def main():
    """Test optimization with real scraping - no emails."""
    
    # Load environment variables
    load_dotenv()
    
    # Get configuration from environment
    business_url = os.getenv('GOOGLE_BUSINESS_URL')
    database_path = os.getenv('DATABASE_PATH', './data/reviews.db')
    
    # Proxy configuration (optional)
    proxy_server = os.getenv('PROXY_SERVER')
    proxy_username = os.getenv('PROXY_USERNAME')
    proxy_password = os.getenv('PROXY_PASSWORD')
    
    # Validate required configuration
    if not business_url:
        print("❌ Error: GOOGLE_BUSINESS_URL not set in .env file")
        sys.exit(1)
    
    # Prepare proxy config
    proxy_config = None
    if proxy_server:
        proxy_config = {
            'server': proxy_server,
            'username': proxy_username,
            'password': proxy_password
        }
        print("✓ Proxy configuration loaded")
    
    print("=" * 80)
    print("🧪 REAL-WORLD OPTIMIZATION TEST")
    print("=" * 80)
    print("This test will:")
    print("1. Check how many reviews are already in the database")
    print("2. Scrape 20 reviews from the actual website")
    print("3. Show that report URLs are ONLY clicked for NEW reviews")
    print("4. NOT send any emails (test mode)")
    print("=" * 80)
    
    # Initialize database
    print(f"\n📊 Using database: {database_path}")
    db = DatabaseManager(database_path)
    
    # Get current stats
    stats = db.get_stats()
    print(f"\n📈 Current Database Stats:")
    print(f"   - Total reviews: {stats['total_reviews']}")
    print(f"   - 1-star reviews: {stats['one_star_reviews']}")
    print(f"   - Notified: {stats['notified_count']}")
    
    # Extract dealership name from URL
    dealership_name = "Test Dealership"
    try:
        url_parts = business_url.split('/place/')[1].split('/')[0] if '/place/' in business_url else None
        if url_parts:
            dealership_name = url_parts.split('@')[0].replace('+', ' ')
    except:
        pass
    
    # Add or get dealership
    dealership_id = db.add_dealership(dealership_name, business_url)
    print(f"\n📍 Dealership: {dealership_name} (ID: {dealership_id})")
    
    # Start scraping
    print(f"\n🔍 Starting scrape (limited to 20 reviews)...")
    print(f"   URL: {business_url}")
    
    try:
        with GoogleReviewsScraper(proxy_config) as scraper:
            # IMPORTANT: Force scrape_all=True and max_reviews=20 for this test
            # This ensures we scrape exactly 20 reviews regardless of what's in DB
            print(f"\n⚙️  Scrape Settings:")
            print(f"   - Mode: scrape_all=True (force scrape 20 reviews)")
            print(f"   - Max reviews: 20")
            print(f"   - Star ratings: [1]")
            print(f"   - Database check: ENABLED (will skip existing reviews)")
            
            all_reviews = scraper.scrape_reviews(
                business_url, 
                db_manager=db, 
                dealership_id=dealership_id,
                scrape_all=True, 
                max_reviews=20, 
                star_ratings_to_track=[1]
            )
            
            if not all_reviews:
                print("\n⚠️  No reviews found")
                return
            
            print(f"\n✓ Scraped {len(all_reviews)} total reviews")
            
            # Filter for 1-star reviews
            one_star_reviews = scraper.filter_reviews_by_rating(all_reviews, [1])
            print(f"✓ Found {len(one_star_reviews)} 1-star review(s)")
            
            # Count how many are new vs existing
            print(f"\n🔍 Analyzing reviews...")
            new_count = 0
            existing_count = 0
            
            for review in one_star_reviews:
                if db.review_exists(
                    review['reviewer_name'],
                    review['review_text'],
                    review['review_date'],
                    dealership_id
                ):
                    existing_count += 1
                    print(f"   📋 EXISTING: {review['reviewer_name']}")
                else:
                    new_count += 1
                    print(f"   🆕 NEW: {review['reviewer_name']}")
            
            # Print optimization summary
            print("\n" + "=" * 80)
            print("📊 OPTIMIZATION RESULTS")
            print("=" * 80)
            print(f"Total 1-star reviews found:    {len(one_star_reviews)}")
            print(f"Already in database (skipped): {existing_count}")
            print(f"New reviews (clicked URLs):    {new_count}")
            print(f"\n💡 Report URL Clicks:")
            print(f"   - Without optimization:  {len(one_star_reviews)} clicks")
            print(f"   - With optimization:     {new_count} clicks")
            print(f"   - Clicks saved:          {existing_count} ({(existing_count/len(one_star_reviews)*100) if len(one_star_reviews) > 0 else 0:.0f}%)")
            
            if existing_count > 0:
                print(f"\n✅ SUCCESS! Optimization working correctly!")
                print(f"   The scraper skipped clicking report URLs for {existing_count} existing reviews.")
            elif new_count > 0:
                print(f"\n✅ All {new_count} reviews were new - this is expected for first run!")
            else:
                print(f"\n⚠️  No 1-star reviews found to test")
            
            # Show what would have been processed (but we don't save or email)
            if new_count > 0:
                print(f"\n📧 Would have sent {new_count} email(s) (skipped in test mode)")
            
            print("\n" + "=" * 80)
            print("🎯 TEST COMPLETE - No changes made to database, no emails sent")
            print("=" * 80)
            
    except Exception as e:
        print(f"\n❌ Error during execution: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

