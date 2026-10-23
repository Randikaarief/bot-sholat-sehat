FROM python:3.11-slim

# Set timezone & environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Jakarta

WORKDIR /app

# Install dependencies sistem jika diperlukan
RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Salin dan install requirements Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Salin seluruh kode aplikasi
COPY . .

# Expose port FastAPI / Healthcheck
EXPOSE 8000

# Jalankan aplikasi FastAPI + Telegram Bot Polling/Webhook
CMD ["python", "-m", "app.main"]
