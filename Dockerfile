# Use official Python 3.12 slim image as base for smaller size
FROM python:3.12-slim

# Set working directory inside the container
WORKDIR /app

# Install system dependencies for psycopg2
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PORT=8000 \
    UVICORN_WORKERS=4

# Expose port
EXPOSE 8000

# Healthcheck to verify FastAPI is running
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run FastAPI with uvicorn
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT --workers $UVICORN_WORKERS"]