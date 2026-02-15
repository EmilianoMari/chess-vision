# Chess Vision Dockerfile
# Backend service for chess board position recognition using ML

FROM python:3.11-slim

LABEL maintainer="SeasGroup"
LABEL description="Chess board position recognition from photos - ML backend service"

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install system dependencies for OpenCV and ML libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    curl \
    ca-certificates \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create directories for models and data
RUN mkdir -p /app/models /app/data /app/logs

# Copy application code
COPY api/ ./api/
COPY src/ ./src/
COPY gunicorn.conf.py .

# Environment defaults
ENV HOST=0.0.0.0
ENV PORT=8002
ENV DEBUG=false

# ML Model Configuration
ENV CONFIDENCE_THRESHOLD=0.85
ENV ENABLE_TTA=true
ENV ENABLE_VALIDATION=true
ENV MAX_IMAGE_SIZE_MB=10
ENV PROCESSING_TIMEOUT_SEC=30

# Model paths (will be populated when models are trained)
ENV MODELS_DIR=/app/models

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD wget -q --spider http://localhost:${PORT}/health || exit 1

EXPOSE 8002

CMD ["gunicorn", "api.main:app", "-c", "gunicorn.conf.py"]
