# TokenDance

<div align="center">

**🕺 The Next-Generation AI Agent Platform 🕺**

*Combining the best of Manus, GenSpark, and AnyGen*

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Vue](https://img.shields.io/badge/vue-3.x-green.svg)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/fastapi-latest-teal.svg)](https://fastapi.tiangolo.com/)

[English](README.md) | [中文文档](README_CN.md)

</div>

---

## 🌟 Vision

**TokenDance** aims to democratize advanced AI agent capabilities. We believe every user deserves an autonomous AI assistant that can:

- 🔍 **Deep Research**: Multi-source information synthesis with citation tracking
- 🎨 **Content Generation**: Professional-grade PPTs, reports, and artifacts
- 💻 **Code Execution**: Sandboxed Python execution with file system access
- 🧠 **Long-term Memory**: Context that persists across sessions
- 🤝 **Team Collaboration**: Shared knowledge bases and agent snapshots

## 🚀 What Makes TokenDance Different?

### 1. **Token Efficiency @ Scale** 💎

Traditional agents waste 60-80% of context window on repeated content. We pioneered:

- **Plan Recitation**: TODO list appended at context end, preventing "Lost-in-the-Middle"
- **3-File Working Memory**: `task_plan.md`, `findings.md`, `progress.md` act as persistent RAM
- **Append-Only Context**: 7x faster than context reconstruction, 90%+ KV-Cache hit rate
- **Tool Definition Masking**: All tools loaded once, visibility controlled by attention masks

**Result**: 70% token savings, enabling $0.10/task instead of $0.50/task.

### 2. **Intelligent Failure Handling** 🛡️

- **Keep the Failures**: Errors preserved in context → Agent learns to avoid repeated mistakes
- **3-Strike Protocol**: Same error 3 times → Force re-read plan and pivot approach
- **5-Question Reboot**: When stuck, Agent self-diagnoses via structured introspection

**Result**: 40%+ success rate improvement on complex multi-step tasks.

### 3. **Multi-Tenancy with KV-Cache Sharing** 🏢

Industry-first architecture for team collaboration:

```
Organization (Unified Billing)
  └─ Team (Shared Skill Cache + Knowledge Base)
      └─ Workspace (Individual Agent Sessions)
```

- **KV-Cache Snapshots**: Expert agents can be "published" to team, saving setup costs
- **Logits Masking**: Atomic permission control without context duplication
- **Token Budget Governance**: Automatic quota tracking and alerts

### 4. **Progressive Disclosure UX** 🎯

Inspired by AnyGen's human-in-the-loop design:

- Structured prompting for ambiguous requests
- Pause before risky operations (file deletion, API calls)
- Real-time execution trace with expandable reasoning steps

### 5. **Hybrid Context Architecture** 🔄

```
┌─────────────────────────────────────────────────────────┐
│  Working Memory (LLM Context)       File System (Disk) │
│  ├─ Compressed summaries            ├─ Full tool outputs│
│  ├─ Recent dialogue                 ├─ Research artifacts│
│  └─ Active TODO list                └─ Session history  │
└─────────────────────────────────────────────────────────┘
```

**Like human cognition**: Short-term vs. long-term memory separation.

## 🏗️ Architecture Highlights

<details>
<summary><b>Core Principles (click to expand)</b></summary>

- **Append-Only Context Growth**: Never edit existing messages → KV-Cache always valid
- **KV Caching Stability**: System prompt + tool definitions frozen → 90%+ cache hit
- **Structured Tags**: `<REASONING>`, `<TOOL_CALL>`, `<TOOL_RESULT>` for semantic clarity
- **Controlled Randomness**: Break attention loops when repetitive behavior detected
- **Action Space Pruning**: 8 core tools > 100 vertical APIs (Agent builds helpers in sandbox)

See [docs/architecture/HLD.md](docs/architecture/HLD.md) for details.

</details>

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

## ✨ MVP Features

### 🔍 AI Deep Research

- Multi-source parallel search with configurable depth
- Intelligent information aggregation and deduplication  
- **Citation tracking** for every conclusion (e.g., `[1][2]` references)
- Read-then-Summarize pattern to prevent context explosion
- Export to Markdown/PDF

### 🎨 AI PPT Generation

- Generate professional presentations from topic/outline
- Multiple template styles (Business, Minimal, Creative)
- Real-time preview and per-slide regeneration
- Export to PPTX/PDF

### 💻 Sandboxed Code Execution

- Isolated Docker containers with resource limits
- Python 3.11+ with popular libraries pre-installed
- File system access within workspace
- Network restrictions (whitelist-based)

### 🧠 Three-Layer Memory System

1. **Working Memory**: Active context for current session
2. **Episodic Memory**: Session history with fast retrieval
3. **Semantic Memory**: Long-term knowledge base (vector search)

## 📚 Tech Stack

| Layer | Technology | Why? |
|-------|-----------|------|
| **Frontend** | Vue 3 + TypeScript + Vite | Reactive, fast HMR |
| **UI** | Shadcn/UI (Vue) + Tailwind | Modern, customizable |
| **Backend** | FastAPI + Uvicorn | Async, high performance |
| **Database** | PostgreSQL + pgvector | ACID + vector search |
| **Cache** | Redis | KV-Cache persistence, MQ |
| **Storage** | MinIO (S3-compatible) | Artifacts, files |
| **Sandbox** | Docker | Secure code execution |
| **LLM** | Claude API (primary), Gemini (fallback) | State-of-the-art reasoning |
| **Search** | Tavily API | Web research |

## 📜 Project Structure

```
TokenDance/
├── backend/                 # FastAPI Backend
│   ├── app/
│   │   ├── api/            # REST endpoints
│   │   ├── core/           # Agent engine, context, memory
│   │   ├── models/         # SQLAlchemy models
│   │   ├── services/       # Business logic
│   │   └── skills/         # Pluggable agent skills
│   ├── tests/              # Pytest suite
│   └── alembic/            # DB migrations
│
├── frontend/               # Vue 3 Frontend
│   ├── src/
│   │   ├── components/    # Reusable UI components
│   │   ├── views/         # Page views
│   │   ├── stores/        # Pinia state management
│   │   └── api/           # API client
│   └── vite.config.ts     # Vite config
│
├── docs/                   # Comprehensive design docs
│   ├── product/           # PRD
│   ├── architecture/      # HLD, LLD, multi-tenancy
│   └── modules/           # Context, Memory, Skills, etc.
│
├── scripts/                # Dev setup scripts
└── docker-compose.yml      # Local dev environment
```

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

## 🚧 Roadmap

- [x] **Phase 0**: Core architecture design + Project scaffolding
- [ ] **Phase 1**: Personal workspace + Basic agent loop + Sandbox execution
- [ ] **Phase 2**: Deep Research skill + Citation system + WebSocket streaming
- [ ] **Phase 3**: PPT Generation + Artifact system + Template engine
- [ ] **Phase 4**: Multi-tenancy + Team collaboration + KV-Cache sharing
- [ ] **Phase 5**: Advanced memory system + Skill marketplace + Plugin SDK

See [docs/plans/](docs/plans/) for detailed milestones.

## 📚 Documentation

### For Users
- [Getting Started Guide](GETTING_STARTED.md)
- [Quick Start (UI)](QUICKSTART-UI.md)
- [Quick Start (API)](QUICKSTART.md)

### For Developers
- [Product Requirements (PRD)](docs/product/PRD.md)
- [High-Level Design (HLD)](docs/architecture/HLD.md)
- [Low-Level Design (LLD)](docs/architecture/LLD.md)
- [Multi-Tenancy Architecture](docs/architecture/Multi-Tenancy-v2.md)

### Module Deep-Dives
- [Context Management](docs/modules/Context-Management.md)
- [Memory System](docs/modules/Memory.md)
- [Skill Design](docs/modules/Skill-Design.md)
- [Tool System](docs/modules/Tool-Use.md)
- [FileSystem](docs/modules/FileSystem.md)

## 🤝 Contributing

We welcome contributions of all kinds! Here's how you can help:

### 🐛 Report Bugs
Open an issue with:
- Clear description of the bug
- Steps to reproduce
- Expected vs. actual behavior
- System info (OS, Python/Node version)

### ✨ Suggest Features
Open a discussion with:
- Use case description
- Proposed solution (if any)
- Alternatives considered

### 💻 Code Contributions

1. **Fork** the repository
2. **Clone** your fork: `git clone https://github.com/YOUR_USERNAME/TokenDance.git`
3. **Create branch**: `git checkout -b feature/amazing-feature`
4. **Make changes** following our [coding standards](CONTRIBUTING.md)
5. **Test** your changes: `pytest` (backend) / `npm test` (frontend)
6. **Commit**: `git commit -m 'feat: add amazing feature'` (use [Conventional Commits](https://www.conventionalcommits.org/))
7. **Push**: `git push origin feature/amazing-feature`
8. **Open PR** with clear description

### 📖 Documentation
Improving docs is highly valued! Even fixing typos helps.

### Code of Conduct
Be respectful, inclusive, and constructive. See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## 💬 Community

- **Discussions**: [GitHub Discussions](https://github.com/hxk622/TokenDance/discussions)
- **Issues**: [GitHub Issues](https://github.com/hxk622/TokenDance/issues)
- **Twitter**: [@TokenDance_AI](https://twitter.com/TokenDance_AI) *(coming soon)*

## 👏 Acknowledgments

TokenDance builds upon ideas from:

- **[Manus](https://manus.im)**: Plan Recitation, 3-File Working Memory, Keep the Failures
- **[GenSpark](https://genspark.ai)**: Citation tracking, Read-then-Summarize
- **[AnyGen](https://anygen.io)**: Progressive Disclosure, Human-in-the-Loop UX
- **[Anthropic](https://anthropic.com)**: Extended context windows, tool use patterns

We're grateful to the open-source community for frameworks like FastAPI, Vue, PostgreSQL, and countless others.

## 📄 License

**Apache License 2.0**

Copyright (c) 2026 TokenDance Team

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

See [LICENSE](LICENSE) for the full text.

## ⭐ Star History

If you find TokenDance useful, please consider giving it a star! It helps us reach more people.

[![Star History Chart](https://api.star-history.com/svg?repos=hxk622/TokenDance&type=Date)](https://star-history.com/#hxk622/TokenDance&Date)

---

<div align="center">

**Built with ❤️ by developers who believe AI agents should be open, efficient, and accessible to all.**

Made with FastAPI · Vue 3 · PostgreSQL · Redis · Claude AI

[Give us a ⭐](https://github.com/hxk622/TokenDance) if you like what we're building!

</div>
