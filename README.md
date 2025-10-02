# Dealer Reputation Keeper

An automated system to monitor Google Business Profile reviews, detect new 1-star reviews, analyze them with AI, and send actionable email alerts.

## Features

- **Automated Review Monitoring**: Continuously scrapes a Google Business Profile for new reviews
- **Smart Detection**: Identifies only new 1-star reviews since the last check
- **AI-Powered Analysis**: Uses OpenAI to determine the best reporting category for each review
- **Instant Alerts**: Sends detailed email notifications with direct links to reviews
- **Cloud-Based**: Runs automatically on a schedule with zero manual intervention

## Setup

1. Copy `.env.example` to `.env` and fill in your configuration:
   ```bash
   cp .env.example .env
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

3. Run the scraper:
   ```bash
   python src/main.py
   ```

## Deployment

This application is designed to be deployed to Render.com as a Docker container running as a Cron Job.

See the `Dockerfile` for the container configuration.

## Project Structure

```
├── src/
│   ├── scraper/        # Web scraping logic
│   ├── database/       # SQLite database management
│   ├── ai/             # AI analysis integration
│   ├── notifications/  # Email notification system
│   └── main.py         # Main orchestration script
├── data/               # SQLite database storage
├── Dockerfile          # Container configuration
└── requirements.txt    # Python dependencies
```

## License

Proprietary - All rights reserved
