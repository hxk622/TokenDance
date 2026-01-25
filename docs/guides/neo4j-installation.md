# Neo4j 安装指南

> 适用于 macOS，用于 TokenDance Context Graph 服务

## 前置要求

- Java 17+ (已验证系统有 Java 17.0.1)

## 方案一：手动下载安装 (推荐)

### 1. 下载 Neo4j

由于网络限制，建议从以下渠道下载：

**官方下载** (需登录):
- https://neo4j.com/deployment-center/

**国内镜像** (如可访问):
- http://we-yun.com/index.php/blog/versions-56.html
- http://doc.we-yun.com:1008/

下载版本: `neo4j-community-5.26.0-unix.tar.gz` (或最新版)

### 2. 安装

```bash
# 创建安装目录
mkdir -p ~/opt

# 解压到 ~/opt/neo4j (请替换为您下载的文件路径)
tar -xzf ~/Downloads/neo4j-community-5.26.0-unix.tar.gz -C ~/opt
mv ~/opt/neo4j-community-5.26.0 ~/opt/neo4j
```

### 3. 配置 Java

```bash
# 创建环境配置
cat >> ~/.zshrc << 'EOF'
# Neo4j
export NEO4J_HOME=~/opt/neo4j
export JAVA_HOME=/Library/Java/JavaVirtualMachines/jdk-17.0.1.jdk/Contents/Home
export PATH=$NEO4J_HOME/bin:$PATH
EOF

# 应用配置
source ~/.zshrc
```

### 4. 配置 Neo4j

```bash
# 设置初始密码
$NEO4J_HOME/bin/neo4j-admin dbms set-initial-password tokendance

# 编辑配置 (可选)
# vi $NEO4J_HOME/conf/neo4j.conf
```

### 5. 启动测试

```bash
# 前台启动 (测试)
neo4j console

# 或后台启动
neo4j start
```

访问 http://localhost:7474 验证安装

### 6. 设置开机自启动

```bash
# 创建 launchd 配置
cat > ~/Library/LaunchAgents/com.neo4j.server.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.neo4j.server</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>export JAVA_HOME=/Library/Java/JavaVirtualMachines/jdk-17.0.1.jdk/Contents/Home && ~/opt/neo4j/bin/neo4j console</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/neo4j.stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/neo4j.stderr.log</string>
</dict>
</plist>
EOF

# 加载服务
launchctl load ~/Library/LaunchAgents/com.neo4j.server.plist
```

## 方案二：使用 Docker (需安装 Docker)

```bash
# 拉取镜像
docker pull neo4j:5.26.0-community

# 启动容器
docker run -d \
  --name neo4j \
  --restart always \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/tokendance \
  -v ~/data/neo4j:/data \
  neo4j:5.26.0-community
```

## 启用 TokenDance Neo4j 模式

安装完成后，修改 `backend/.env`:

```bash
# 将
CONTEXT_GRAPH_MODE=memory

# 改为
CONTEXT_GRAPH_MODE=neo4j
```

## 验证

```bash
cd /Users/xingkaihan/Documents/Code/TokenDance/backend

# 运行测试
uv run pytest tests/services/test_context_graph.py -v

# 检查 Neo4j 连接
uv run python -c "
import asyncio
from app.services.context_graph import get_context_graph_service
from app.services.context_graph.service import StorageMode

async def check():
    service = await get_context_graph_service(mode=StorageMode.NEO4J)
    print(f'Mode: {service.mode.value}')
    print(f'Neo4j connected: {service._neo4j_storage is not None}')

asyncio.run(check())
"
```

## 故障排除

### Neo4j 启动失败

```bash
# 检查日志
tail -f /tmp/neo4j.stderr.log

# 检查 Java 版本
$JAVA_HOME/bin/java -version

# 手动启动调试
NEO4J_HOME/bin/neo4j console
```

### 连接被拒绝

```bash
# 检查端口
lsof -i :7687
lsof -i :7474

# 检查服务状态
neo4j status
```
