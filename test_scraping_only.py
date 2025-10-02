"""
Test ONLY Scraping - No AI, No API Costs
Just scrape reviews and save to database to verify we get ALL 1-star reviews.
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
    """Test scraping only."""
    
    # Load environment variables
    load_dotenv()
    
    # Get configuration
    business_url = os.getenv('GOOGLE_BUSINESS_URL')
    database_path = './data/reviews_scrape_test.db'
    
    # Parse star ratings to track
    star_ratings_str = os.getenv('STAR_RATINGS_TO_TRACK', '1')
    star_ratings_to_track = [int(x.strip()) for x in star_ratings_str.split(',')]
    
    # Proxy configuration
    proxy_server = os.getenv('PROXY_SERVER')
    proxy_username = os.getenv('PROXY_USERNAME')
    proxy_password = os.getenv('PROXY_PASSWORD')
    
    if not business_url:
        print("❌ Error: GOOGLE_BUSINESS_URL not set")
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
    
    # Ensure data directory exists
    data_dir = Path(database_path).parent
    data_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("🧪 SCRAPING ONLY TEST (No AI - No API Costs)")
    print("=" * 60)
    
    # Initialize database
    print("\n📊 Initializing database...")
    db = DatabaseManager(database_path)
    
    ratings_str = ','.join(map(str, star_ratings_to_track))
    print(f"\n🔍 Scraping ALL {ratings_str}-star reviews from: {business_url}")
    print("⏳ This may take a while...")
    
    try:
        with GoogleReviewsScraper(proxy_config) as scraper:
            # UNLIMITED MODE
            all_reviews = scraper.scrape_reviews(business_url, db_manager=db, scrape_all=True, max_reviews=0, star_ratings_to_track=star_ratings_to_track)
            
            if not all_reviews:
                print("⚠️  No reviews found")
                return
            
            print(f"\n✓ Scraped {len(all_reviews)} total reviews")
            
            # Show star rating breakdown BEFORE filtering
            star_breakdown = {}
            for review in all_reviews:
                rating = review.get('star_rating', 0)
                star_breakdown[rating] = star_breakdown.get(rating, 0) + 1
            
            print(f"\n📊 Star Rating Breakdown (all scraped reviews):")
            for stars in sorted(star_breakdown.keys()):
                print(f"   {stars}-star: {star_breakdown[stars]} reviews")
            
            # Filter for tracked star ratings
            tracked_reviews = scraper.filter_reviews_by_rating(all_reviews, star_ratings_to_track)
            print(f"\n✓ Filtering to keep only {ratings_str}-star reviews: {len(tracked_reviews)} reviews")
            
            # Save to database (NO AI ANALYSIS)
            new_count = 0
            for review in tracked_reviews:
                if not db.review_exists(review['reviewer_name'], review['review_text'], review['review_date']):
                    db.add_review(review)
                    new_count += 1
            
            print(f"\n✓ Saved {new_count} new reviews to database")
            
            stats = db.get_stats()
            print(f"\n📊 Total reviews in database: {stats['total_reviews']}")
            print(f"⭐ Reviews with tracked ratings ({ratings_str}-star): {stats['one_star_reviews']}")
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("\n✅ Test completed")
    print("=" * 60)


if __name__ == "__main__":
    main()

