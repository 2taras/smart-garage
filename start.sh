#!/bin/bash

# Configuration
DOMAIN="dg.2taras.site"
TUNNEL_NAME="garage-tunnel"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Function to check if cloudflared is installed
check_cloudflared() {
    if ! command -v cloudflared &> /dev/null; then
        echo -e "${RED}cloudflared is not installed.${NC}"
        echo "Installing cloudflared..."
        
        curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
        sudo dpkg -i cloudflared.deb
        rm cloudflared.deb
        
        echo -e "${GREEN}cloudflared installed successfully.${NC}"
    fi
}

# Function to create and configure tunnel
setup_tunnel() {
    echo -e "${YELLOW}Setting up Cloudflare Tunnel...${NC}"
    
    echo "Please login to Cloudflare in your browser..."
    cloudflared tunnel login
    
    echo "Creating tunnel..."
    cloudflared tunnel create $TUNNEL_NAME
    
    rm ~/.cloudflared/config.yml

    TUNNEL_ID=$(cloudflared tunnel list | grep $TUNNEL_NAME | awk '{print $1}')
    FULL_CRED_PATH=$(dir ~/.cloudflared/${TUNNEL_ID}.json)
    
    cat > ~/.cloudflared/config.yml << EOF
tunnel: ${TUNNEL_ID}
credentials-file: ${FULL_CRED_PATH}

ingress:
  - hostname: ${DOMAIN}
    path: /ws/*
    service: http://localhost:8000
    originRequest:
      noTLSVerify: true

  - hostname: ${DOMAIN}
    path: /api/*
    service: http://localhost:5000

  - hostname: ${DOMAIN}
    path: /*
    service: http://localhost:3000
  
  - service: http_status:404
EOF
    
    echo "Creating DNS record..."
    cloudflared tunnel route dns -f $TUNNEL_NAME $DOMAIN
    
    echo -e "${GREEN}Tunnel setup complete!${NC}"
}

# Function to start all services
start_services() {
    cleanup() {
        echo -e "\n${YELLOW}Cleaning up...${NC}"
        
        if [ -n "$NEXT_PID" ]; then
            kill $NEXT_PID 2>/dev/null
        fi
        
        kill $(jobs -p) 2>/dev/null
        pkill cloudflared
        
        echo -e "${GREEN}All services stopped.${NC}"
        exit 0
    }
    
    trap cleanup SIGINT
    
    echo -e "${YELLOW}Starting Cloudflare tunnel...${NC}"
    cloudflared tunnel run $TUNNEL_NAME &
    
    sleep 2
    
    echo -e "${YELLOW}Starting services...${NC}"
    
    # Start FastAPI backend (API)
    echo "Starting FastAPI API backend..."
    cd server
    uvicorn web:app --host 0.0.0.0 --port 5000 --reload &
    
    # Start FastAPI backend (WebSocket)
    echo "Starting FastAPI WebSocket backend..."
    uvicorn server:app --host 0.0.0.0 --port 8000 --reload &
    
    # Start Telegram bot
    echo "Starting Telegram bot..."
    python bot.py &
    cd ..
    
    # Start Next.js frontend
    echo "Starting Next.js frontend..."
    cd web
    npm run dev &
    NEXT_PID=$!
    cd ..
    
    echo -e "${GREEN}All services started!${NC}"
    echo -e "Application available at: ${YELLOW}https://${DOMAIN}${NC}"
    echo -e "API docs available at: ${YELLOW}https://${DOMAIN}/api/docs${NC}"
    echo -e "Press ${RED}Ctrl+C${NC} to stop all services.\n"
    
    wait
}

# Main script
main() {
    echo -e "${YELLOW}Service Manager${NC}"
    echo "----------------------------------------"
    
    check_cloudflared
    
    if ! cloudflared tunnel list | grep -q $TUNNEL_NAME; then
        setup_tunnel
    fi
    
    start_services
}

main