"""
Diagnostic Test to Reproduce Deduplication Bug
This test simulates the exact scenario where review_exists() failed during scraping.
"""

import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from database.db_manager import DatabaseManager
import os

def test_deduplication_bug():
    """Reproduce the exact bug scenario from the handoff."""
    
    print("=" * 80)
    print("🔍 DIAGNOSTIC TEST: Reproduce Deduplication Bug")
    print("=" * 80)
    
    # Use a fresh test database
    test_db_path = "./data/test_dedup_bug.db"
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
        print("✓ Cleaned up old test database\n")
    
    # Initialize database
    db = DatabaseManager(test_db_path)
    
    # Create a dealership
    print("STEP 1: Creating dealership...")
    dealership_id = db.add_dealership(
        "Test Dealership", 
        "https://example.com/dealership"
    )
    print(f"✓ Created dealership with ID: {dealership_id}\n")
    
    # Add some sample reviews (simulating first run)
    sample_reviews = [
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
    
    print("STEP 2: Adding 3 reviews to database (simulating first scrape run)...")
    for review in sample_reviews:
        result = db.add_review(review, dealership_id=dealership_id)
        if result:
            print(f"  ✓ Added review from {review['reviewer_name']}")
        else:
            print(f"  ❌ Failed to add review from {review['reviewer_name']}")
    
    print(f"\nDatabase now has {db.get_stats()['total_reviews']} reviews\n")
    
    # Now simulate the scraper re-scraping the same reviews
    print("STEP 3: Simulating second scrape run (re-scraping same reviews)...")
    print("This simulates what happens in _extract_reviews() during Pass 1\n")
    
    # Test review_exists() WITHOUT dealership_id (what might have happened)
    print("TEST A: Calling review_exists() WITHOUT dealership_id")
    print("-" * 80)
    for review in sample_reviews:
        exists = db.review_exists(
            review['reviewer_name'],
            review['review_text'],
            review['review_date']
            # NOTE: No dealership_id parameter!
        )
        status = "✓ FOUND" if exists else "❌ NOT FOUND"
        print(f"  {status}: {review['reviewer_name']}")
    
    print("\n")
    
    # Test review_exists() WITH dealership_id (what should happen)
    print("TEST B: Calling review_exists() WITH dealership_id")
    print("-" * 80)
    for review in sample_reviews:
        exists = db.review_exists(
            review['reviewer_name'],
            review['review_text'],
            review['review_date'],
            dealership_id=dealership_id  # WITH dealership_id
        )
        status = "✓ FOUND" if exists else "❌ NOT FOUND"
        print(f"  {status}: {review['reviewer_name']}")
    
    print("\n")
    
    # Test with WRONG dealership_id (edge case)
    print("TEST C: Calling review_exists() WITH WRONG dealership_id")
    print("-" * 80)
    wrong_dealership_id = 9999
    for review in sample_reviews:
        exists = db.review_exists(
            review['reviewer_name'],
            review['review_text'],
            review['review_date'],
            dealership_id=wrong_dealership_id  # Wrong ID
        )
        status = "✓ FOUND" if exists else "❌ NOT FOUND"
        print(f"  {status}: {review['reviewer_name']}")
    
    print("\n" + "=" * 80)
    print("DIAGNOSIS:")
    print("=" * 80)
    print("""
Expected Behavior:
  - TEST A (no dealership_id): Should find reviews ✓
  - TEST B (correct dealership_id): Should find reviews ✓
  - TEST C (wrong dealership_id): Should NOT find reviews ✓

If TEST B shows "NOT FOUND", that would explain why the optimization failed!
The scraper needs to pass dealership_id to review_exists() for proper deduplication.
    """)
    
    # Clean up
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
        print("✓ Cleaned up test database")
    
    return True


if __name__ == "__main__":
    try:
        test_deduplication_bug()
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

