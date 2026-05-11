# ─── Build Stage: React Dashboard ───
FROM node:20-slim AS frontend

WORKDIR /app/dashboard
COPY dashboard/package.json dashboard/package-lock.json* ./
RUN npm ci --production=false
COPY dashboard/ ./
RUN npm run build


# ─── Production Stage: Flask API + Built Dashboard ───
FROM python:3.12-slim

WORKDIR /app

# Install system deps for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY api/ ./api/
COPY scraper/ ./scraper/
COPY sql/ ./sql/
COPY .env.example ./.env.example

# Copy built React dashboard from frontend stage
COPY --from=frontend /app/dashboard/dist ./dashboard/dist

# Expose port
EXPOSE ${PORT:-5000}

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:${PORT:-5000}/api/health', timeout=3)" || exit 1

# Start with gunicorn
CMD ["sh", "-c", "python -c 'from scraper.db import init_db; init_db()' && gunicorn api.app:app --bind 0.0.0.0:${PORT:-5000} --workers 2 --timeout 120 --access-logfile -"]
