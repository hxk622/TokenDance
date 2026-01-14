#!/bin/bash

# TokenDance System Check Script
# Checks if frontend and backend are running and ready

set -e

echo "🔍 TokenDance System Check"
echo "================================"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Backend
echo -n "Checking Backend (http://localhost:8000)... "
if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Running${NC}"
    BACKEND_VERSION=$(curl -s http://localhost:8000/health | grep -o '"version":"[^"]*"' | cut -d'"' -f4)
    echo "  Version: $BACKEND_VERSION"
else
    echo -e "${RED}✗ Not responding${NC}"
    echo -e "${YELLOW}  Start with: cd backend && uv run uvicorn app.main:app --reload${NC}"
    BACKEND_ERROR=1
fi

# Check Frontend
echo -n "Checking Frontend (http://localhost:5173)... "
if curl -s -f http://localhost:5173 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Running${NC}"
else
    echo -e "${RED}✗ Not responding${NC}"
    echo -e "${YELLOW}  Start with: cd frontend && npm run dev${NC}"
    FRONTEND_ERROR=1
fi

echo ""
echo "================================"

# API Endpoints Check (if backend is running)
if [ -z "$BACKEND_ERROR" ]; then
    echo "📡 Testing API Endpoints..."
    
    # Health check
    echo -n "  /health... "
    if curl -s -f http://localhost:8000/health > /dev/null; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
    fi
    
    # API docs
    echo -n "  /api/v1/docs... "
    if curl -s -f http://localhost:8000/api/v1/docs > /dev/null; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
    fi
fi

echo ""

# Summary
if [ -z "$BACKEND_ERROR" ] && [ -z "$FRONTEND_ERROR" ]; then
    echo -e "${GREEN}✅ System is ready!${NC}"
    echo ""
    echo "Access the application:"
    echo "  Frontend: http://localhost:5173"
    echo "  Backend API: http://localhost:8000"
    echo "  API Docs: http://localhost:8000/api/v1/docs"
    echo "  Demo UI: http://localhost:5173/demo"
    exit 0
else
    echo -e "${RED}❌ System is not fully operational${NC}"
    echo ""
    echo "Please start the missing services and try again."
    exit 1
fi
