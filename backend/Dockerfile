FROM python:3.11-slim

# Install system dependencies, including Tesseract OCR and Poppler utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    poppler-utils \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements file first to leverage Docker build cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

EXPOSE 8000

# Default command is to start the FastAPI application
# Use shell form so Render's dynamic $PORT env var is expanded at runtime.
# Falls back to 8000 for local Docker usage.
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
