#!/bin/bash
#
# Git Hooks 安装脚本
# 在克隆仓库后运行此脚本以设置安全检查
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}TokenDance Git Hooks 安装${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# 检查是否在 Git 仓库中
if [ ! -d ".git" ]; then
    echo "❌ 错误：当前目录不是 Git 仓库"
    exit 1
fi

# 1. 安装 pre-commit hook
echo "📦 安装 Pre-commit hook..."
HOOKS_DIR=".git/hooks"
mkdir -p "$HOOKS_DIR"

# Pre-commit hook 源文件路径
if [ -f "$HOOKS_DIR/pre-commit" ]; then
    echo -e "${YELLOW}⚠️  Pre-commit hook 已存在，备份到 pre-commit.backup${NC}"
    cp "$HOOKS_DIR/pre-commit" "$HOOKS_DIR/pre-commit.backup"
fi

# 创建 pre-commit hook（内联内容）
cat > "$HOOKS_DIR/pre-commit" << 'HOOK_EOF'
#!/bin/bash
#
# Git Pre-commit Hook - 防止敏感信息泄露
# TokenDance Project
#
# 自动检测并阻止提交包含 API Keys、密码等敏感信息的文件
#

# 颜色定义
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检测到的问题数量
issues_found=0

echo "🔍 正在检查敏感信息..."

# 获取待提交的文件
files=$(git diff --cached --name-only --diff-filter=ACM)

# 1. 检查 OpenRouter API Keys
if git diff --cached | grep -E "sk-or-v1-[a-zA-Z0-9]{64}"; then
    echo -e "${RED}❌ 检测到 OpenRouter API Key 泄露！${NC}"
    echo "   请移除明文 API Key 并使用环境变量。"
    echo "   参考: docs/security/API-Key-Management.md"
    issues_found=$((issues_found + 1))
fi

# 2. 检查 Anthropic API Keys
if git diff --cached | grep -E "sk-ant-api[0-9]{2}-[a-zA-Z0-9_-]{95,}"; then
    echo -e "${RED}❌ 检测到 Anthropic API Key 泄露！${NC}"
    echo "   请使用环境变量: ANTHROPIC_API_KEY"
    issues_found=$((issues_found + 1))
fi

# 3. 检查 OpenAI API Keys
if git diff --cached | grep -E "sk-[a-zA-Z0-9]{48}"; then
    echo -e "${RED}❌ 检测到 OpenAI API Key 泄露！${NC}"
    echo "   请使用环境变量: OPENAI_API_KEY"
    issues_found=$((issues_found + 1))
fi

# 4. 检查通用密钥模式
if git diff --cached | grep -iE "(password|passwd|pwd|secret|token|api_key|apikey)\s*[=:]\s*['\"][^'\"]{8,}['\"]"; then
    echo -e "${RED}❌ 检测到可能的密码/密钥泄露！${NC}"
    echo "   请检查是否有硬编码的敏感信息。"
    issues_found=$((issues_found + 1))
fi

# 5. 检查 JWT Tokens
if git diff --cached | grep -E "eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}"; then
    echo -e "${RED}❌ 检测到 JWT Token 泄露！${NC}"
    issues_found=$((issues_found + 1))
fi

# 6. 检查 AWS Keys
if git diff --cached | grep -E "AKIA[0-9A-Z]{16}"; then
    echo -e "${RED}❌ 检测到 AWS Access Key 泄露！${NC}"
    issues_found=$((issues_found + 1))
fi

# 7. 检查 .env 文件（不应该被提交）
for file in $files; do
    if [[ "$file" == ".env" ]] || [[ "$file" == *".env.local" ]] || [[ "$file" == *".env.production" ]]; then
        echo -e "${RED}❌ 检测到 .env 文件！${NC}"
        echo "   文件: $file"
        echo "   .env 文件不应该被提交到 Git。"
        echo "   请添加到 .gitignore 并使用 .env.example 作为模板。"
        issues_found=$((issues_found + 1))
    fi
done

# 8. 检查私钥文件
if git diff --cached | grep -E "BEGIN (RSA |DSA |EC |OPENSSH )?PRIVATE KEY"; then
    echo -e "${RED}❌ 检测到私钥文件！${NC}"
    echo "   私钥不应该被提交到 Git。"
    issues_found=$((issues_found + 1))
fi

# 9. 检查数据库连接字符串
if git diff --cached | grep -iE "(mysql|postgresql|mongodb|redis)://[^@]+:[^@]+@"; then
    echo -e "${RED}❌ 检测到数据库连接字符串（含密码）！${NC}"
    echo "   请使用环境变量管理数据库凭证。"
    issues_found=$((issues_found + 1))
fi

# 10. 警告：大文件检查
for file in $files; do
    if [ -f "$file" ]; then
        file_size=$(wc -c < "$file" | tr -d ' ')
        # 警告超过 1MB 的文件
        if [ "$file_size" -gt 1048576 ]; then
            echo -e "${YELLOW}⚠️  大文件警告: $file ($(numfmt --to=iec-i --suffix=B $file_size 2>/dev/null || echo "${file_size} bytes"))${NC}"
            echo "   考虑使用 Git LFS 管理大文件。"
        fi
    fi
done

# 结果判断
if [ $issues_found -gt 0 ]; then
    echo ""
    echo -e "${RED}================================${NC}"
    echo -e "${RED}提交被阻止！发现 $issues_found 个安全问题。${NC}"
    echo -e "${RED}================================${NC}"
    echo ""
    echo "解决方案："
    echo "1. 移除敏感信息，使用环境变量替代"
    echo "2. 如果已泄露，立即撤销对应的 API Key"
    echo "3. 参考: docs/security/API-Key-Management.md"
    echo ""
    echo "如需跳过检查（不推荐），使用: git commit --no-verify"
    exit 1
fi

echo "✅ 安全检查通过！"
exit 0
HOOK_EOF

# 设置执行权限
chmod +x "$HOOKS_DIR/pre-commit"

echo -e "${GREEN}✅ Pre-commit hook 安装成功${NC}"
echo ""

# 2. 更新 .gitignore（确保 .env 文件不会被提交）
echo "📝 检查 .gitignore..."
GITIGNORE_FILE=".gitignore"

# 需要添加的忽略规则
IGNORE_PATTERNS=(
    ".env"
    ".env.local"
    ".env.*.local"
    ".env.production"
    "*.pem"
    "*.key"
    "*.p12"
    "*.pfx"
)

for pattern in "${IGNORE_PATTERNS[@]}"; do
    if ! grep -q "^$pattern$" "$GITIGNORE_FILE" 2>/dev/null; then
        echo "$pattern" >> "$GITIGNORE_FILE"
        echo "  添加: $pattern"
    fi
done

echo -e "${GREEN}✅ .gitignore 更新完成${NC}"
echo ""

# 3. 测试 hook
echo "🧪 测试 Pre-commit hook..."
if [ -x "$HOOKS_DIR/pre-commit" ]; then
    echo -e "${GREEN}✅ Hook 可执行${NC}"
else
    echo -e "${YELLOW}⚠️  Hook 可能无法执行${NC}"
fi

# 4. 显示使用说明
echo ""
echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}安装完成！${NC}"
echo -e "${BLUE}================================${NC}"
echo ""
echo "📖 使用说明："
echo ""
echo "1. Pre-commit hook 已激活"
echo "   - 每次 git commit 时会自动检查敏感信息"
echo "   - 如检测到问题，提交会被阻止"
echo ""
echo "2. 配置环境变量"
echo "   - 复制 backend/.env.example 到 backend/.env"
echo "   - 填入你的 API Keys（永远不要提交 .env 文件）"
echo ""
echo "3. 运行测试"
echo "   bash scripts/test_pre_commit_hook.sh"
echo ""
echo "4. 参考文档"
echo "   - 安全指南: docs/security/API-Key-Management.md"
echo "   - 集成文档: docs/integration/OpenRouter-Integration.md"
echo ""
echo -e "${GREEN}🎉 开始安全开发吧！${NC}"
