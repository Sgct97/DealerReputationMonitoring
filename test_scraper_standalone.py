"""
Standalone Scraper Test
Tests the Google Reviews scraper without needing API keys.
"""

import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from scraper.scraper import GoogleReviewsScraper

def test_scraper():
    """Test the scraper with the AutoNation Ford URL."""
    
    print("=" * 60)
    print("🧪 Testing Google Reviews Scraper")
    print("=" * 60)
    
    # The URL you provided
    test_url = "https://www.google.com/maps/place/AutoNation+Ford+St.+Petersburg/@27.794611,-82.6804603,16z/data=!4m16!1m9!3m8!1s0x88c2e3bb687f7e2b:0x4ca2bbe8f85c3f98!2sAutoNation+Ford+St.+Petersburg!8m2!3d27.794611!4d-82.67788!9m1!1b1!16s%2Fg%2F1tj9v3d4!3m5!1s0x88c2e3bb687f7e2b:0x4ca2bbe8f85c3f98!8m2!3d27.794611!4d-82.67788!16s%2Fg%2F1tj9v3d4"
    
    print(f"\nTarget URL: {test_url}\n")
    
    try:
        # Create scraper (no proxy for testing)
        with GoogleReviewsScraper() as scraper:
            print("✓ Scraper initialized\n")
            
            # Scrape reviews
            all_reviews = scraper.scrape_reviews(test_url)
            
            print(f"\n✓ Scraping completed!")
            print(f"Total reviews found: {len(all_reviews)}")
            
            if all_reviews:
                # Show sample of reviews
                print("\n" + "=" * 60)
                print("Sample Reviews:")
                print("=" * 60)
                
                for i, review in enumerate(all_reviews[:3], 1):  # Show first 3
                    print(f"\n{i}. Reviewer: {review['reviewer_name']}")
                    print(f"   Rating: {'⭐' * review['star_rating']}")
                    print(f"   Date: {review['review_date']}")
                    print(f"   Text: {review['review_text'][:100]}..." if len(review['review_text']) > 100 else f"   Text: {review['review_text']}")
                
                # Filter for 1-star reviews
                one_star = scraper.filter_one_star_reviews(all_reviews)
                print(f"\n" + "=" * 60)
                print(f"⭐ 1-Star Reviews: {len(one_star)}")
                print("=" * 60)
                
                if one_star:
                    print("\nFirst 1-star review:")
                    review = one_star[0]
                    print(f"  Reviewer: {review['reviewer_name']}")
                    print(f"  Date: {review['review_date']}")
                    print(f"  Text: {review['review_text'][:200]}...")
                
            else:
                print("\n⚠️  No reviews were extracted.")
                print("This could mean:")
                print("  - The selectors need adjustment")
                print("  - Google's layout has changed")
                print("  - The page didn't load properly")
            
            print("\n" + "=" * 60)
            print("✅ Test Completed!")
            print("=" * 60)
            
            return True
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_scraper()
    sys.exit(0 if success else 1)

