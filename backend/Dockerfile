FROM python:3.11-slim

# System dependencies:
# - tesseract-ocr + tesseract-ocr-eng: OCR engine for scanned PDFs
# - poppler-utils: provides pdftoppm, required by pdf2image
# - libpq-dev + gcc: needed to compile the psycopg2 PostgreSQL driver
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (cached layer — only re-runs if
# requirements.txt changes, not on every code change)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create the uploads directory inside the container
RUN mkdir -p /app/media/uploads

EXPOSE 8000

# Default command runs the production WSGI server
# The docker-compose api service overrides this with runserver for hot-reload
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "120"]
