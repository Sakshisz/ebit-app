# Multi-stage build for production
FROM python:3.11-slim as base

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY data/ ./data/

# Expose ports
EXPOSE 8000 8501

# Create startup script
COPY docker-entrypoint.sh .
RUN chmod +x docker-entrypoint.sh

CMD ["./docker-entrypoint.sh"]
