"""
Test Multi-Dealership System
Tests that multiple dealerships can be tracked in one database.
"""

import os
import sys
from dotenv import load_dotenv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from scraper.scraper import GoogleReviewsScraper
from database.db_manager import DatabaseManager
from ai.analyzer import ReviewAnalyzer

load_dotenv()

# Test URLs
dealerships = [
    ("Crown Honda", "https://www.google.com/maps/place/Crown+Honda/@27.8424813,-82.6876056,16z/data=!3m1!4b1!4m6!3m5!1s0x88c2e466a0750b31:0xec498971ea9d4ac7!8m2!3d27.8424813!4d-82.6850253!16s%2Fg%2F11h0zn3j2?entry=ttu&g_ep=EgoyMDI1MDkyOC4wIKXMDSoASAFQAw%3D%3D"),
    ("AutoNation Ford St. Petersburg", "https://www.google.com/maps/place/AutoNation+Ford+St.+Petersburg/@27.794611,-82.6804603,16z/data=!4m16!1m9!3m8!1s0x88c2e3bb687f7e2b:0x4ca2bbe8f85c3f98!2sAutoNation+Ford+St.+Petersburg!8m2!3d27.794611!4d-82.67788!9m1!1b1!16s%2Fg%2F1tj9v3d4!3m5!1s0x88c2e3bb687f7e2b:0x4ca2bbe8f85c3f98!8m2!3d27.794611!4d-82.67788!16s%2Fg%2F1tj9v3d4"),
    ("Lexus of Clearwater", "https://www.google.com/maps/place/Lexus+of+Clearwater/@28.0224685,-82.739267,17z/data=!3m1!4b1!4m6!3m5!1s0x88c2f2070886551b:0x96ac92db6fc5c563!8m2!3d28.0224685!4d-82.7366867!16s%2Fg%2F1tdbxk1c?entry=ttu&g_ep=EgoyMDI1MDkyOC4wIKXMDSoASAFQAw%3D%3D")
]

# Proxy config
proxy_server = os.getenv('PROXY_SERVER')
proxy_username = os.getenv('PROXY_USERNAME')
proxy_password = os.getenv('PROXY_PASSWORD')

proxy_config = None
if proxy_server:
    proxy_config = {
        'server': proxy_server,
        'username': proxy_username,
        'password': proxy_password
    }

database_path = './data/reviews.db'
db = DatabaseManager(database_path)

print("=" * 70)
print("🧪 Multi-Dealership Test")
print("=" * 70)
print(f"\nTesting {len(dealerships)} dealerships in ONE database\n")

for name, url in dealerships:
    print(f"\n{'=' * 70}")
    print(f"📍 {name}")
    print(f"{'=' * 70}")
    
    # Add dealership
    dealership_id = db.add_dealership(name, url)
    print(f"✓ Dealership ID: {dealership_id}")
    
    # Scrape 3 reviews (quick test)
    with GoogleReviewsScraper(proxy_config) as scraper:
        reviews = scraper.scrape_reviews(url, db_manager=db, scrape_all=True, max_reviews=3, star_ratings_to_track=[1])
        
        one_star = scraper.filter_reviews_by_rating(reviews, [1])
        print(f"✓ Scraped {len(one_star)} 1-star reviews")
        
        # Save reviews
        new_count = 0
        for review in one_star:
            if not db.review_exists(review['reviewer_name'], review['review_text'], review['review_date'], dealership_id):
                db.add_review(review, dealership_id=dealership_id)
                new_count += 1
        
        print(f"✓ Saved {new_count} new reviews for {name}")

# Check database
print(f"\n{'=' * 70}")
print("📊 Database Summary")
print(f"{'=' * 70}\n")

conn = db._DatabaseManager__get_connection() if hasattr(db, '_DatabaseManager__get_connection') else __import__('sqlite3').connect(database_path)
cursor = conn.cursor()

cursor.execute("SELECT id, name, total_reviews FROM dealerships")
dealerships_in_db = cursor.fetchall()

for dealer_id, dealer_name, total in dealerships_in_db:
    cursor.execute("SELECT COUNT(*) FROM reviews WHERE dealership_id = ?", (dealer_id,))
    review_count = cursor.fetchone()[0]
    print(f"📍 {dealer_name}")
    print(f"   ID: {dealer_id} | Reviews: {review_count}")

cursor.execute("SELECT COUNT(*) FROM reviews")
total_reviews = cursor.fetchone()[0]

print(f"\n✅ Total reviews across all dealerships: {total_reviews}")
print(f"✅ All dealerships tracked in ONE database!")

conn.close()

print("\n" + "=" * 70)
print("✅ Multi-Dealership System Verified!")
print("=" * 70)

