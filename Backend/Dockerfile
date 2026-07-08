# Use a lightweight python base image
FROM python:3.10-slim

# Set working directory inside container
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies (build-essential needed for some packages if compiled from source)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY . .

# Run the app binding to the PORT environment variable injected by Render (defaulting to 8000)
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
