# Deploying to Render.com

This guide will walk you through deploying the Dealer Reputation Keeper to Render.com as a scheduled Cron Job.

## Prerequisites

- A GitHub account
- A Render.com account (free tier is fine to start)
- All required API keys ready (OpenAI, SendGrid, Residential Proxy)

## Step 1: Push Code to GitHub

1. Initialize a Git repository in your project:
   ```bash
   git init
   git add .
   git commit -m "Initial commit - Dealer Reputation Keeper"
   ```

2. Create a new repository on GitHub (do NOT initialize with README)

3. Push your code:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
   git branch -M main
   git push -u origin main
   ```

## Step 2: Create a Cron Job on Render

1. Go to https://dashboard.render.com/
2. Click **"New +"** → **"Cron Job"**
3. Connect your GitHub repository
4. Configure the Cron Job:

   **Name:** `dealer-reputation-keeper`
   
   **Region:** Choose closest to your target location
   
   **Branch:** `main`
   
   **Runtime:** `Docker`
   
   **Schedule:** Choose your interval (examples below)
   
   **Docker Command:** (Leave blank - the Dockerfile already specifies the command)

### Schedule Examples

Render uses standard cron syntax:

- Every 4 hours: `0 */4 * * *`
- Every 6 hours: `0 */6 * * *`
- Twice a day (9 AM & 9 PM): `0 9,21 * * *`
- Every 3 hours: `0 */3 * * *`

## Step 3: Set Environment Variables

In the Render dashboard for your Cron Job, go to the **Environment** tab and add these variables:

```
GOOGLE_BUSINESS_URL=<your_google_business_profile_url>
OPENAI_API_KEY=<your_openai_api_key>
SENDGRID_API_KEY=<your_sendgrid_api_key>
FROM_EMAIL=<sender_email>
TO_EMAIL=<recipient_email>
PROXY_SERVER=<your_proxy_server_url>
PROXY_USERNAME=<your_proxy_username>
PROXY_PASSWORD=<your_proxy_password>
DATABASE_PATH=/app/data/reviews.db
```

**Important:** Make sure all values are filled in correctly. Do NOT include quotes around the values.

## Step 4: Deploy

1. Click **"Create Cron Job"**
2. Render will automatically:
   - Pull your code from GitHub
   - Build the Docker container
   - Schedule it to run at your specified intervals

## Step 5: Monitor & Test

### Manual Test Run
You can manually trigger a run from the Render dashboard to test immediately:
- Go to your Cron Job → Click **"Trigger Run"**

### Check Logs
View execution logs in the **Logs** tab to see:
- If the scraper ran successfully
- How many reviews were found
- If any emails were sent
- Any errors that occurred

### Database Persistence

**IMPORTANT:** By default, Render's Cron Jobs do NOT persist data between runs. This means our SQLite database would be reset each time.

**Solution:** Add a Render Disk for persistent storage:

1. In your Cron Job settings, go to **"Disks"**
2. Click **"Add Disk"**
3. Configure:
   - **Name:** `data-storage`
   - **Mount Path:** `/app/data`
   - **Size:** 1 GB (more than enough)
4. Save and redeploy

This ensures the database persists across runs, so we can properly track which reviews we've already seen.

## Step 6: Auto-Deploy on Git Push (Optional)

Enable auto-deploy so any code updates you push to GitHub automatically redeploy:

1. In Render dashboard → Your Cron Job → **Settings**
2. Under **"Build & Deploy"**, ensure **"Auto-Deploy"** is set to **"Yes"**

Now whenever you push to your `main` branch, Render will rebuild and redeploy.

## Troubleshooting

### "Browser not found" error
- Make sure you're using the Docker runtime (not Python or Native)
- Verify the Dockerfile is in your repo root

### No reviews being found
- Check the logs for specific errors
- The selectors in `scraper.py` may need updating (Google changes their HTML)
- Try a manual run and examine the screenshot in `/app/data/error_screenshot.png`

### Email not sending
- Verify your SendGrid API key is valid
- Check that `FROM_EMAIL` is verified in your SendGrid account
- Look for specific errors in the Render logs

### Proxy errors
- Verify your proxy credentials are correct
- Ensure your proxy service is active and has available bandwidth
- Some proxy services require whitelisting Render's IP ranges

## Costs

- **Render Cron Job:** Free tier includes 400 build minutes/month (usually plenty)
- **Render Disk:** $0.25/GB/month (1 GB = $0.25/month)
- **Total estimated cost:** ~$0.25 - $1/month on Render

(Plus the costs of your third-party services: OpenAI, SendGrid, Proxy)

## Next Steps

Once deployed, your system will:
1. Run automatically on your schedule
2. Detect new 1-star reviews
3. Analyze them with AI
4. Send you instant email alerts
5. Track everything in the database

You can adjust the schedule, update code, and monitor everything from the Render dashboard.
