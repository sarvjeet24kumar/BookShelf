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

# Expose the API port
EXPOSE 8000

# Default command (can be overridden by docker-compose)
CMD ["uv run", "uvicorn", "config.asgi:application", "--host", "0.0.0.0", "--port", "8000"]
