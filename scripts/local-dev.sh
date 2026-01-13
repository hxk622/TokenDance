#!/bin/bash
# Local development setup (without Docker)

set -e

echo "🚀 TokenDance Local Development Setup"
echo "======================================"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

cd "$(dirname "$0")/.."

# Step 1: Setup environment variables
echo -e "\n${YELLOW}Step 1: Setting up environment variables...${NC}"
if [ ! -f "backend/.env" ]; then
    echo "Creating backend/.env from template..."
    cp backend/.env.example backend/.env
    
    # Generate SECRET_KEY
    SECRET_KEY=$(openssl rand -base64 32)
    sed -i '' "s|your_secret_key_here_min_32_characters_long_change_me|${SECRET_KEY}|g" backend/.env
    
    # Update for local PostgreSQL
    sed -i '' "s|POSTGRES_HOST=localhost|POSTGRES_HOST=localhost|g" backend/.env
    sed -i '' "s|POSTGRES_PASSWORD=your_postgres_password_here|POSTGRES_PASSWORD=|g" backend/.env
    sed -i '' "s|REDIS_HOST=localhost|REDIS_HOST=localhost|g" backend/.env
    
    echo -e "${GREEN}✓ Created backend/.env${NC}"
else
    echo -e "${GREEN}✓ backend/.env already exists${NC}"
fi

# Step 2: Check PostgreSQL
echo -e "\n${YELLOW}Step 2: Checking PostgreSQL...${NC}"
if pg_isready -q 2>/dev/null; then
    echo -e "${GREEN}✓ PostgreSQL is running${NC}"
else
    echo -e "${YELLOW}⚠ PostgreSQL is not running. Starting...${NC}"
    brew services start postgresql@16 || brew services start postgresql || {
        echo -e "${RED}Failed to start PostgreSQL. Please start it manually.${NC}"
        exit 1
    }
    sleep 3
fi

# Step 3: Create database if not exists
echo -e "\n${YELLOW}Step 3: Creating database...${NC}"
if psql -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw tokendance; then
    echo -e "${GREEN}✓ Database 'tokendance' already exists${NC}"
else
    createdb tokendance 2>/dev/null && echo -e "${GREEN}✓ Created database 'tokendance'${NC}" || {
        echo -e "${YELLOW}⚠ Could not create database (it might already exist)${NC}"
    }
fi

# Step 4: Check Redis
echo -e "\n${YELLOW}Step 4: Checking Redis...${NC}"
if redis-cli ping >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Redis is running${NC}"
else
    echo -e "${YELLOW}⚠ Redis is not running. Starting...${NC}"
    brew services start redis || {
        echo -e "${RED}Failed to start Redis. Please start it manually.${NC}"
        exit 1
    }
    sleep 2
fi

# Step 5: Install Python dependencies
echo -e "\n${YELLOW}Step 5: Installing Python dependencies...${NC}"
if ! command -v poetry &> /dev/null; then
    echo -e "${YELLOW}Installing Poetry...${NC}"
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="$HOME/.local/bin:$PATH"
fi

cd backend
poetry install
cd ..
echo -e "${GREEN}✓ Python dependencies installed${NC}"

# Step 6: Run database migrations
echo -e "\n${YELLOW}Step 6: Running database migrations...${NC}"
cd backend
poetry run alembic upgrade head 2>/dev/null || {
    echo -e "${YELLOW}⚠ No migrations to run yet. You can create one with:${NC}"
    echo -e "  ${GREEN}poetry run alembic revision --autogenerate -m \"Initial migration\"${NC}"
}
cd ..

# Step 7: Install Node.js dependencies
echo -e "\n${YELLOW}Step 7: Installing Node.js dependencies...${NC}"
if ! command -v node &> /dev/null; then
    echo -e "${RED}Node.js is not installed. Please install it first.${NC}"
    exit 1
fi

cd frontend
npm install
cd ..
echo -e "${GREEN}✓ Node.js dependencies installed${NC}"

# Done!
echo -e "\n${GREEN}✨ Setup complete!${NC}"
echo -e "\n${YELLOW}To start development:${NC}"
echo ""
echo -e "Terminal 1 (Backend):"
echo -e "  ${GREEN}cd backend && poetry run python -m app.main${NC}"
echo ""
echo -e "Terminal 2 (Frontend):"
echo -e "  ${GREEN}cd frontend && npm run dev${NC}"
echo ""
echo -e "\nServices will be available at:"
echo -e "  Frontend:    ${GREEN}http://localhost:5173${NC}"
echo -e "  Backend API: ${GREEN}http://localhost:8000${NC}"
echo -e "  API Docs:    ${GREEN}http://localhost:8000/api/v1/docs${NC}"
echo -e "  Health:      ${GREEN}http://localhost:8000/health${NC}"
