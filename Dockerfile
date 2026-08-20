FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src /app

# Set environment variables
ENV DATABASE_URL=postgresql+asyncpg://postgres:myactivities@db:5432/myactivities-test

EXPOSE 8000

# Run migrations and start app
CMD ["sh", "-c", "python -m app.db.manage && uvicorn app.main:app --host 0.0.0.0 --port 8000"]