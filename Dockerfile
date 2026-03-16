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

# Download AWS RDS Global Bundle for secure DB connections
RUN curl -sS https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem -o global-bundle.pem

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
# --frozen ensures we use the lockfile exactly
RUN uv sync --frozen --no-cache --no-dev

# Copy the rest of the application code
COPY . .

# Ensure entrypoint script is executable
RUN chmod +x /app/scripts/entrypoint.sh

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=config.settings.prod

# Collect static files during build (baked into image)
RUN SECRET_KEY=build-only-key \
    DATABASE_URL=sqlite:///tmp/db.sqlite3 \
    OTP_EXPIRY_MINUTES=5 \
    USER_DATA_RETENTION_DAYS=30 \
    UNVERIFIED_USER_CLEANUP_HOURS=24 \
    uv run python manage.py collectstatic --no-input

# Expose the API port
EXPOSE 8000

# Use the entrypoint script
ENTRYPOINT ["/app/scripts/entrypoint.sh"]

# Default to starting the web service
CMD ["web"]
