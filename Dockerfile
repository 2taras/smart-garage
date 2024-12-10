# Use Python and Node.js as the base environment.
FROM python:3.9-slim

# Install Node.js and necessary packages for Python
RUN apt-get update && apt-get install -y curl build-essential && \
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean

# Set the working directory
WORKDIR /app

# Copy all the code into the container
COPY . .

# Install Python dependencies
COPY server/requirements.txt server/requirements.txt
RUN pip install --no-cache-dir -r server/requirements.txt

# Install Node.js dependencies for the Next.js app
WORKDIR /app/web
RUN npm install

# Expose all the required ports
EXPOSE 3000 5000 8000

# Return to root working directory
WORKDIR /app

# Define the command to start all services
CMD ["bash", "-c", "\
    echo 'Starting API backend...' && \
    cd /app/server && python3 -m uvicorn web:app --host 0.0.0.0 --port 5000 --reload & \
    echo 'Starting WebSocket backend...' && \
    cd /app/server && python3 -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload & \
    echo 'Starting Telegram bot...' && \
    cd /app/server && python3 bot.py & \
    echo 'Starting Next.js frontend...' && \
    cd /app/web && npm run dev & \
    wait"]