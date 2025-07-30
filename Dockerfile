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

# Copy and make startup script executable
COPY start-servers.sh .
RUN chmod +x start-servers.sh

# Expose both REST API and gRPC ports
EXPOSE 8000 50051

# Start both servers using the startup script
ENTRYPOINT ["./start-servers.sh"]