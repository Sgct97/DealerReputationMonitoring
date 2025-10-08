"""
Test script to run pipeline with multiple dealership URLs
"""

import os
from dotenv import load_dotenv
from src.scraper.scraper import GoogleReviewsScraper
from src.database.db_manager import DatabaseManager
from src.ai.analyzer import ReviewAnalyzer
from src.notifications.emailer import EmailNotifier

load_dotenv()

# Test with 2 URLs
TEST_URLS = [
    os.getenv('GOOGLE_BUSINESS_URL'),  # Lexus of Wesley Chapel
    "https://www.google.com/maps/place/Lexus+of+Tampa+Bay/@27.9458742,-82.5167946,17z/data=!3m1!4b1!4m6!3m5!1s0x88c2c35b87e0d971:0x7f5b5a3a4d3c3b0a!8m2!3d27.9458695!4d-82.5142197!16s%2Fg%2F1tg6h8g8?entry=ttu"  # Different Lexus dealership
]

print("=" * 80)
print("🧪 MULTI-URL PIPELINE TEST")
print("=" * 80)
print(f"\nTesting with {len(TEST_URLS)} dealership URLs:")
for i, url in enumerate(TEST_URLS, 1):
    print(f"  {i}. {url[:80]}...")

# Initialize components
db = DatabaseManager("./data/reviews.db")

# Setup proxy config
proxy_config = None
if os.getenv('PROXY_SERVER'):
    proxy_config = {
        'server': os.getenv('PROXY_SERVER'),
        'username': os.getenv('PROXY_USERNAME'),
        'password': os.getenv('PROXY_PASSWORD')
    }

scraper = GoogleReviewsScraper(proxy_config=proxy_config)
analyzer = ReviewAnalyzer(api_key=os.getenv('OPENAI_API_KEY'))
emailer = EmailNotifier(
    gmail_address=os.getenv('EMAIL_ADDRESS'),
    gmail_app_password=os.getenv('EMAIL_PASSWORD'),
    to_email=os.getenv('RECIPIENT_EMAIL')
)

total_new_reviews = 0
total_emails_sent = 0

# Process each URL
for idx, url in enumerate(TEST_URLS, 1):
    print(f"\n{'=' * 80}")
    print(f"🏢 Processing Dealership {idx}/{len(TEST_URLS)}")
    print(f"{'=' * 80}")
    print(f"URL: {url[:80]}...")
    
    try:
        # Get or create dealership record
        dealership = db.get_dealership_by_url(url)
        if dealership:
            dealership_id = dealership[0]
            print(f"✓ Found existing dealership (ID: {dealership_id})")
        else:
            dealership_id = db.add_dealership(url, f"Dealership {idx}")
            print(f"✓ Created new dealership (ID: {dealership_id})")
        
        # Scrape reviews
        print(f"\n🔍 Scraping reviews...")
        star_ratings = [int(x.strip()) for x in os.getenv('STAR_RATINGS_TO_TRACK', '1').split(',')]
        all_reviews = scraper.scrape_reviews(url, star_ratings_to_track=star_ratings)
        print(f"✓ Scraped {len(all_reviews)} total reviews")
        
        # Filter and process new reviews
        new_reviews = []
        for review in all_reviews:
            if not db.review_exists(review['reviewer_name'], review['review_text'], dealership_id):
                new_reviews.append(review)
        
        print(f"✓ Found {len(new_reviews)} new reviews for this dealership")
        
        # Process each new review
        dealership_new_count = 0
        for review in new_reviews:
            print(f"\n🆕 New review from: {review['reviewer_name']}")
            
            # AI Analysis
            print("   🤖 Analyzing with AI...")
            analysis = analyzer.analyze_review(review['review_text'], review['reviewer_name'])
            print(f"   ✓ Recommended category: {analysis['category']}")
            
            # Save to database
            db.add_review(
                dealership_id=dealership_id,
                reviewer_name=review['reviewer_name'],
                star_rating=review['star_rating'],
                review_text=review['review_text'],
                review_date=review['review_date'],
                review_url=review['review_url'],
                ai_analysis=analysis
            )
            
            # Send email
            print("   📧 Sending email notification...")
            emailer.send_new_review_alert(
                reviewer_name=review['reviewer_name'],
                review_text=review['review_text'],
                star_rating=review['star_rating'],
                review_date=review['review_date'],
                review_url=review['review_url'],
                ai_category=analysis['category'],
                ai_reasoning=analysis['reasoning']
            )
            print("   ✓ Email sent successfully")
            
            dealership_new_count += 1
            total_emails_sent += 1
        
        total_new_reviews += dealership_new_count
        
        # Update last scraped timestamp
        db.update_dealership_last_scraped(dealership_id)
        
        print(f"\n✓ Completed dealership {idx}: {dealership_new_count} new reviews processed")
        
    except Exception as e:
        print(f"\n❌ Error processing dealership {idx}: {e}")
        continue

# Final summary
print("\n" + "=" * 80)
print("📈 FINAL SUMMARY")
print("=" * 80)
print(f"✓ {total_new_reviews} total new review(s) detected across all dealerships")
print(f"📧 {total_emails_sent} total email notifications sent")

# Show database stats
cursor = db.conn.cursor()
cursor.execute("SELECT COUNT(*) FROM dealerships")
dealership_count = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM reviews")
review_count = cursor.fetchone()[0]

print(f"📊 Database: {dealership_count} dealerships, {review_count} total reviews")
print("\n✅ Multi-URL test completed")
print("=" * 80)

