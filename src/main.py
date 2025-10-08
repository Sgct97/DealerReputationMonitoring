"""
Main Orchestration Script
Coordinates scraping, analysis, and notification for new 1-star reviews.
"""

import os
import sys
from dotenv import load_dotenv
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from scraper.scraper import GoogleReviewsScraper
from database.db_manager import DatabaseManager
from ai.analyzer import ReviewAnalyzer
from notifications.emailer import EmailNotifier


def main():
    """Main execution function."""
    
    # Load environment variables
    load_dotenv()
    
    # Get configuration from environment
    business_url = os.getenv('GOOGLE_BUSINESS_URL')
    openai_api_key = os.getenv('OPENAI_API_KEY')
    gmail_address = os.getenv('GMAIL_ADDRESS')
    gmail_app_password = os.getenv('GMAIL_APP_PASSWORD')
    to_email = os.getenv('TO_EMAIL')
    database_path = os.getenv('DATABASE_PATH', './data/reviews.db')
    initial_scrape_limit = int(os.getenv('INITIAL_SCRAPE_LIMIT', '75'))  # 0 = unlimited
    
    # Parse star ratings to track (comma-separated)
    star_ratings_str = os.getenv('STAR_RATINGS_TO_TRACK', '1')
    star_ratings_to_track = [int(x.strip()) for x in star_ratings_str.split(',')]
    
    # Proxy configuration (optional)
    proxy_server = os.getenv('PROXY_SERVER')
    proxy_username = os.getenv('PROXY_USERNAME')
    proxy_password = os.getenv('PROXY_PASSWORD')
    
    # Validate required configuration
    required_vars = {
        'GOOGLE_BUSINESS_URL': business_url,
        'OPENAI_API_KEY': openai_api_key,
        'GMAIL_ADDRESS': gmail_address,
        'GMAIL_APP_PASSWORD': gmail_app_password,
        'TO_EMAIL': to_email
    }
    
    missing_vars = [var for var, value in required_vars.items() if not value]
    
    if missing_vars:
        print(f"❌ Error: Missing required environment variables: {', '.join(missing_vars)}")
        print("Please check your .env file.")
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
    print("🚀 Starting Dealer Reputation Keeper")
    print("=" * 60)
    
    # Initialize components
    print("\n📊 Initializing database...")
    db = DatabaseManager(database_path)
    
    # Extract dealership name from URL or use default
    dealership_name = "Dealership"  # Default
    try:
        # Try to extract name from URL (e.g., "Crown+Honda" → "Crown Honda")
        url_parts = business_url.split('/place/')[1].split('/')[0] if '/place/' in business_url else None
        if url_parts:
            dealership_name = url_parts.split('@')[0].replace('+', ' ')
    except:
        pass
    
    # Add or get dealership
    dealership_id = db.add_dealership(dealership_name, business_url)
    print(f"📍 Monitoring: {dealership_name} (ID: {dealership_id})")
    
    print("🤖 Initializing AI analyzer...")
    analyzer = ReviewAnalyzer(openai_api_key)
    
    print("📧 Initializing email notifier...")
    notifier = EmailNotifier(gmail_address, gmail_app_password, to_email)
    
    # Start scraping
    print(f"\n🔍 Scraping reviews from: {business_url}")
    
    try:
        with GoogleReviewsScraper(proxy_config) as scraper:
            # Auto-detect if this is the initial run (empty database)
            stats = db.get_stats()
            is_initial_run = stats['total_reviews'] == 0
            
            ratings_str = ','.join(map(str, star_ratings_to_track))
            
            if is_initial_run:
                limit_text = "UNLIMITED" if initial_scrape_limit == 0 else f"up to {initial_scrape_limit}"
                print(f"📊 Initial run detected - will scrape {limit_text} reviews with {ratings_str}-star rating(s)")
                all_reviews = scraper.scrape_reviews(business_url, db_manager=db, dealership_id=dealership_id, scrape_all=True, max_reviews=initial_scrape_limit, star_ratings_to_track=star_ratings_to_track)
            else:
                print(f"📊 Incremental run - will stop at known {ratings_str}-star reviews")
                all_reviews = scraper.scrape_reviews(business_url, db_manager=db, dealership_id=dealership_id, stop_at_seen=3, star_ratings_to_track=star_ratings_to_track)
            
            if not all_reviews:
                print("⚠️  No reviews found. This could mean:")
                print("   - The page structure has changed (selectors need updating)")
                print("   - The business has no reviews yet")
                print("   - Access was blocked")
                return
            
            print(f"✓ Found {len(all_reviews)} total reviews")
            
            # Filter for tracked star ratings
            tracked_reviews = scraper.filter_reviews_by_rating(all_reviews, star_ratings_to_track)
            print(f"✓ Found {len(tracked_reviews)} review(s) with {ratings_str}-star rating(s)")
            
            # Process each tracked review
            new_reviews_count = 0
            
            for review in tracked_reviews:
                # Check if this is a new review for this dealership
                if not db.review_exists(
                    review['reviewer_name'],
                    review['review_text'],
                    review['review_date'],
                    dealership_id
                ):
                    print(f"\n🆕 New {review['star_rating']}-star review detected from: {review['reviewer_name']}")
                    
                    # Analyze with AI first
                    print("   🤖 Analyzing with AI...")
                    ai_analysis = analyzer.analyze_review(
                        review['review_text'],
                        review['reviewer_name']
                    )
                    
                    print(f"   ✓ Recommended category: {ai_analysis['category']}")
                    
                    # Add to database with AI analysis
                    db.add_review(review, dealership_id=dealership_id, ai_analysis=ai_analysis)
                    
                    # Send notification
                    print("   📧 Sending email notification...")
                    success = notifier.send_review_alert(review, ai_analysis)
                    
                    if success:
                        print("   ✓ Email sent successfully")
                        db.mark_as_notified(
                            review['reviewer_name'],
                            review['review_text'],
                            review['review_date']
                        )
                        new_reviews_count += 1
                    else:
                        print("   ❌ Failed to send email")
            
            # Update dealership last scraped time
            db.update_dealership_last_scraped(dealership_id)
            
            # Print summary
            print("\n" + "=" * 60)
            print("📈 Summary")
            print("=" * 60)
            
            if new_reviews_count > 0:
                print(f"✓ {new_reviews_count} new {ratings_str}-star review(s) detected and reported")
            else:
                print(f"✓ No new {ratings_str}-star reviews detected")
            
            stats = db.get_stats()
            print(f"📊 Total reviews tracked: {stats['total_reviews']}")
            print(f"⭐ Reviews with tracked ratings ({ratings_str}-star): {stats['one_star_reviews']}")
            print(f"📧 Total notifications sent: {stats['notified_count']}")
            
    except Exception as e:
        print(f"\n❌ Error during execution: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Send failure alert email
        try:
            print("\n📧 Sending failure alert email...")
            failure_subject = f"🚨 Dealer Reputation Keeper - Scraping Failed"
            failure_body = f"""
            <h2 style="color: #dc3545;">Scraping Failed</h2>
            <p><strong>Error:</strong> {str(e)}</p>
            <p><strong>Business URL:</strong> {business_url}</p>
            <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <h3>Possible Causes:</h3>
            <ul>
                <li>Google changed their UI - selectors need updating</li>
                <li>Proxy was blocked</li>
                <li>Network connectivity issue</li>
                <li>Website timeout</li>
            </ul>
            
            <p><strong>Action Required:</strong> Check the error message and update selectors if needed.</p>
            <p>See FINDING_SELECTORS.md for instructions.</p>
            
            <hr>
            <pre style="background: #f5f5f5; padding: 10px; overflow-x: auto;">
{traceback.format_exc()}
            </pre>
            """
            
            from datetime import datetime
            notifier.send_failure_alert(failure_subject, failure_body)
            print("✓ Failure alert sent")
        except Exception as email_error:
            print(f"⚠️ Could not send failure alert: {email_error}")
        
        sys.exit(1)
    
    print("\n✅ Execution completed successfully")
    print("=" * 60)


if __name__ == "__main__":
    main()
