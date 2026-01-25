#!/bin/bash
# =============================================================================
# Neo4j 安装和配置脚本 (macOS)
#
# 功能:
# - 安装 Neo4j Community Edition
# - 配置开机自启动 (launchd)
# - 设置初始密码
#
# 使用方法:
#   chmod +x scripts/setup-neo4j.sh
#   ./scripts/setup-neo4j.sh
#
# 环境变量:
#   NEO4J_VERSION   - Neo4j 版本 (默认: 5.26.0)
#   NEO4J_PASSWORD  - 初始密码 (默认: tokendance)
#   NEO4J_HOME      - 安装目录 (默认: ~/opt/neo4j)
# =============================================================================

set -e

# 配置
NEO4J_VERSION="${NEO4J_VERSION:-5.26.0}"
NEO4J_PASSWORD="${NEO4J_PASSWORD:-tokendance}"
NEO4J_HOME="${NEO4J_HOME:-$HOME/opt/neo4j}"
NEO4J_DATA="${NEO4J_DATA:-$HOME/.neo4j/data}"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查 Java 版本
check_java() {
    log_info "检查 Java 版本..."
    
    if ! command -v java &> /dev/null; then
        log_error "Java 未安装。请安装 Java 17+ (推荐 OpenJDK)"
        log_info "可以使用: brew install openjdk@17"
        exit 1
    fi
    
    JAVA_VERSION=$(java -version 2>&1 | head -1 | cut -d'"' -f2 | cut -d'.' -f1)
    
    if [ "$JAVA_VERSION" -lt 17 ]; then
        log_error "Java 版本太低 (当前: $JAVA_VERSION)。Neo4j 5.x 需要 Java 17+"
        log_info "可以使用: brew install openjdk@17"
        log_info "然后设置: export JAVA_HOME=\$(/usr/libexec/java_home -v 17)"
        exit 1
    fi
    
    log_info "Java 版本: $JAVA_VERSION ✓"
}

# 下载 Neo4j
download_neo4j() {
    log_info "下载 Neo4j Community Edition $NEO4J_VERSION..."
    
    DOWNLOAD_URL="https://neo4j.com/artifact.php?name=neo4j-community-${NEO4J_VERSION}-unix.tar.gz"
    DOWNLOAD_PATH="/tmp/neo4j-${NEO4J_VERSION}.tar.gz"
    
    # 注意: 官方下载可能需要登录，尝试备用源
    # 备用源: https://dist.neo4j.org/neo4j-community-${NEO4J_VERSION}-unix.tar.gz
    
    if [ -f "$DOWNLOAD_PATH" ]; then
        log_info "发现缓存文件: $DOWNLOAD_PATH"
    else
        log_info "尝试从官方下载..."
        if ! curl -L -o "$DOWNLOAD_PATH" "$DOWNLOAD_URL" --progress-bar --fail 2>/dev/null; then
            log_warn "官方下载失败，尝试备用源..."
            DOWNLOAD_URL="https://dist.neo4j.org/neo4j-community-${NEO4J_VERSION}-unix.tar.gz"
            if ! curl -L -o "$DOWNLOAD_PATH" "$DOWNLOAD_URL" --progress-bar --fail 2>/dev/null; then
                log_error "下载失败。请手动下载 Neo4j 并放置到: $DOWNLOAD_PATH"
                log_info "下载地址: https://neo4j.com/deployment-center/"
                exit 1
            fi
        fi
    fi
    
    # 验证下载文件
    if file "$DOWNLOAD_PATH" | grep -q "HTML"; then
        log_error "下载的文件是 HTML (可能需要登录)"
        log_info "请手动从 https://neo4j.com/deployment-center/ 下载"
        log_info "选择 Community Edition -> Linux/Mac Executable"
        log_info "下载后放置到: $DOWNLOAD_PATH"
        rm -f "$DOWNLOAD_PATH"
        exit 1
    fi
    
    log_info "下载完成 ✓"
}

# 安装 Neo4j
install_neo4j() {
    log_info "安装 Neo4j 到 $NEO4J_HOME..."
    
    # 创建目录
    mkdir -p "$(dirname $NEO4J_HOME)"
    mkdir -p "$NEO4J_DATA"
    
    # 解压
    DOWNLOAD_PATH="/tmp/neo4j-${NEO4J_VERSION}.tar.gz"
    tar -xzf "$DOWNLOAD_PATH" -C "$(dirname $NEO4J_HOME)"
    
    # 重命名为统一路径
    if [ -d "$NEO4J_HOME" ]; then
        log_warn "已存在安装目录，备份..."
        mv "$NEO4J_HOME" "${NEO4J_HOME}.bak.$(date +%Y%m%d%H%M%S)"
    fi
    mv "$(dirname $NEO4J_HOME)/neo4j-community-${NEO4J_VERSION}" "$NEO4J_HOME"
    
    log_info "安装完成 ✓"
}

# 配置 Neo4j
configure_neo4j() {
    log_info "配置 Neo4j..."
    
    CONFIG_FILE="$NEO4J_HOME/conf/neo4j.conf"
    
    # 备份原配置
    cp "$CONFIG_FILE" "${CONFIG_FILE}.bak"
    
    # 配置数据目录
    echo "" >> "$CONFIG_FILE"
    echo "# TokenDance 自定义配置" >> "$CONFIG_FILE"
    echo "server.directories.data=$NEO4J_DATA" >> "$CONFIG_FILE"
    
    # 允许本地连接
    echo "server.default_listen_address=127.0.0.1" >> "$CONFIG_FILE"
    
    # 启用 Bolt 协议
    echo "server.bolt.enabled=true" >> "$CONFIG_FILE"
    echo "server.bolt.listen_address=127.0.0.1:7687" >> "$CONFIG_FILE"
    
    # HTTP 接口
    echo "server.http.enabled=true" >> "$CONFIG_FILE"
    echo "server.http.listen_address=127.0.0.1:7474" >> "$CONFIG_FILE"
    
    # 内存配置 (适合开发环境)
    echo "server.memory.heap.initial_size=512m" >> "$CONFIG_FILE"
    echo "server.memory.heap.max_size=1G" >> "$CONFIG_FILE"
    
    log_info "配置完成 ✓"
}

# 设置初始密码
set_password() {
    log_info "设置初始密码..."
    
    # 首次启动需要设置密码
    "$NEO4J_HOME/bin/neo4j-admin" dbms set-initial-password "$NEO4J_PASSWORD" 2>/dev/null || true
    
    log_info "密码设置完成 ✓"
    log_info "用户名: neo4j"
    log_info "密码: $NEO4J_PASSWORD"
}

# 创建 launchd 配置 (开机自启动)
setup_launchd() {
    log_info "配置开机自启动 (launchd)..."
    
    PLIST_PATH="$HOME/Library/LaunchAgents/com.tokendance.neo4j.plist"
    
    # 创建 plist 文件
    cat > "$PLIST_PATH" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.tokendance.neo4j</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>${NEO4J_HOME}/bin/neo4j</string>
        <string>console</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>${NEO4J_HOME}</string>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>NEO4J_HOME</key>
        <string>${NEO4J_HOME}</string>
    </dict>
    
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
    launchctl unload "$PLIST_PATH" 2>/dev/null || true
    launchctl load "$PLIST_PATH"
    
    log_info "launchd 配置完成 ✓"
    log_info "服务将在开机时自动启动"
}

# 启动 Neo4j
start_neo4j() {
    log_info "启动 Neo4j..."
    
    # 使用 launchctl 启动
    launchctl start com.tokendance.neo4j
    
    # 等待启动
    log_info "等待 Neo4j 启动..."
    for i in {1..30}; do
        if curl -s http://localhost:7474 > /dev/null 2>&1; then
            log_info "Neo4j 已启动 ✓"
            log_info "Web 界面: http://localhost:7474"
            log_info "Bolt 端口: bolt://localhost:7687"
            return 0
        fi
        sleep 1
    done
    
    log_warn "Neo4j 启动可能需要更长时间，请检查日志:"
    log_info "  tail -f /tmp/neo4j.stdout.log"
}

# 更新 .env 文件
update_env() {
    log_info "更新 TokenDance 环境配置..."
    
    ENV_FILE="$(dirname $0)/../backend/.env"
    
    if [ -f "$ENV_FILE" ]; then
        # 检查是否已有 Neo4j 配置
        if grep -q "NEO4J_URI" "$ENV_FILE"; then
            log_info ".env 已包含 Neo4j 配置"
        else
            echo "" >> "$ENV_FILE"
            echo "# Neo4j Configuration" >> "$ENV_FILE"
            echo "NEO4J_URI=bolt://localhost:7687" >> "$ENV_FILE"
            echo "NEO4J_USER=neo4j" >> "$ENV_FILE"
            echo "NEO4J_PASSWORD=$NEO4J_PASSWORD" >> "$ENV_FILE"
            echo "CONTEXT_GRAPH_MODE=neo4j" >> "$ENV_FILE"
            log_info ".env 已更新 ✓"
        fi
    else
        log_warn ".env 文件不存在，请手动添加以下配置:"
        echo "NEO4J_URI=bolt://localhost:7687"
        echo "NEO4J_USER=neo4j"
        echo "NEO4J_PASSWORD=$NEO4J_PASSWORD"
        echo "CONTEXT_GRAPH_MODE=neo4j"
    fi
}

# 显示使用说明
show_usage() {
    echo ""
    echo "=========================================="
    echo "Neo4j 安装完成!"
    echo "=========================================="
    echo ""
    echo "访问方式:"
    echo "  - Web 界面: http://localhost:7474"
    echo "  - Bolt 协议: bolt://localhost:7687"
    echo "  - 用户名: neo4j"
    echo "  - 密码: $NEO4J_PASSWORD"
    echo ""
    echo "常用命令:"
    echo "  启动:   launchctl start com.tokendance.neo4j"
    echo "  停止:   launchctl stop com.tokendance.neo4j"
    echo "  状态:   launchctl list | grep neo4j"
    echo "  日志:   tail -f /tmp/neo4j.stdout.log"
    echo ""
    echo "TokenDance 配置:"
    echo "  - 内存模式: CONTEXT_GRAPH_MODE=memory (默认)"
    echo "  - Neo4j 模式: CONTEXT_GRAPH_MODE=neo4j"
    echo ""
}

# 卸载
uninstall() {
    log_info "卸载 Neo4j..."
    
    # 停止服务
    launchctl stop com.tokendance.neo4j 2>/dev/null || true
    launchctl unload "$HOME/Library/LaunchAgents/com.tokendance.neo4j.plist" 2>/dev/null || true
    
    # 删除文件
    rm -f "$HOME/Library/LaunchAgents/com.tokendance.neo4j.plist"
    rm -rf "$NEO4J_HOME"
    
    log_info "卸载完成 (数据目录保留在 $NEO4J_DATA)"
}

# 主函数
main() {
    case "${1:-install}" in
        install)
            echo "=========================================="
            echo "Neo4j 安装脚本 (TokenDance)"
            echo "=========================================="
            
            check_java
            download_neo4j
            install_neo4j
            configure_neo4j
            set_password
            setup_launchd
            start_neo4j
            update_env
            show_usage
            ;;
        uninstall)
            uninstall
            ;;
        start)
            launchctl start com.tokendance.neo4j
            ;;
        stop)
            launchctl stop com.tokendance.neo4j
            ;;
        *)
            echo "用法: $0 {install|uninstall|start|stop}"
            exit 1
            ;;
    esac
}

main "$@"
