#!/bin/bash
#
# Pre-commit Hook 测试脚本
# 测试各种敏感信息检测功能
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🧪 测试 Pre-commit Hook"
echo "========================"

# 检查 hook 是否存在
if [ ! -f ".git/hooks/pre-commit" ]; then
    echo -e "${RED}❌ Pre-commit hook 不存在！${NC}"
    echo "   请先运行安装脚本。"
    exit 1
fi

# 检查 hook 是否可执行
if [ ! -x ".git/hooks/pre-commit" ]; then
    echo -e "${RED}❌ Pre-commit hook 不可执行！${NC}"
    echo "   运行: chmod +x .git/hooks/pre-commit"
    exit 1
fi

echo -e "${GREEN}✅ Pre-commit hook 已安装${NC}"
echo ""

# 创建测试分支
TEST_BRANCH="test-pre-commit-hook-$(date +%s)"
git checkout -b "$TEST_BRANCH" 2>/dev/null || true

echo "📝 测试各种敏感信息检测..."
echo ""

# 测试函数
test_detection() {
    local test_name="$1"
    local test_content="$2"
    local test_file="test_secret.txt"
    
    echo -n "测试: $test_name ... "
    
    # 写入测试内容
    echo "$test_content" > "$test_file"
    git add "$test_file"
    
    # 尝试提交（应该失败）
    if git commit -m "Test: $test_name" --no-verify 2>/dev/null; then
        echo -e "${RED}❌ 失败（应该被阻止但通过了）${NC}"
        git reset HEAD~1 --soft
        rm "$test_file"
        return 1
    else
        # 手动运行 hook 检查
        if .git/hooks/pre-commit 2>&1 | grep -q "检测到"; then
            echo -e "${GREEN}✅ 通过（成功检测）${NC}"
            git reset HEAD
            rm "$test_file"
            return 0
        else
            echo -e "${YELLOW}⚠️  未检测到（可能是误判）${NC}"
            git reset HEAD
            rm "$test_file"
            return 1
        fi
    fi
}

# 运行测试
passed=0
failed=0

# 1. OpenRouter API Key
if test_detection "OpenRouter API Key" "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"; then
    passed=$((passed + 1))
else
    failed=$((failed + 1))
fi

# 2. Anthropic API Key
if test_detection "Anthropic API Key" "sk-ant-api03-AbCdEfGhIjKlMnOpQrStUvWxYz0123456789AbCdEfGhIjKlMnOpQrStUvWxYz0123456789AbCdEfGhIjKlMnOpQr"; then
    passed=$((passed + 1))
else
    failed=$((failed + 1))
fi

# 3. OpenAI API Key
if test_detection "OpenAI API Key" "sk-AbCdEfGhIjKlMnOpQrStUvWxYz0123456789AbCdEfGh"; then
    passed=$((passed + 1))
else
    failed=$((failed + 1))
fi

# 4. 通用密码
if test_detection "通用密码" "password = \"mysecretpassword123\""; then
    passed=$((passed + 1))
else
    failed=$((failed + 1))
fi

# 5. JWT Token
if test_detection "JWT Token" "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"; then
    passed=$((passed + 1))
else
    failed=$((failed + 1))
fi

# 6. AWS Access Key
if test_detection "AWS Access Key" "AKIAIOSFODNN7EXAMPLE"; then
    passed=$((passed + 1))
else
    failed=$((failed + 1))
fi

# 7. 数据库连接字符串
if test_detection "数据库连接字符串" "postgresql://user:password@localhost:5432/dbname"; then
    passed=$((passed + 1))
else
    failed=$((failed + 1))
fi

# 测试正常提交（不包含敏感信息）
echo ""
echo -n "测试: 正常提交（无敏感信息） ... "
echo "This is a safe file" > test_safe.txt
git add test_safe.txt

if .git/hooks/pre-commit > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 通过${NC}"
    passed=$((passed + 1))
    git reset HEAD
    rm test_safe.txt
else
    echo -e "${RED}❌ 失败（正常文件被阻止）${NC}"
    failed=$((failed + 1))
    git reset HEAD
    rm test_safe.txt
fi

# 清理测试分支
git checkout master 2>/dev/null || git checkout main 2>/dev/null
git branch -D "$TEST_BRANCH" 2>/dev/null

# 结果统计
echo ""
echo "========================"
echo "测试结果："
echo -e "${GREEN}✅ 通过: $passed${NC}"
if [ $failed -gt 0 ]; then
    echo -e "${RED}❌ 失败: $failed${NC}"
fi
echo "========================"

if [ $failed -eq 0 ]; then
    echo -e "${GREEN}🎉 所有测试通过！Pre-commit hook 工作正常。${NC}"
    exit 0
else
    echo -e "${RED}⚠️  部分测试失败，请检查 hook 配置。${NC}"
    exit 1
fi
