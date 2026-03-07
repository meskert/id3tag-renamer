FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MUSIC_DIR=/music

WORKDIR /app

# Build-time dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy only what is needed to build the package
COPY pyproject.toml README.md ./
COPY src/ ./src

# Build wheels for the project (and its dependencies)
RUN pip wheel --no-cache-dir --wheel-dir /wheels .


FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MUSIC_DIR=/music

WORKDIR /app

# Runtime system dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libchromaprint-tools \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install application and dependencies from wheels built in the builder stage
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# Create application user and music directory with appropriate permissions
RUN useradd -m appuser \
    && mkdir -p "${MUSIC_DIR}" \
    && chown -R appuser:appuser "${MUSIC_DIR}"

USER appuser

EXPOSE 8000

CMD ["id3tag-renamer"]
