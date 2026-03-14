# Use a slim Python image
FROM python:3.13-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
# --frozen ensures we use the lockfile exactly
RUN uv sync --frozen --no-cache --no-dev

# Copy the rest of the application code
COPY . .

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=config.settings.dev

# Collect static files during build (baked into image)
RUN SECRET_KEY=build-only-key \
    DATABASE_URL=sqlite:///tmp/db.sqlite3 \
    OTP_EXPIRY_MINUTES=5 \
    USER_DATA_RETENTION_DAYS=30 \
    UNVERIFIED_USER_CLEANUP_HOURS=24 \
    uv run python manage.py collectstatic --no-input

# Expose the API port
EXPOSE 8000

# Default command: Gunicorn
CMD ["uv", "run", "gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"]
