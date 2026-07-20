FROM python:3.11-slim

# Install system dependencies, including Tesseract OCR and Poppler utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    poppler-utils \
    build-essential \
    libpq-dev \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements file first to leverage Docker build cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

EXPOSE 8000

# Fix line endings and set up startup script (runs migrations then starts server)
COPY start.sh .
RUN dos2unix start.sh && chmod +x start.sh
CMD ["./start.sh"]
