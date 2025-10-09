# Use the official Playwright Python image with Chromium pre-installed
FROM mcr.microsoft.com/playwright/python:v1.55.0-jammy

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies (force reinstall openai to avoid conflicts)
RUN pip uninstall -y openai || true
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application
COPY . .

# Create data directory for SQLite database
RUN mkdir -p /app/data

# Set environment variable to ensure Python output is unbuffered
ENV PYTHONUNBUFFERED=1

# Run the main script
CMD ["python", "src/main.py"]
