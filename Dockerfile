# Use official Python 3.12 slim image as base for smaller size
FROM python:3.12-slim

# Set working directory inside the container
WORKDIR /app

# Install system dependencies required for psycopg2 and other packages
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt to install dependencies
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project code
COPY . .

# Set environment variables
# - PYTHONUNBUFFERED ensures logs are output in real-time
# - PORT is set for the FastAPI app (can be overridden)
ENV PYTHONUNBUFFERED=1 \
    PORT=8000

# Expose the port FastAPI will run on
EXPOSE 8000

# Command to run the FastAPI app with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]