#!/bin/bash
# Development environment setup script

set -e

echo "🚀 TokenDance Development Setup"
echo "================================"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running from project root
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}Error: Please run this script from the project root directory${NC}"
    exit 1
fi

# Step 1: Check prerequisites
echo -e "\n${YELLOW}Step 1: Checking prerequisites...${NC}"
command -v docker >/dev/null 2>&1 || { echo -e "${RED}Docker is required but not installed.${NC}" >&2; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo -e "${RED}Docker Compose is required but not installed.${NC}" >&2; exit 1; }
echo -e "${GREEN}✓ Docker and Docker Compose found${NC}"

# Step 2: Setup backend environment
echo -e "\n${YELLOW}Step 2: Setting up backend environment...${NC}"
if [ ! -f "backend/.env" ]; then
    echo "Creating backend/.env from template..."
    cp backend/.env.example backend/.env
    
    # Generate a random SECRET_KEY
    SECRET_KEY=$(openssl rand -base64 32)
    
    # Update SECRET_KEY in .env
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s|your_secret_key_here_min_32_characters_long_change_me|${SECRET_KEY}|g" backend/.env
    else
        # Linux
        sed -i "s|your_secret_key_here_min_32_characters_long_change_me|${SECRET_KEY}|g" backend/.env
    fi
    
    echo -e "${GREEN}✓ Created backend/.env with generated SECRET_KEY${NC}"
    echo -e "${YELLOW}⚠ Please edit backend/.env and add your ANTHROPIC_API_KEY if you have one${NC}"
else
    echo -e "${GREEN}✓ backend/.env already exists${NC}"
fi

# Step 3: Start database services
echo -e "\n${YELLOW}Step 3: Starting PostgreSQL and Redis...${NC}"
docker-compose up -d postgres redis
echo "Waiting for services to be ready..."
sleep 5
echo -e "${GREEN}✓ Database services started${NC}"

# Step 4: Check if we should use Docker or local development
echo -e "\n${YELLOW}Choose development mode:${NC}"
echo "1) Docker (full stack in containers)"
echo "2) Local (backend and frontend run locally, only DB in Docker)"
read -p "Enter choice [1 or 2]: " DEV_MODE

if [ "$DEV_MODE" = "1" ]; then
    echo -e "\n${YELLOW}Starting all services in Docker...${NC}"
    docker-compose up -d
    
    echo -e "\n${GREEN}✓ All services started!${NC}"
    echo -e "\nServices are available at:"
    echo -e "  Frontend:    ${GREEN}http://localhost:5173${NC}"
    echo -e "  Backend API: ${GREEN}http://localhost:8000${NC}"
    echo -e "  API Docs:    ${GREEN}http://localhost:8000/api/v1/docs${NC}"
    echo -e "\nView logs with: ${YELLOW}docker-compose logs -f${NC}"
    echo -e "Stop services with: ${YELLOW}docker-compose down${NC}"
    
elif [ "$DEV_MODE" = "2" ]; then
    echo -e "\n${YELLOW}Setting up local development environment...${NC}"
    
    # Check for uv
    if ! command -v uv &> /dev/null; then
        echo -e "${YELLOW}uv not found. Installing uv...${NC}"
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.local/bin:$PATH"
    fi
    
    # Install backend dependencies
    echo -e "\n${YELLOW}Installing backend dependencies...${NC}"
    cd backend
    uv sync --all-extras
    cd ..
    echo -e "${GREEN}✓ Backend dependencies installed${NC}"
    
    # Check for Node.js
    if ! command -v node &> /dev/null; then
        echo -e "${RED}Node.js is required but not installed. Please install Node.js 18+${NC}"
        exit 1
    fi
    
    # Install frontend dependencies
    echo -e "\n${YELLOW}Installing frontend dependencies...${NC}"
    cd frontend
    npm install
    cd ..
    echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
    
    echo -e "\n${GREEN}✓ Setup complete!${NC}"
    echo -e "\n${YELLOW}To start development:${NC}"
    echo -e "1. Backend:  ${GREEN}cd backend && uv run uvicorn app.main:app --reload${NC}"
    echo -e "2. Frontend: ${GREEN}cd frontend && npm run dev${NC}"
    echo -e "\nServices will be available at:"
    echo -e "  Frontend:    ${GREEN}http://localhost:5173${NC}"
    echo -e "  Backend API: ${GREEN}http://localhost:8000${NC}"
    echo -e "  API Docs:    ${GREEN}http://localhost:8000/api/v1/docs${NC}"
else
    echo -e "${RED}Invalid choice. Exiting.${NC}"
    exit 1
fi

echo -e "\n${GREEN}✨ Setup complete! Happy coding!${NC}"
