#!/bin/bash

# Exit on any error
set -e

echo "Starting Letraz servers..."

# Start gRPC server in background
echo "Starting gRPC server..."
python manage.py grpcrunaioserver &
GRPC_PID=$!

echo "Started gRPC server..."

# Start Django REST API server with gunicorn
echo "Starting Django REST API server..."
exec gunicorn letraz_server.wsgi:application --bind 0.0.0.0:8000 --workers=${WORKERS:-4} &
GUNICORN_PID=$!

# Function to handle shutdown gracefully
cleanup() {
    echo "Shutting down servers..."
    kill $GRPC_PID $GUNICORN_PID 2>/dev/null || true
    wait $GRPC_PID $GUNICORN_PID 2>/dev/null || true
    echo "Servers stopped."
    exit 0
}

# Trap signals for graceful shutdown
trap cleanup SIGTERM SIGINT

# Wait for both processes
wait $GRPC_PID $GUNICORN_PID