# Dealer Reputation Keeper


## What It Does

Monitors your Google Business Profile for low-star reviews 24/7 and emails you immediately when one appears. Built specifically for auto dealerships.

This system checks every 4 hours, so you're never more than 4 hours behind.

---

## How It Works

### 1. Automated Monitoring
- Scrapes your Google Business Profile every 4 hours
- Tracks 1, 2, and 3-star reviews (configurable)
- Runs on cloud servers - no software to install

### 2. AI Analysis
- Each review gets analyzed by GPT-4
- Categorizes into one of the 7 Google Report review’ types 
- Explains why it flagged the review

### 3. Instant Alerts
- Email sent within minutes of detection
- Includes direct link to report the review to Google
- Shows full review text and AI recommendation
---

## Technical Details

- **Infrastructure**: Hosted on Render (cloud platform)
- **Database**: Stores review history to prevent duplicates - **Browser Automation**: Playwright - mimics real browser behavior
- **Proxy Network**: Uses residential proxies to avoid Google blocking
- **AI**: OpenAI GPT-4 for review analysis
- **Monitoring Frequency**: Every 4 hours (customizable)
- **Email**: Sends via Gmail SMTP 

---

## Future Enhancement: Automatic Reporting

### What's Possible

The system can be upgraded to automatically submit reports to Google on your behalf. Instead of just sending you an email with a link, it would:

1. Detect the inappropriate review
2. Run AI analysis to determine report reason
3. Log into your Google account
4. Click the "Report review" button automatically
5. Select the appropriate violation category
6. Submit the report
7. Send you a confirmation email

