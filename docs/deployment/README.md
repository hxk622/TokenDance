# TokenDance 部署指南

## 目录

- [本地开发环境](#本地开发环境)
- [Docker Compose 部署](#docker-compose-部署)
- [生产环境部署](#生产环境部署)
- [环境变量配置](#环境变量配置)
- [数据库迁移](#数据库迁移)
- [监控与日志](#监控与日志)
- [常见问题](#常见问题)

---

## 本地开发环境

### 系统要求

- macOS / Linux / Windows (WSL2)
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+

### 后端启动

```bash
# 1. 进入后端目录
cd backend

# 2. 安装 uv (Python 包管理器)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. 安装依赖
uv sync --all-extras

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填写必要配置

# 5. 运行数据库迁移
uv run alembic upgrade head

# 6. 启动开发服务器
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 前端启动

```bash
# 1. 进入前端目录
cd frontend

# 2. 安装依赖 (推荐 pnpm)
pnpm install
# 或使用 npm: npm install

# 3. 配置环境变量
cp .env.example .env.local
# 编辑 .env.local

# 4. 启动开发服务器
pnpm dev
# 访问 http://localhost:5173
```

---

## Docker Compose 部署

### 快速启动

```bash
# 克隆项目
git clone https://github.com/hxk622/TokenDance.git
cd TokenDance

# 复制环境变量
cp .env.example .env

# 编辑环境变量
# 至少需要配置: SECRET_KEY, ANTHROPIC_API_KEY

# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 服务组件

| 服务 | 端口 | 说明 |
|------|------|------|
| frontend | 5173 | Vue 3 前端 |
| backend | 8000 | FastAPI 后端 |
| postgres | 5432 | PostgreSQL 数据库 |
| redis | 6379 | Redis 缓存 |

### 访问地址

- 前端: http://localhost:5173
- API: http://localhost:8000
- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

### docker-compose.yml 配置

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: tokendance
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-tokendance}
      POSTGRES_DB: tokendance
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U tokendance"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD:-tokendance}
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql+asyncpg://tokendance:${POSTGRES_PASSWORD:-tokendance}@postgres:5432/tokendance
      - REDIS_URL=redis://:${REDIS_PASSWORD:-tokendance}@redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    environment:
      - VITE_API_BASE_URL=http://localhost:8000
    ports:
      - "5173:80"
    depends_on:
      - backend

volumes:
  postgres_data:
  redis_data:
```

---

## 生产环境部署

### 推荐架构

```
                    ┌─────────────┐
                    │   Nginx     │
                    │  (Reverse   │
                    │   Proxy)    │
                    └──────┬──────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   ┌────▼────┐       ┌─────▼─────┐      ┌─────▼─────┐
   │Frontend │       │  Backend  │      │  Backend  │
   │ (Static)│       │ Instance 1│      │ Instance 2│
   └─────────┘       └─────┬─────┘      └─────┬─────┘
                           │                  │
                    ┌──────▼──────────────────▼──────┐
                    │     PostgreSQL (Primary)       │
                    │     + Redis Cluster            │
                    └────────────────────────────────┘
```

### Nginx 配置

```nginx
upstream backend {
    server backend1:8000;
    server backend2:8000;
    keepalive 32;
}

server {
    listen 80;
    server_name tokendance.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name tokendance.example.com;

    ssl_certificate /etc/ssl/certs/tokendance.crt;
    ssl_certificate_key /etc/ssl/private/tokendance.key;

    # 前端静态文件
    location / {
        root /var/www/tokendance/frontend;
        try_files $uri $uri/ /index.html;
        expires 1d;
        add_header Cache-Control "public, immutable";
    }

    # API 代理
    location /api/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # SSE 配置
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 86400s;
    }

    # 健康检查
    location /health {
        proxy_pass http://backend/health;
    }
}
```

### Kubernetes 部署 (可选)

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tokendance-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: tokendance-backend
  template:
    metadata:
      labels:
        app: tokendance-backend
    spec:
      containers:
      - name: backend
        image: tokendance/backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: tokendance-secrets
              key: database-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /readiness
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

---

## 环境变量配置

### 必需变量

| 变量 | 说明 | 示例 |
|------|------|------|
| `SECRET_KEY` | JWT 密钥 (≥32字符) | `your-super-secret-key-min-32-chars` |
| `DATABASE_URL` | PostgreSQL 连接 | `postgresql+asyncpg://user:pass@host:5432/db` |
| `REDIS_URL` | Redis 连接 | `redis://:password@host:6379/0` |
| `ANTHROPIC_API_KEY` | Claude API 密钥 | `sk-ant-api...` |

### 可选变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `LOG_LEVEL` | `INFO` | 日志级别 |
| `CORS_ORIGINS` | `["*"]` | 允许的跨域来源 |
| `MAX_CONNECTIONS` | `10` | 数据库连接池大小 |
| `WORKSPACE_ROOT_PATH` | `/tmp/tokendance` | 工作区根目录 |

### .env 示例

```env
# 必需
SECRET_KEY=your-super-secret-key-at-least-32-characters
DATABASE_URL=postgresql+asyncpg://tokendance:password@localhost:5432/tokendance
REDIS_URL=redis://:password@localhost:6379/0
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx

# 可选
LOG_LEVEL=INFO
CORS_ORIGINS=["http://localhost:5173","https://tokendance.example.com"]
WORKSPACE_ROOT_PATH=/var/lib/tokendance/workspaces
```

---

## 数据库迁移

### 初始化

```bash
cd backend

# 生成迁移
uv run alembic revision --autogenerate -m "initial"

# 应用迁移
uv run alembic upgrade head
```

### 生产环境迁移

```bash
# 1. 备份数据库
pg_dump -h localhost -U tokendance tokendance > backup.sql

# 2. 应用迁移
uv run alembic upgrade head

# 3. 验证
uv run alembic current
```

### 回滚

```bash
# 回滚一个版本
uv run alembic downgrade -1

# 回滚到特定版本
uv run alembic downgrade <revision_id>
```

---

## 监控与日志

### 健康检查端点

- `GET /health` - 基本健康检查
- `GET /readiness` - 就绪检查 (含数据库/Redis)

### Prometheus 指标

```bash
# 访问指标端点
curl http://localhost:8000/metrics
```

### 日志配置

```python
# 生产环境使用 JSON 格式
LOGGING = {
    "version": 1,
    "handlers": {
        "json": {
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s"
        }
    }
}
```

---

## 常见问题

### Q: 数据库连接失败

```
sqlalchemy.exc.OperationalError: could not connect to server
```

**解决**:
1. 检查 PostgreSQL 是否运行
2. 验证 `DATABASE_URL` 格式
3. 确认网络连通性

### Q: Redis 连接超时

```
redis.exceptions.ConnectionError: Error connecting to redis
```

**解决**:
1. 检查 Redis 是否运行
2. 验证密码配置
3. 检查防火墙规则

### Q: SSE 连接断开

**解决**:
1. 检查 Nginx `proxy_buffering off` 配置
2. 增加 `proxy_read_timeout`
3. 检查网络代理设置

### Q: 前端无法连接后端

**解决**:
1. 确认 `VITE_API_BASE_URL` 配置正确
2. 检查 CORS 配置
3. 验证 API 端点可访问

---

## 更新日志

- **2026-01-15**: 初始版本
