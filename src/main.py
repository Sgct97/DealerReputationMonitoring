"""
Main Orchestration Script
Coordinates scraping, analysis, and notification for new 1-star reviews.
"""

import os
import sys
import time
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
    business_urls_str = os.getenv('GOOGLE_BUSINESS_URL')
    openai_api_key = os.getenv('OPENAI_API_KEY')
    gmail_address = os.getenv('GMAIL_ADDRESS')
    gmail_app_password = os.getenv('GMAIL_APP_PASSWORD')
    to_email = os.getenv('TO_EMAIL')
    database_path = os.getenv('DATABASE_PATH', './data/reviews.db')
    initial_scrape_limit = int(os.getenv('INITIAL_SCRAPE_LIMIT', '75'))  # 0 = unlimited
    
    # Parse multiple URLs (pipe-separated: url1|url2|url3)
    # Use pipe (|) instead of comma since URLs contain commas in coordinates
    business_urls = [url.strip() for url in business_urls_str.split('|')] if business_urls_str else []
    
    # Parse star ratings to track (comma-separated)
    star_ratings_str = os.getenv('STAR_RATINGS_TO_TRACK', '1')
    star_ratings_to_track = [int(x.strip()) for x in star_ratings_str.split(',')]
    
    # Proxy configuration (optional)
    proxy_server = os.getenv('PROXY_SERVER')
    proxy_username = os.getenv('PROXY_USERNAME')
    proxy_password = os.getenv('PROXY_PASSWORD')
    
    # Validate required configuration
    required_vars = {
        'GOOGLE_BUSINESS_URL': business_urls_str,
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
    
    if not business_urls:
        print("❌ Error: No business URLs found in GOOGLE_BUSINESS_URL")
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
    print(f"📍 Monitoring {len(business_urls)} dealership(s)")
    
    # Initialize components
    print("\n📊 Initializing database...")
    db = DatabaseManager(database_path)
    
    print("🤖 Initializing AI analyzer...")
    analyzer = ReviewAnalyzer(openai_api_key)
    
    print("📧 Initializing email notifier...")
    notifier = EmailNotifier(gmail_address, gmail_app_password, to_email)
    
    # Track totals across all dealerships
    total_new_reviews = 0
    total_tracked_reviews = 0
    total_emails_sent = 0  # Track emails actually sent in this run
    
    try:
        import subprocess
        with GoogleReviewsScraper(proxy_config) as scraper:
            # Process each dealership
            for idx, business_url in enumerate(business_urls, 1):
                print(f"\n{'=' * 60}")
                print(f"🏢 Dealership {idx}/{len(business_urls)}")
                print(f"{'=' * 60}")
                
                # Extract dealership name from URL or use default
                dealership_name = f"Dealership {idx}"  # Default
                try:
                    # Try to extract name from URL (e.g., "Crown+Honda" → "Crown Honda")
                    url_parts = business_url.split('/place/')[1].split('/')[0] if '/place/' in business_url else None
                    if url_parts:
                        dealership_name = url_parts.split('@')[0].replace('+', ' ')
                except:
                    pass
                
                # Add or get dealership
                dealership_id = db.add_dealership(dealership_name, business_url)
                print(f"📍 {dealership_name} (ID: {dealership_id})")
                print(f"🔍 URL: {business_url}")
                
                # Auto-detect if this is the initial run for THIS dealership
                dealership_stats = db.get_stats(dealership_id)
                is_initial_run = dealership_stats['total_reviews'] == 0
                
                ratings_str = ','.join(map(str, star_ratings_to_track))
                
                if is_initial_run:
                    limit_text = "UNLIMITED" if initial_scrape_limit == 0 else f"up to {initial_scrape_limit}"
                    print(f"📊 Initial run detected - will scrape {limit_text} reviews with {ratings_str}-star rating(s)")
                    print(f"⏭️  Skipping report URL collection (will get them for NEW reviews on future runs)")
                    print(f"\n🌐 Starting scrape for: {dealership_name}...")
                    all_reviews = scraper.scrape_reviews(business_url, db_manager=db, dealership_id=dealership_id, scrape_all=True, max_reviews=initial_scrape_limit, star_ratings_to_track=star_ratings_to_track, skip_report_urls=True)
                    print(f"✓ Scrape completed for: {dealership_name}")
                else:
                    print(f"📊 Incremental run - will scrape all {ratings_str}-star reviews")
                    print(f"\n🌐 Starting scrape for: {dealership_name}...")
                    all_reviews = scraper.scrape_reviews(business_url, db_manager=db, dealership_id=dealership_id, stop_at_seen=3, star_ratings_to_track=star_ratings_to_track)
                    print(f"✓ Scrape completed for: {dealership_name}")
                
                if not all_reviews:
                    print(f"⚠️  No reviews found for {dealership_name}. This could mean:")
                    print("   - The page structure has changed (selectors need updating)")
                    print("   - The business has no reviews yet")
                    print("   - Access was blocked")
                    print(f"   → Skipping to next dealership...\n")
                    continue  # Skip to next dealership
                
                print(f"✓ Found {len(all_reviews)} total reviews")
                
                # Filter for tracked star ratings
                tracked_reviews = scraper.filter_reviews_by_rating(all_reviews, star_ratings_to_track)
                print(f"✓ Found {len(tracked_reviews)} review(s) with {ratings_str}-star rating(s)")
                
                # Identify which star ratings are NEW for this dealership (not in DB yet)
                # This prevents email spam when user adds new ratings to track
                new_star_ratings = []
                if not is_initial_run:  # Only check on incremental runs (initial run skips all emails anyway)
                    for rating in star_ratings_to_track:
                        if not db.has_reviews_with_rating(dealership_id, rating):
                            new_star_ratings.append(rating)
                    
                    if new_star_ratings:
                        # Only show message if we actually found reviews with these new ratings
                        found_new_ratings = [r['star_rating'] for r in tracked_reviews if r['star_rating'] in new_star_ratings]
                        if found_new_ratings:
                            unique_found = sorted(set(found_new_ratings))
                            new_ratings_str = ','.join(map(str, unique_found))
                            print(f"📌 First time tracking {new_ratings_str}-star reviews for this dealership")
                            print(f"   → All {new_ratings_str}-star reviews will be treated as baseline (no AI/emails)")
                
                # Process each tracked review
                new_reviews_count = 0
                
                for review in tracked_reviews:
                    try:
                        # Check if this is a new review for this dealership
                        if not db.review_exists(
                            review['reviewer_name'],
                            review['review_text'],
                            review['review_date'],
                            dealership_id
                        ):
                            print(f"\n🆕 New {review['star_rating']}-star review detected from: {review['reviewer_name']}")
                            
                            # Check if this review's star rating is new to this dealership
                            is_new_rating_for_dealership = review['star_rating'] in new_star_ratings
                            
                            # Only analyze with AI on incremental runs AND if not a new rating being tracked
                            ai_analysis = None
                            if not is_initial_run and not is_new_rating_for_dealership:
                                print("   🤖 Analyzing with AI...")
                                ai_analysis = analyzer.analyze_review(
                                    review['review_text'],
                                    review['reviewer_name']
                                )
                                print(f"   ✓ Recommended category: {ai_analysis['category']}")
                            else:
                                if is_initial_run:
                                    print("   🤖 AI analysis skipped (initial run - baseline data)")
                                elif is_new_rating_for_dealership:
                                    print(f"   🤖 AI analysis skipped (first time tracking {review['star_rating']}-star - baseline data)")
                            
                            # Add to database with AI analysis (if any)
                            db.add_review(review, dealership_id=dealership_id, ai_analysis=ai_analysis)
                            
                            # Send notification (skip on initial run OR if new rating being tracked)
                            if not is_initial_run and not is_new_rating_for_dealership:
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
                                    total_emails_sent += 1  # Track emails sent in this run
                                else:
                                    print("   ❌ Failed to send email")
                            else:
                                if is_initial_run:
                                    print("   📧 Email skipped (initial run - baseline data)")
                                elif is_new_rating_for_dealership:
                                    print(f"   📧 Email skipped (first time tracking {review['star_rating']}-star - baseline data)")
                                new_reviews_count += 1
                    except Exception as review_error:
                        print(f"   ❌ Error processing review from {review.get('reviewer_name', 'Unknown')}: {review_error}")
                        print(f"   → Skipping this review and continuing with next one...")
                        continue
                
                # Update dealership last scraped time (after processing all reviews)
                db.update_dealership_last_scraped(dealership_id)
                
                # Update totals
                total_new_reviews += new_reviews_count
                total_tracked_reviews += len(tracked_reviews)
                
                # Add delay between dealerships to prevent rate limiting
                if idx < len(business_urls):  # Not the last dealership
                    delay = 30  # 30 seconds between dealerships
                    print(f"\n{'='*60}")
                    print(f"✓ Finished dealership {idx}/{len(business_urls)}: {dealership_name if 'dealership_name' in locals() else 'Unknown'}")
                    print(f"⏳ Waiting {delay} seconds before next dealership...")
                    print(f"   (Prevents rate limiting/proxy blocks)")
                    print(f"{'='*60}\n")
                    time.sleep(delay)
        
        # Clean up any zombie Chromium processes after scraper closes
        try:
            subprocess.run(['killall', '-9', 'Chromium'], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
            print("\n✓ Cleaned up browser processes")
        except:
            pass
            
        # Print summary
        print("\n" + "=" * 60)
        print("📈 Summary")
        print("=" * 60)
        print(f"🏢 Dealerships processed: {len(business_urls)}")
        
        ratings_str = ','.join(map(str, star_ratings_to_track))
        if total_new_reviews > 0:
            print(f"✓ {total_new_reviews} new {ratings_str}-star review(s) detected and reported")
        else:
            print(f"✓ No new {ratings_str}-star reviews detected")
        
        stats = db.get_stats()  # Get global stats across all dealerships
        print(f"📊 Total reviews tracked: {stats['total_reviews']}")
        print(f"⭐ Reviews with tracked ratings ({ratings_str}-star): {total_tracked_reviews}")
        print(f"📧 Notifications sent (this run): {total_emails_sent}")
        print(f"📧 Total notifications sent (all time): {stats['notified_count']}")
    
    except Exception as e:
        print(f"\n❌ Error during execution: {str(e)}")
        import traceback
        from datetime import datetime as dt
        traceback.print_exc()
        
        # Send failure alert email
        try:
            print("\n📧 Sending failure alert email...")
            failure_subject = f"🚨 Dealer Reputation Keeper - Scraping Failed"
            failure_body = f"""
            <h2 style="color: #dc3545;">Scraping Failed</h2>
            <p><strong>Error:</strong> {str(e)}</p>
            <p><strong>Business URL:</strong> {business_url}</p>
            <p><strong>Time:</strong> {dt.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
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
