# Stage 1: Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install uv
RUN apt-get update && apt-get install -y libpq-dev gcc
RUN pip install uv

# Copy requirements and install dependencies
COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt
RUN uv pip install --system --no-cache gunicorn

# Copy the rest of the application code
COPY . .

# Stage 2: Final stage
FROM python:3.11-slim

RUN apt-get update && apt-get install -y tesseract-ocr libpq5 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed dependencies from the builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Make entrypoint script executable
RUN chmod +x /app/entrypoint.sh

# Expose the port Gunicorn will run on
EXPOSE 5000

# Set environment variables (can be overridden by docker-compose)
ENV FLASK_APP="wsgi:app"
ENV FLASK_ENV="development"

# Run migrations and start the application
ENTRYPOINT ["/app/entrypoint.sh"]
