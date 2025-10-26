FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (Cloud Run uses 8080 by default, but we can use any port)
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=run.py
ENV FLASK_ENV=production
ENV FLASK_PORT=5000
ENV PORT=5000

# Create data directory and instance directory for SQLite
RUN mkdir -p /app/data /app/instance

# Run Flask with gunicorn for production
RUN pip install --no-cache-dir gunicorn

# Create entrypoint script that initializes DB and runs the app
RUN echo '#!/bin/bash' > /app/entrypoint.sh && \
    echo 'set -e' >> /app/entrypoint.sh && \
    echo '' >> /app/entrypoint.sh && \
    echo 'echo "Initializing database..."' >> /app/entrypoint.sh && \
    echo 'python init_db.py || echo "DB init script not found, skipping"' >> /app/entrypoint.sh && \
    echo '' >> /app/entrypoint.sh && \
    echo 'echo "Starting Flask app with gunicorn..."' >> /app/entrypoint.sh && \
    echo 'exec gunicorn --bind :${PORT:-5000} --workers 4 --timeout 120 --access-logfile - --error-logfile - "run:app"' >> /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

CMD ["/app/entrypoint.sh"]
