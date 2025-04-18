# Use official Python 3.12 slim image as base
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies for psycopg2 and curl (for healthcheck)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download any large dependencies (e.g., model weights) if applicable
# Adjust this based on quiz_generation requirements
RUN python -c "from quiz_generation import generate_quiz; generate_quiz({'user_id': 0, 'topic': 'test', 'num_questions': 5, 'difficulty': 'easy'})" || true

# Copy project code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PORT=8000 \
    UVICORN_WORKERS=1  
    #Reduce to 1 to minimize memory usage

# Expose port
EXPOSE 8000

# Healthcheck to verify FastAPI is running
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run FastAPI with uvicorn, including timeout settings
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT --workers $UVICORN_WORKERS --timeout-keep-alive 65 --timeout 600"]