# syntax=docker/dockerfile:1

# Build stage
FROM python:3.12.3-slim AS builder

# Prevents Python from writing pyc files and keeps Python from buffering stdout and stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements.txt

# Final stage
FROM python:3.12.3-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Create a non-privileged user
ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    appuser

# Copy wheels from builder stage and install
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels/ /wheels/* && \
    rm -rf /wheels

# Proxy settings removed - now managed via .env file to avoid hardcoding
# This allows flexible proxy configuration per environment without rebuilding image

# Copy application code
COPY . .

# Set ownership to non-privileged user
RUN chown -R appuser:appuser /app

# Use non-privileged user
USER appuser
ENV RABBITMQ_HOST=rabbitmq
# Expose the port the application listens on
EXPOSE 8000
# Run the application
CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
