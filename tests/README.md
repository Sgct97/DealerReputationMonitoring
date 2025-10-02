# Testing Guide

This directory contains test scripts to verify each component of the Dealer Reputation Keeper works correctly.

## Before You Test

### 1. Install Python Dependencies

Make sure you're in the project root directory and run:

```bash
pip install -r requirements.txt
```

### 2. Set Up Your `.env` File

You need to configure your API keys and settings. The `.env` file is in the project root.

**Minimum configuration for testing:**

```env
# For Database Test (no API keys needed)
DATABASE_PATH=./data/reviews.db

# For AI Test (you need this)
OPENAI_API_KEY=sk-your-actual-openai-api-key

# For Email Test (you need these)
GMAIL_ADDRESS=youremail@gmail.com
GMAIL_APP_PASSWORD=your_16_char_app_password
TO_EMAIL=your-email@domain.com
```

### 3. Get Your API Keys

**OpenAI API Key:**
1. Go to https://platform.openai.com/api-keys
2. Create a new key
3. Copy it to your `.env` file

**Gmail App Password:**
1. Enable 2-Factor Authentication on your Google account
2. Go to https://myaccount.google.com/apppasswords
3. Create a new app password for "Mail"
4. Copy the 16-character password to your `.env` file
5. See `GMAIL_SETUP_GUIDE.md` for detailed instructions

## Running the Tests

### Option 1: Run All Tests (Recommended)

From the project root directory:

```bash
python tests/run_all_tests.py
```

This will run all three tests in sequence with pauses between each.

### Option 2: Run Individual Tests

**Test Database Only** (no API keys needed):
```bash
python tests/test_database.py
```

**Test AI Analysis** (needs OpenAI API key):
```bash
python tests/test_ai.py
```

**Test Email Notifications** (needs Gmail credentials):
```bash
python tests/test_email.py
```

## What Each Test Does

### 1. Database Test (`test_database.py`)
- Creates a test SQLite database
- Adds a sample review
- Tests duplicate prevention
- Tests retrieval and stats
- **No API keys required**

### 2. AI Analysis Test (`test_ai.py`)
- Connects to OpenAI
- Analyzes 3 sample fake reviews
- Returns reporting categories and reasoning
- **Requires:** Valid `OPENAI_API_KEY`
- **Cost:** ~$0.01 per test run

### 3. Email Test (`test_email.py`)
- Sends a test email via Gmail SMTP
- Uses sample review data
- **Requires:** Valid `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD`, `TO_EMAIL`
- **Important:** Check your inbox to verify the email looks good!
- **Free!** Gmail allows 500 emails/day

## Troubleshooting

### "No module named 'playwright'"
```bash
pip install -r requirements.txt
```

### "Missing required environment variables"
- Check that your `.env` file exists in the project root
- Verify all required keys are filled in (not the placeholder values)

### "OpenAI API error"
- Verify your API key is correct
- Check you have credits available: https://platform.openai.com/usage
- Make sure your key has permissions to use the API

### "Gmail email failed"
- Verify you're using an **App Password**, not your regular Gmail password
- Remove spaces from the App Password
- Verify `GMAIL_ADDRESS` is correct
- Make sure 2-Factor Authentication is enabled on your Google account
- See `GMAIL_SETUP_GUIDE.md` for detailed troubleshooting

### Email doesn't arrive
- Check your spam folder
- Verify the `TO_EMAIL` is correct
- Check your Gmail "Sent" folder to confirm it was sent

## Expected Output

### ✅ Successful Test Run

```
🔹 TEST 1/3: Database Module
✓ Database initialized successfully
✓ Review added successfully
✓ Review found in database
✓ Duplicate prevention working correctly
...
✅ All Database Tests Passed!

🔹 TEST 2/3: AI Analysis Module
✓ OpenAI API key loaded
✓ AI analyzer initialized
✓ Category: Spam
✓ Reasoning: ...
✅ All AI Analysis Tests Passed!

🔹 TEST 3/3: Email Notification Module
✓ Email configuration loaded
✓ Email sent successfully!
✅ Email Test Completed!

🎉 All tests passed! Your system is ready.
```

## Next Steps After Testing

Once all tests pass:
1. ✅ Your database is working
2. ✅ Your AI analysis is working
3. ✅ Your email notifications are working

The only remaining step is to complete the scraper by finding the Google review selectors (see `FINDING_SELECTORS.md` in the project root).
