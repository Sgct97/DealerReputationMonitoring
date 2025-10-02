"""
Test Script for Database Module
Tests that the database can store and retrieve reviews correctly.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from database.db_manager import DatabaseManager
import os

def test_database():
    """Test the database functionality."""
    
    print("=" * 60)
    print("🧪 Testing Database Module")
    print("=" * 60)
    
    # Use a test database
    test_db_path = "./data/test_reviews.db"
    
    # Remove existing test database
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
        print("✓ Cleaned up old test database")
    
    # Initialize database
    print("\n1️⃣  Initializing database...")
    db = DatabaseManager(test_db_path)
    print("✓ Database initialized successfully")
    
    # Create a sample review
    sample_review = {
        'reviewer_name': 'John Doe',
        'star_rating': 1,
        'review_text': 'Terrible service! Never going back.',
        'review_date': '2 days ago',
        'review_url': 'https://example.com/review/123'
    }
    
    # Test adding a review
    print("\n2️⃣  Adding a sample review...")
    result = db.add_review(sample_review)
    
    if result:
        print("✓ Review added successfully")
    else:
        print("❌ Failed to add review")
        return False
    
    # Test checking if review exists
    print("\n3️⃣  Checking if review exists...")
    exists = db.review_exists(
        sample_review['reviewer_name'],
        sample_review['review_text'],
        sample_review['review_date']
    )
    
    if exists:
        print("✓ Review found in database")
    else:
        print("❌ Review not found in database")
        return False
    
    # Test duplicate prevention
    print("\n4️⃣  Testing duplicate prevention...")
    duplicate_result = db.add_review(sample_review)
    
    if not duplicate_result:
        print("✓ Duplicate prevention working correctly")
    else:
        print("❌ Duplicate was added (should not happen)")
        return False
    
    # Test marking as notified
    print("\n5️⃣  Marking review as notified...")
    db.mark_as_notified(
        sample_review['reviewer_name'],
        sample_review['review_text'],
        sample_review['review_date']
    )
    print("✓ Review marked as notified")
    
    # Test getting all reviews
    print("\n6️⃣  Retrieving all reviews...")
    all_reviews = db.get_all_reviews()
    print(f"✓ Found {len(all_reviews)} review(s)")
    
    # Test getting stats
    print("\n7️⃣  Getting database statistics...")
    stats = db.get_stats()
    print(f"✓ Total reviews: {stats['total_reviews']}")
    print(f"✓ One-star reviews: {stats['one_star_reviews']}")
    print(f"✓ Notified: {stats['notified_count']}")
    
    # Display the review data
    print("\n8️⃣  Sample review data:")
    for review in all_reviews:
        print(f"   • Reviewer: {review['reviewer_name']}")
        print(f"   • Rating: {review['star_rating']} ⭐")
        print(f"   • Text: {review['review_text']}")
        print(f"   • Notified: {'Yes' if review['notified'] else 'No'}")
    
    print("\n" + "=" * 60)
    print("✅ All Database Tests Passed!")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    try:
        success = test_database()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
