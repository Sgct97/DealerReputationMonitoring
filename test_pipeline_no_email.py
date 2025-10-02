"""
Test Pipeline Without Email
Tests scraping → database → AI analysis pipeline without sending emails.
"""

import os
import sys
from dotenv import load_dotenv
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from scraper.scraper import GoogleReviewsScraper
from database.db_manager import DatabaseManager
from ai.analyzer import ReviewAnalyzer


def main():
    """Test the pipeline without email notifications."""
    
    # Load environment variables
    load_dotenv()
    
    # Get configuration from environment
    business_url = os.getenv('GOOGLE_BUSINESS_URL')
    openai_api_key = os.getenv('OPENAI_API_KEY')
    database_path = os.getenv('DATABASE_PATH', './data/reviews_test.db')
    initial_scrape_limit = int(os.getenv('INITIAL_SCRAPE_LIMIT', '75'))  # 0 = unlimited
    
    # Proxy configuration (optional)
    proxy_server = os.getenv('PROXY_SERVER')
    proxy_username = os.getenv('PROXY_USERNAME')
    proxy_password = os.getenv('PROXY_PASSWORD')
    
    # Validate required configuration
    if not business_url:
        print("❌ Error: GOOGLE_BUSINESS_URL not set in .env file")
        sys.exit(1)
    
    if not openai_api_key:
        print("❌ Error: OPENAI_API_KEY not set in .env file")
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
    else:
        print("⚠️  Warning: No proxy configured. This may result in blocking by Google.")
    
    # Ensure data directory exists
    data_dir = Path(database_path).parent
    data_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("🧪 Testing Pipeline (NO EMAIL)")
    print("=" * 60)
    
    # Initialize components
    print("\n📊 Initializing database...")
    db = DatabaseManager(database_path)
    
    print("🤖 Initializing AI analyzer (GPT-5)...")
    analyzer = ReviewAnalyzer(openai_api_key)
    
    print("📧 Email notifications: DISABLED (test mode)")
    
    # Start scraping
    print(f"\n🔍 Scraping reviews from: {business_url}")
    
    try:
        with GoogleReviewsScraper(proxy_config) as scraper:
            # Auto-detect if this is the initial run (empty database)
            stats = db.get_stats()
            is_initial_run = stats['total_reviews'] == 0
            
            if is_initial_run:
                limit_text = "UNLIMITED" if initial_scrape_limit == 0 else f"up to {initial_scrape_limit}"
                print(f"📊 Initial run detected - will scrape {limit_text} 1-star reviews")
                all_reviews = scraper.scrape_reviews(business_url, db_manager=db, scrape_all=True, max_reviews=initial_scrape_limit)
            else:
                print("📊 Incremental run - will stop at known reviews")
                all_reviews = scraper.scrape_reviews(business_url, db_manager=db, stop_at_seen=3)
            
            if not all_reviews:
                print("⚠️  No reviews found. This could mean:")
                print("   - The page structure has changed (selectors need updating)")
                print("   - The business has no reviews yet")
                print("   - Access was blocked")
                return
            
            print(f"✓ Found {len(all_reviews)} total reviews")
            
            # Filter for 1-star reviews
            one_star_reviews = scraper.filter_one_star_reviews(all_reviews)
            print(f"✓ Found {len(one_star_reviews)} one-star reviews")
            
            # Process each 1-star review
            new_reviews_count = 0
            
            for review in one_star_reviews:
                # Check if this is a new review
                if not db.review_exists(
                    review['reviewer_name'],
                    review['review_text'],
                    review['review_date']
                ):
                    print(f"\n🆕 New 1-star review detected!")
                    print(f"   Reviewer: {review['reviewer_name']}")
                    print(f"   Date: {review['review_date']}")
                    print(f"   Rating: {review['star_rating']} star(s)")
                    print(f"   Text: {review['review_text'][:100]}..." if len(review['review_text']) > 100 else f"   Text: {review['review_text']}")
                    
                    # Add to database
                    db.add_review(review)
                    print(f"   ✓ Saved to database")
                    
                    # Analyze with AI
                    print("   🤖 Analyzing with GPT-5...")
                    ai_analysis = analyzer.analyze_review(
                        review['review_text'],
                        review['reviewer_name']
                    )
                    
                    print(f"   ✓ AI Recommendation:")
                    print(f"      Category: {ai_analysis['category']}")
                    print(f"      Reasoning: {ai_analysis['reasoning']}")
                    
                    # Mark as processed (but not notified since we're skipping email)
                    new_reviews_count += 1
                else:
                    # Review already in database
                    pass
            
            # Print summary
            print("\n" + "=" * 60)
            print("📈 Test Summary")
            print("=" * 60)
            
            if new_reviews_count > 0:
                print(f"✓ {new_reviews_count} new 1-star review(s) detected and analyzed")
            else:
                print("✓ No new 1-star reviews detected")
            
            stats = db.get_stats()
            print(f"📊 Total reviews tracked: {stats['total_reviews']}")
            print(f"⭐ Total 1-star reviews: {stats['one_star_reviews']}")
            
            print("\n💡 Note: Email notifications were skipped in this test")
            
    except Exception as e:
        print(f"\n❌ Error during execution: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("\n✅ Test completed successfully")
    print("=" * 60)


if __name__ == "__main__":
    main()

