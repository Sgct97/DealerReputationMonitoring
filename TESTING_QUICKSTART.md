# Quick Start: Testing Your Components

Follow these steps to test that everything works before completing the scraper.

## Step 1: Install Python Libraries

Open your terminal in this project folder and run:

```bash
pip install -r requirements.txt
```

This installs all the necessary Python libraries.

## Step 2: Configure Your API Keys

Edit the `.env` file in this folder. Replace the placeholder values with real ones:

### What you need:

1. **OpenAI API Key** (for AI testing)
   - Sign up/login: https://platform.openai.com/
   - Go to API keys: https://platform.openai.com/api-keys
   - Click "Create new secret key"
   - Copy the key (starts with `sk-`)
   - Paste it in `.env` as: `OPENAI_API_KEY=sk-your-key-here`

2. **SendGrid API Key** (for email testing)
   - Sign up/login: https://sendgrid.com/
   - Go to Settings → API Keys: https://app.sendgrid.com/settings/api_keys
   - Click "Create API Key"
   - Give it "Mail Send" permission
   - Copy the key (starts with `SG.`)
   - Paste it in `.env` as: `SENDGRID_API_KEY=SG.your-key-here`
   
3. **Verify Your Sender Email in SendGrid**
   - Go to: https://app.sendgrid.com/settings/sender_auth
   - Click "Verify a Single Sender"
   - Enter your email and verify it
   - Use this email as `FROM_EMAIL` in `.env`

4. **Set Your Recipient Email**
   - Set `TO_EMAIL` to where you want to receive test emails

### Example `.env` file:

```env
OPENAI_API_KEY=sk-abc123yourrealkeyhere
SENDGRID_API_KEY=SG.xyz789yourrealkeyhere
FROM_EMAIL=alerts@yourdomain.com
TO_EMAIL=youremail@gmail.com
DATABASE_PATH=./data/reviews.db
```

## Step 3: Run the Tests

From this project folder, run:

```bash
python tests/run_all_tests.py
```

### What will happen:

1. **Database Test** - Should pass immediately (no API needed)
2. **AI Test** - Will call OpenAI and analyze 3 fake reviews
3. **Email Test** - Will send you a test email

Between each test, you'll be prompted to press Enter.

## Step 4: Verify Results

### ✅ Check these things:

1. All three tests show "PASSED"
2. You received the test email in your inbox (check spam if not)
3. The email looks professional and contains all the info

### ❌ If something fails:

- Read the error message carefully
- Check the `tests/README.md` for troubleshooting
- Verify your API keys are correct (no extra spaces, complete key)
- For SendGrid: Make sure your FROM_EMAIL is verified

## Step 5: What's Next?

Once all tests pass:

✅ Your backend is 100% working!

The only remaining task is to complete the scraper:
- See `FINDING_SELECTORS.md` for instructions
- You'll inspect a Google Business Profile page
- Find the HTML selectors for reviews
- Give them to me, and I'll update the scraper code

---

## Cost Note

- **Database test:** Free
- **AI test:** ~$0.01 per run (uses OpenAI API)
- **Email test:** Free (SendGrid free tier: 100 emails/day)

Total cost to test everything: **Less than $0.05**
