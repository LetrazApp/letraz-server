# Use Python 3.12 slim image based on Debian Bookworm
FROM python:3.12-slim-bookworm

# Set up working directory and volume
VOLUME /letraz
WORKDIR /letraz

# Copy uv package manager from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy application source code
COPY . .

# Configure UV environment
ENV UV_PROJECT_ENVIRONMENT="/usr/local/"

# Install system dependencies required for Python packages
RUN apt-get update && apt-get -y install libpq-dev gcc

# Install Python dependencies using UV
RUN uv sync

# Add gunicorn WSGI server
RUN uv add gunicorn

# Collect static files for Django application
RUN python manage.py collectstatic --noinput

# Expose application port
EXPOSE 8000

# Start the application using Gunicorn WSGI server
ENTRYPOINT ["gunicorn", "letraz_server.wsgi:application", "--bind", "0.0.0.0:8000"]
