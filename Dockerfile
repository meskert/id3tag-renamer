# Use a slim Python image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV MUSIC_DIR=/music

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libchromaprint-tools \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy application files
COPY . .

# Install the package
RUN pip install --no-cache-dir .

# Expose the port the app runs on
EXPOSE 8000

# Create music directory and set permissions
RUN mkdir -p /music && chmod 777 /music

# Create a non-root user
RUN useradd -m appuser
USER appuser

# Command to run the application
CMD ["id3tag-renamer"]
