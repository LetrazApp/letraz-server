#!/bin/bash
set -e

# Pull the latest image
docker pull ${DOCKER_USERNAME}/letraz-server:${IMAGE_TAG}

# Stop and remove the existing container if it exists
docker stop letraz-server || true
docker rm letraz-server || true

# Run the new container
docker run --env-file /path/to/letraz-server/.env \
  --name letraz-server \
  -p 8000:8000 \
  -v /path/to/letraz-server/media:/letraz/media \
  -v /path/to/letraz-server/logs:/letraz/logs \
  -d ${DOCKER_USERNAME}/letraz-server:${IMAGE_TAG} --workers=2

# Clean up old images
docker system prune -f 