"""
Test Optimization: Verify Report URLs Only Clicked for New Reviews
This test verifies that the deduplication optimization works correctly:
- First run: Should click report URLs for all reviews
- Second run: Should skip clicking for existing reviews, only click for new ones
"""

import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from database.db_manager import DatabaseManager
import os

def test_optimization():
    """Test that deduplication optimization reduces unnecessary clicks."""
    
    print("=" * 80)
    print("🧪 OPTIMIZATION TEST: Verify Report URLs Only Clicked for New Reviews")
    print("=" * 80)
    
    # Use a fresh test database
    test_db_path = "./data/test_optimization.db"
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
        print("✓ Cleaned up old test database\n")
    
    # Initialize database
    db = DatabaseManager(test_db_path)
    
    # Create a dealership
    print("SETUP: Creating dealership...")
    dealership_id = db.add_dealership(
        "Test Dealership", 
        "https://example.com/dealership"
    )
    print(f"✓ Created dealership with ID: {dealership_id}\n")
    
    # Simulate FIRST scrape run - all reviews are new
    print("=" * 80)
    print("SCENARIO 1: First Scrape Run (All Reviews Are New)")
    print("=" * 80)
    
    first_run_reviews = [
        {
            'reviewer_name': 'Alice Smith',
            'star_rating': 1,
            'review_text': 'Terrible customer service. Very disappointed.',
            'review_date': '3 days ago',
            'review_url': 'https://example.com/review/1'
        },
        {
            'reviewer_name': 'Bob Johnson',
            'star_rating': 1,
            'review_text': 'Worst experience ever. Do not recommend.',
            'review_date': '1 week ago',
            'review_url': 'https://example.com/review/2'
        },
        {
            'reviewer_name': 'Charlie Brown',
            'star_rating': 1,
            'review_text': 'Never going back. Rude staff.',
            'review_date': '2 weeks ago',
            'review_url': 'https://example.com/review/3'
        }
    ]
    
    print(f"Scraped {len(first_run_reviews)} reviews from page")
    print("\nChecking which reviews need report URLs...")
    
    # Simulate the deduplication check (Pass 1.5)
    existing_count = 0
    new_count = 0
    
    for review in first_run_reviews:
        if db.review_exists(
            review['reviewer_name'],
            review['review_text'],
            review['review_date'],
            dealership_id
        ):
            existing_count += 1
            print(f"  ⏭️  SKIP (exists): {review['reviewer_name']}")
        else:
            new_count += 1
            print(f"  🔗 CLICK (new): {review['reviewer_name']}")
    
    print(f"\n✅ First Run Summary:")
    print(f"   - Total reviews scraped: {len(first_run_reviews)}")
    print(f"   - Existing reviews (skip): {existing_count}")
    print(f"   - New reviews (click URL): {new_count}")
    print(f"   - Report URL clicks: {new_count}")
    
    expected_first_run_clicks = len(first_run_reviews)  # All are new
    if new_count == expected_first_run_clicks:
        print(f"   ✅ PASS: Clicked {new_count}/{expected_first_run_clicks} report URLs (as expected)")
    else:
        print(f"   ❌ FAIL: Expected {expected_first_run_clicks} clicks, got {new_count}")
        return False
    
    # Add these reviews to database (simulating they were saved)
    print("\nAdding reviews to database...")
    for review in first_run_reviews:
        db.add_review(review, dealership_id=dealership_id)
        print(f"  ✓ Saved: {review['reviewer_name']}")
    
    print(f"\nDatabase now has {db.get_stats()['total_reviews']} reviews")
    
    # Simulate SECOND scrape run - mix of existing and new reviews
    print("\n" + "=" * 80)
    print("SCENARIO 2: Second Scrape Run (Mix of Existing and New Reviews)")
    print("=" * 80)
    
    second_run_reviews = [
        # These 3 already exist
        {
            'reviewer_name': 'Alice Smith',
            'star_rating': 1,
            'review_text': 'Terrible customer service. Very disappointed.',
            'review_date': '3 days ago',
            'review_url': 'https://example.com/review/1'
        },
        {
            'reviewer_name': 'Bob Johnson',
            'star_rating': 1,
            'review_text': 'Worst experience ever. Do not recommend.',
            'review_date': '1 week ago',
            'review_url': 'https://example.com/review/2'
        },
        {
            'reviewer_name': 'Charlie Brown',
            'star_rating': 1,
            'review_text': 'Never going back. Rude staff.',
            'review_date': '2 weeks ago',
            'review_url': 'https://example.com/review/3'
        },
        # These 2 are NEW
        {
            'reviewer_name': 'David Lee',
            'star_rating': 1,
            'review_text': 'Horrible dealership. Avoid at all costs.',
            'review_date': '1 day ago',
            'review_url': 'https://example.com/review/4'
        },
        {
            'reviewer_name': 'Emma Wilson',
            'star_rating': 1,
            'review_text': 'Total waste of time. Unprofessional.',
            'review_date': '2 hours ago',
            'review_url': 'https://example.com/review/5'
        }
    ]
    
    print(f"Scraped {len(second_run_reviews)} reviews from page")
    print("\nChecking which reviews need report URLs...")
    
    # Simulate the deduplication check (Pass 1.5)
    existing_count = 0
    new_count = 0
    new_reviews = []
    
    for review in second_run_reviews:
        if db.review_exists(
            review['reviewer_name'],
            review['review_text'],
            review['review_date'],
            dealership_id
        ):
            existing_count += 1
            print(f"  ⏭️  SKIP (exists): {review['reviewer_name']}")
        else:
            new_count += 1
            new_reviews.append(review)
            print(f"  🔗 CLICK (new): {review['reviewer_name']}")
    
    print(f"\n✅ Second Run Summary:")
    print(f"   - Total reviews scraped: {len(second_run_reviews)}")
    print(f"   - Existing reviews (skip): {existing_count}")
    print(f"   - New reviews (click URL): {new_count}")
    print(f"   - Report URL clicks: {new_count}")
    print(f"   - Clicks saved: {existing_count} (would have clicked {len(second_run_reviews)} without optimization)")
    
    expected_existing = 3  # Alice, Bob, Charlie
    expected_new = 2  # David, Emma
    
    success = True
    
    if existing_count == expected_existing:
        print(f"   ✅ PASS: Correctly identified {existing_count} existing reviews")
    else:
        print(f"   ❌ FAIL: Expected {expected_existing} existing, got {existing_count}")
        success = False
    
    if new_count == expected_new:
        print(f"   ✅ PASS: Correctly identified {new_count} new reviews")
    else:
        print(f"   ❌ FAIL: Expected {expected_new} new, got {new_count}")
        success = False
    
    # Calculate optimization benefit
    print("\n" + "=" * 80)
    print("OPTIMIZATION ANALYSIS")
    print("=" * 80)
    
    without_optimization = len(second_run_reviews)  # Would click all 5
    with_optimization = new_count  # Only clicks 2
    clicks_saved = without_optimization - with_optimization
    savings_percent = (clicks_saved / without_optimization) * 100
    
    print(f"Without optimization: {without_optimization} report URL clicks")
    print(f"With optimization:    {with_optimization} report URL clicks")
    print(f"Clicks saved:         {clicks_saved} ({savings_percent:.0f}% reduction)")
    
    # Real-world example from handoff
    print(f"\nReal-world example from handoff document:")
    print(f"  - Total reviews scraped: 129")
    print(f"  - Already in database: 30")
    print(f"  - New reviews: 99")
    print(f"  - Without optimization: 129 clicks (what happened before)")
    print(f"  - With optimization: 99 clicks")
    print(f"  - Clicks saved: 30 (23% reduction)")
    
    # Clean up
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
        print("\n✓ Cleaned up test database")
    
    if success:
        print("\n" + "=" * 80)
        print("✅ OPTIMIZATION TEST PASSED!")
        print("=" * 80)
        print("The deduplication check correctly identifies existing reviews")
        print("and skips clicking report URLs for them, saving time and resources.")
        return True
    else:
        print("\n" + "=" * 80)
        print("❌ OPTIMIZATION TEST FAILED!")
        print("=" * 80)
        return False


if __name__ == "__main__":
    try:
        success = test_optimization()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

