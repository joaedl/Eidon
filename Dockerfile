# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for CadQuery/OpenCascade
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1 \
    libglu1 \
    libxrender1 \
    libxext6 \
    libxi6 \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Copy application code
COPY app/ ./app/

# Expose port (Fly.io will set PORT env var)
EXPOSE 8000

# Run the application
# Use PORT environment variable if set (Fly.io provides this)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

