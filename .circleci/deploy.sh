#!/bin/bash

# Production deployment script for letraz-server
# This script handles the safe deployment of the new Docker image with rollback capabilities

set -e  # Exit on any error

# Configuration
DOCKER_TAG=${1:-"latest"}
CONTAINER_NAME="letraz-server"
BACKUP_CONTAINER_NAME="letraz-server-backup"
REGISTRY="ghcr.io/letrazapp"
IMAGE_NAME="letraz-server"
FULL_IMAGE_NAME="${REGISTRY}/${IMAGE_NAME}:${DOCKER_TAG}"
HEALTH_CHECK_URL="http://localhost:8000/health"
HEALTH_CHECK_TIMEOUT=60
HEALTH_CHECK_INTERVAL=5
WORKERS=3

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

# Function to check if container is running
is_container_running() {
    local container_name=$1
    docker ps --filter "name=${container_name}" --format "{{.Names}}" | grep -q "^${container_name}$"
}

# Function to check if container exists
container_exists() {
    local container_name=$1
    docker ps -a --filter "name=${container_name}" --format "{{.Names}}" | grep -q "^${container_name}$"
}

# Function to wait for health check
wait_for_health() {
    local timeout=$1
    local interval=$2
    local elapsed=0
    
    log "Waiting for health check to pass..."
    
    while [ $elapsed -lt $timeout ]; do
        if curl -f -s "$HEALTH_CHECK_URL" > /dev/null 2>&1; then
            log "Health check passed!"
            return 0
        fi
        
        # Try a simple connectivity check if health endpoint is not available
        if curl -f -s "http://localhost:8000/" > /dev/null 2>&1; then
            log "Service is responding (health endpoint may not be implemented)"
            return 0
        fi
        
        sleep $interval
        elapsed=$((elapsed + interval))
        echo -n "."
    done
    
    error "Health check failed after ${timeout}s"
    return 1
}

# Function to rollback to previous version
rollback() {
    error "Deployment failed. Initiating rollback..."
    
    # Stop the failed container
    if is_container_running "$CONTAINER_NAME"; then
        log "Stopping failed container..."
        docker stop "$CONTAINER_NAME" || true
        docker rm "$CONTAINER_NAME" || true
    fi
    
    # Start the backup container if it exists
    if container_exists "$BACKUP_CONTAINER_NAME"; then
        log "Starting backup container..."
        docker rename "$BACKUP_CONTAINER_NAME" "$CONTAINER_NAME"
        docker start "$CONTAINER_NAME"
        
        # Wait for rollback to be healthy
        if wait_for_health $HEALTH_CHECK_TIMEOUT $HEALTH_CHECK_INTERVAL; then
            log "Rollback successful!"
            return 0
        else
            error "Rollback failed - manual intervention required!"
            return 1
        fi
    else
        error "No backup container found - manual intervention required!"
        return 1
    fi
}

# Function to cleanup old images
cleanup_old_images() {
    log "Cleaning up old Docker images..."
    
    # Keep only the last 3 images
    docker images "${REGISTRY}/${IMAGE_NAME}" --format "{{.Repository}}:{{.Tag}}" | \
        grep -v "latest" | \
        sort -V | \
        head -n -3 | \
        xargs -r docker rmi || true
}

# Function to run Django migrations
run_migrations() {
    log "Running Django migrations..."
    
    # Create a temporary container to run migrations
    docker run --rm \
        --env-file .env \
        -v $(pwd)/data:/app/data \
        "$FULL_IMAGE_NAME" \
        python manage.py migrate --noinput
    
    if [ $? -eq 0 ]; then
        log "Django migrations completed successfully"
    else
        error "Django migrations failed"
        return 1
    fi
}

# Function to collect static files
collect_static() {
    log "Collecting static files..."
    
    # Create a temporary container to collect static files
    docker run --rm \
        --env-file .env \
        -v $(pwd)/static:/app/static \
        "$FULL_IMAGE_NAME" \
        python manage.py collectstatic --noinput
    
    if [ $? -eq 0 ]; then
        log "Static files collected successfully"
    else
        warn "Static files collection failed (this might be expected)"
    fi
}

# Main deployment function
deploy() {
    log "Starting deployment of ${FULL_IMAGE_NAME}..."
    
    # Check if .env file exists
    if [ ! -f ".env" ]; then
        error ".env file not found in current directory"
        return 1
    fi
    
    # Pull the new image
    log "Pulling new Docker image: ${FULL_IMAGE_NAME}..."
    if ! docker pull "$FULL_IMAGE_NAME"; then
        error "Failed to pull Docker image"
        return 1
    fi
    
    # Run Django migrations
    run_migrations
    
    # Collect static files
    collect_static
    
    # Create backup of current container if it exists
    if is_container_running "$CONTAINER_NAME"; then
        log "Creating backup of current container..."
        
        # Remove old backup if it exists
        if container_exists "$BACKUP_CONTAINER_NAME"; then
            docker rm -f "$BACKUP_CONTAINER_NAME" || true
        fi
        
        # Stop current container and rename it as backup
        docker stop "$CONTAINER_NAME"
        docker rename "$CONTAINER_NAME" "$BACKUP_CONTAINER_NAME"
        
        log "Current container backed up as ${BACKUP_CONTAINER_NAME}"
    fi
    
    # Create necessary directories
    mkdir -p data logs static media
    
    # Start new container
    log "Starting new container with image: ${FULL_IMAGE_NAME}..."
    docker run -d \
        --name "$CONTAINER_NAME" \
        --env-file .env \
        -p 8000:8000 \
        --restart unless-stopped \
        --memory=2g \
        --log-driver json-file \
        --log-opt max-size=10m \
        --log-opt max-file=3 \
        -v $(pwd)/data:/app/data \
        -v $(pwd)/logs:/app/logs \
        -v $(pwd)/static:/app/static \
        -v $(pwd)/media:/app/media \
        "$FULL_IMAGE_NAME" \
        --workers="$WORKERS"
    
    # Wait for the new container to be healthy
    if wait_for_health $HEALTH_CHECK_TIMEOUT $HEALTH_CHECK_INTERVAL; then
        log "New container is healthy!"
        
        # Remove backup container if deployment was successful
        if container_exists "$BACKUP_CONTAINER_NAME"; then
            log "Removing backup container..."
            docker rm "$BACKUP_CONTAINER_NAME"
        fi
        
        # Cleanup old images
        cleanup_old_images
        
        log "Deployment completed successfully!"
        return 0
    else
        error "New container failed health check"
        rollback
        return 1
    fi
}

# Function to display deployment status
show_status() {
    log "=== Deployment Status ==="
    log "Docker Tag: ${DOCKER_TAG}"
    log "Image: ${FULL_IMAGE_NAME}"
    log "Health Check URL: ${HEALTH_CHECK_URL}"
    log "Workers: ${WORKERS}"
    
    if is_container_running "$CONTAINER_NAME"; then
        log "Container Status: Running"
        log "Container ID: $(docker ps --filter "name=${CONTAINER_NAME}" --format "{{.ID}}")"
        log "Container Uptime: $(docker ps --filter "name=${CONTAINER_NAME}" --format "{{.Status}}")"
    else
        warn "Container Status: Not Running"
    fi
    
    log "=========================="
}

# Function to show help
show_help() {
    echo "Usage: $0 [DOCKER_TAG]"
    echo ""
    echo "Deploy letraz-server with the specified Docker tag"
    echo ""
    echo "Parameters:"
    echo "  DOCKER_TAG    Docker image tag to deploy (default: latest)"
    echo ""
    echo "Options:"
    echo "  --help, -h    Show this help message"
    echo "  --status, -s  Show deployment status"
    echo ""
    echo "Examples:"
    echo "  $0 latest"
    echo "  $0 abc1234"
    echo "  $0 v1.0.0"
    echo ""
    echo "Environment:"
    echo "  Requires .env file in current directory"
    echo "  Container will be named: $CONTAINER_NAME"
    echo "  Workers: $WORKERS"
    echo ""
}

# Main execution
main() {
    if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
        show_help
        exit 0
    fi
    
    if [ "$1" = "--status" ] || [ "$1" = "-s" ]; then
        show_status
        exit 0
    fi
    
    log "Starting letraz-server deployment..."
    log "Docker tag: ${DOCKER_TAG}"
    
    # Ensure we're in the correct directory
    if [ ! -f ".env" ]; then
        error "Please run this script from the directory containing the .env file"
        exit 1
    fi
    
    # Load environment variables from .env file
    if [ -f ".env" ]; then
        log "Loading environment variables from .env file..."
        set -a  # automatically export all variables
        source .env
        set +a  # stop automatically exporting
    fi
    
    # Login to GitHub Container Registry
    if [ -n "$GITHUB_TOKEN" ] && [ -n "$GITHUB_USERNAME" ]; then
        log "Logging in to GitHub Container Registry..."
        echo "$GITHUB_TOKEN" | docker login ghcr.io -u "$GITHUB_USERNAME" --password-stdin
    else
        warn "GitHub credentials not found. Make sure GITHUB_TOKEN and GITHUB_USERNAME are set in .env file."
    fi
    
    # Run deployment
    if deploy; then
        log "🎉 Deployment successful!"
        show_status
        exit 0
    else
        error "💥 Deployment failed!"
        exit 1
    fi
}

# Run main function with all arguments
main "$@" 