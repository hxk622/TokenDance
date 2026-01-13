# TokenDance

**Universal AI Agent Platform - Next Generation AI Agent System**

TokenDance is a cutting-edge AI agent platform that combines Personal and Team modes, enabling seamless collaboration through KV-Cache snapshot sharing, Logits Masking-based permission control, and automatic Token budget governance.

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local backend development)
- Node.js 18+ (for local frontend development)

### Development with Docker Compose

```bash
# Start all services (PostgreSQL, Redis, Backend, Frontend)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

Access the application:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/v1/docs
- **Health Check**: http://localhost:8000/health

### Local Development (Without Docker)

#### Backend

```bash
cd backend

# Install Poetry (if not installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Copy environment variables
cp .env.example .env
# Edit .env and fill in required values

# Run database migrations
poetry run alembic upgrade head

# Start development server
poetry run python -m app.main
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## 📁 Project Structure

```
TokenDance/
├── backend/                 # FastAPI Backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Core configuration
│   │   ├── models/         # Database models
│   │   ├── services/       # Business logic
│   │   └── main.py         # Application entry
│   ├── tests/              # Unit tests
│   ├── alembic/            # Database migrations
│   ├── pyproject.toml      # Python dependencies
│   └── Dockerfile.dev      # Development Dockerfile
│
├── frontend/               # Vue 3 Frontend
│   ├── src/
│   │   ├── api/           # API client
│   │   ├── components/    # Vue components
│   │   ├── views/         # Page components
│   │   ├── stores/        # Pinia stores
│   │   ├── router/        # Vue Router
│   │   └── main.ts        # Application entry
│   ├── package.json       # Node dependencies
│   ├── vite.config.ts     # Vite configuration
│   └── Dockerfile.dev     # Development Dockerfile
│
├── docs/                   # Documentation
│   ├── architecture/       # Architecture design
│   └── modules/            # Module specifications
│
└── docker-compose.yml      # Docker Compose configuration
```

## 🏗️ Architecture Highlights

### Core Differentiators

1. **Workspace = KV-Cache Isolation + Long-term Asset**
   - Physical isolation of KV-Cache per workspace
   - File system as persistent memory
   - Smart compression with FileSystemPointer

2. **Teams = Shared Intelligence Pool + Resource Governance**
   - KV-Cache snapshot sharing (expert agents published to team)
   - Logits Masking-based atomic permission control
   - Automatic Token budget governance

3. **Dual Mode Design**
   - **Personal Mode**: Direct workspace creation without Organization/Team
   - **Team Mode**: Organization → Team → Workspace hierarchy

## 🛠️ Development

### Running Tests

```bash
# Backend tests
cd backend
poetry run pytest

# Frontend tests
cd frontend
npm run test
```

### Code Quality

```bash
# Backend linting & formatting
cd backend
poetry run black app/
poetry run isort app/
poetry run ruff app/
poetry run mypy app/

# Frontend linting & formatting
cd frontend
npm run lint
npm run format
npm run type-check
```

### Database Migrations

```bash
cd backend

# Create a new migration
poetry run alembic revision --autogenerate -m "description"

# Apply migrations
poetry run alembic upgrade head

# Rollback one migration
poetry run alembic downgrade -1
```

## 📊 Monitoring

- **Metrics**: http://localhost:8000/metrics (Prometheus format)
- **Logs**: Structured JSON logs in production, pretty console in development
- **Health Checks**: `/health` and `/readiness` endpoints

## 🔒 Security

- JWT-based authentication
- Row-Level Security (RLS) for multi-tenancy
- Logits Masking for atomic permission control
- Secrets management via environment variables

## 📝 Environment Variables

### Backend

See `backend/.env.example` for all available configuration options.

Key variables:
- `SECRET_KEY`: JWT secret (min 32 characters)
- `POSTGRES_*`: Database connection
- `REDIS_*`: Redis connection
- `ANTHROPIC_API_KEY`: LLM API key

### Frontend

See `frontend/.env.example` for configuration.

Key variables:
- `VITE_API_BASE_URL`: Backend API URL

## 🚧 Development Roadmap

**Phase 0 (Current)**: Project scaffolding ✅
**Phase 1 (Week 1-4)**: Personal mode MVP + E2E path
**Phase 2 (Week 5-8)**: Agent core capabilities + WebSocket
**Phase 3 (Week 9-12)**: Team mode + Advanced features
**Phase 4 (Week 13-16)**: Polish + Public beta

See [docs/plans/](docs/plans/) for detailed development plans.

## 📚 Documentation

- [Architecture Overview](docs/architecture/HLD.md)
- [Multi-Tenancy Design](docs/architecture/Multi-Tenancy-v2.md)
- [FileSystem Module](docs/modules/FileSystem.md)
- [Context Compression](docs/modules/Context-Compression.md)

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is proprietary and confidential.

## 👥 Team

- **Product**: TokenDance Team
- **Architecture**: Based on comprehensive design docs

---

**Built with** ❤️ **using FastAPI, Vue 3, PostgreSQL, Redis, and Claude AI**
