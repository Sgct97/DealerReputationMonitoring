# Gmail SMTP Setup Guide

This project uses Gmail's SMTP server to send email notifications. It's **free, simple, and secure**.

## What You Need

1. A Gmail account (any Gmail address)
2. A Gmail "App Password" (NOT your regular Gmail password)

## Step-by-Step Setup

### Step 1: Enable 2-Factor Authentication (if not already enabled)

Gmail App Passwords require 2-Factor Authentication to be enabled on your Google account.

1. Go to: https://myaccount.google.com/security
2. Under "How you sign in to Google", click **"2-Step Verification"**
3. Follow the prompts to enable it (you'll need your phone)

### Step 2: Generate an App Password

1. Go to: https://myaccount.google.com/apppasswords
   
2. You may need to sign in again

3. In the "App name" field, type something like: **"Dealer Reputation Keeper"**

4. Click **"Create"**

5. Google will generate a 16-character password that looks like:
   ```
   abcd efgh ijkl mnop
   ```

6. **Copy this password** (you won't be able to see it again!)

### Step 3: Update Your `.env` File

Open your `.env` file and add your Gmail credentials:

```env
GMAIL_ADDRESS=youremail@gmail.com
GMAIL_APP_PASSWORD=abcdefghijklmnop
TO_EMAIL=where-to-send-alerts@example.com
```

**Important Notes:**
- `GMAIL_ADDRESS` = Your full Gmail address
- `GMAIL_APP_PASSWORD` = The 16-character password from Step 2 (remove spaces)
- `TO_EMAIL` = Where you want to receive the alerts (can be the same Gmail or a different email)

### Example `.env` Configuration

```env
# OpenAI API Key
OPENAI_API_KEY=sk-abc123...

# Gmail Configuration
GMAIL_ADDRESS=mybusiness@gmail.com
GMAIL_APP_PASSWORD=abcdefghijklmnop
TO_EMAIL=mybusiness@gmail.com

# Other settings...
DATABASE_PATH=./data/reviews.db
```

## Testing Your Setup

Run the email test to verify everything works:

```bash
python tests/test_email.py
```

You should receive a test email within seconds!

## Troubleshooting

### "Invalid credentials" error
- Make sure you're using the **App Password**, not your regular Gmail password
- Remove any spaces from the App Password
- Verify the Gmail address is correct

### "Less secure apps" message
- You don't need to enable "less secure apps" when using App Passwords
- App Passwords are the secure, modern way to authenticate

### Email not arriving
- Check your spam folder
- Verify `TO_EMAIL` is correct in your `.env` file
- Make sure you have an internet connection

### Can't find App Passwords page
- Make sure 2-Factor Authentication is enabled first
- Try this direct link: https://myaccount.google.com/apppasswords

## Gmail SMTP Limits

- **Free Gmail accounts:** 500 emails per day
- **Google Workspace (paid):** 2,000 emails per day

For this project (checking reviews a few times per day), you'll use maybe 5-10 emails per day max, so the free limit is more than enough.

## Security Notes

✅ **App Passwords are secure**
- They only work for the specific app you created them for
- You can revoke them anytime from your Google account
- They don't give access to your full Google account

✅ **Your password is safe**
- Never share your App Password
- It's stored only in your `.env` file (which is in `.gitignore`)
- It won't be committed to GitHub

## Using This in Production (Render.com)

When you deploy to Render:

1. Go to your Render dashboard
2. Select your Cron Job
3. Go to "Environment" tab
4. Add the environment variables:
   - `GMAIL_ADDRESS`
   - `GMAIL_APP_PASSWORD`
   - `TO_EMAIL`

Render will use these values, and your emails will be sent from the cloud automatically!

---

**All set?** Run the test:

```bash
python tests/test_email.py
```
