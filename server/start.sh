#!/bin/bash

# File: start_services.sh

# Function to kill all background processes on exit
cleanup() {
    echo -e "\nCleaning up..."
    kill $(jobs -p) 2>/dev/null
    exit 0
}

# Trap Ctrl+C (SIGINT) and call cleanup
trap cleanup SIGINT

# Start services in background
echo "Starting FastAPI web service..."
uvicorn web:app --reload --host 0.0.0.0 --port 5000 &

echo "Starting Telegram bot..."
python bot.py &

echo "Starting FastAPI server..."
uvicorn server:app --reload --host 0.0.0.0 &

echo -e "\nAll services started. Press Ctrl+C to stop all services.\n"

# Wait for any process to exit
wait

# Cleanup on exit
cleanup