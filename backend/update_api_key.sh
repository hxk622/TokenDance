#!/bin/bash
#
# OpenRouter API Key 更新脚本
# 帮助你安全地更新 API Key
#

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}OpenRouter API Key 更新向导${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# 检查当前 Key
if [ -f ".env" ]; then
    CURRENT_KEY=$(grep OPENROUTER_API_KEY .env | cut -d '=' -f2 | tr -d '"' | tr -d "'")
    
    if [ -n "$CURRENT_KEY" ]; then
        KEY_PREFIX="${CURRENT_KEY:0:15}"
        echo -e "当前 API Key 前缀: ${YELLOW}$KEY_PREFIX...${NC}"
        
        # 检查是否是泄露的旧 Key
        if [[ "$CURRENT_KEY" == *"a8c6845b268ad61c97e672a8e60e39e3f349adc71d76351097fcaa4ee865047e"* ]]; then
            echo -e "${RED}⚠️  警告：检测到泄露的旧 API Key！${NC}"
            echo ""
        fi
    else
        echo -e "${YELLOW}未找到 OPENROUTER_API_KEY 配置${NC}"
    fi
else
    echo -e "${YELLOW}未找到 .env 文件${NC}"
fi

echo ""
echo -e "${RED}================================${NC}"
echo -e "${RED}重要步骤${NC}"
echo -e "${RED}================================${NC}"
echo ""

# Step 1
echo -e "${YELLOW}Step 1: 撤销旧 Key（如果还没有）${NC}"
echo "1. 访问: https://openrouter.ai/keys"
echo "2. 登录你的账户"
echo "3. 找到旧 Key 并点击 'Revoke' 或 'Delete'"
echo ""
read -p "完成后按 Enter 继续..."
echo ""

# Step 2
echo -e "${YELLOW}Step 2: 生成新 Key${NC}"
echo "1. 在同一页面点击 'Create New API Key'"
echo "2. 设置描述: TokenDance Production"
echo "3. 复制新生成的 Key（格式：sk-or-v1-xxxxx）"
echo ""
read -p "完成后按 Enter 继续..."
echo ""

# Step 3
echo -e "${YELLOW}Step 3: 输入新 API Key${NC}"
echo -e "${BLUE}请粘贴新的 API Key:${NC}"
read -s NEW_API_KEY
echo ""

# 验证格式
if [[ ! "$NEW_API_KEY" =~ ^sk-or-v1- ]]; then
    echo -e "${RED}❌ 错误：API Key 格式不正确${NC}"
    echo "Key 应该以 sk-or-v1- 开头"
    exit 1
fi

# 验证长度
if [ ${#NEW_API_KEY} -lt 50 ]; then
    echo -e "${RED}❌ 错误：API Key 长度太短${NC}"
    exit 1
fi

# 确认不是旧 Key
if [[ "$NEW_API_KEY" == *"a8c6845b268ad61c97e672a8e60e39e3f349adc71d76351097fcaa4ee865047e"* ]]; then
    echo -e "${RED}❌ 错误：这是泄露的旧 Key！请生成新的 Key${NC}"
    exit 1
fi

echo -e "${GREEN}✅ API Key 格式验证通过${NC}"
echo ""

# 备份旧 .env
if [ -f ".env" ]; then
    cp .env .env.backup
    echo -e "${GREEN}✅ 已备份现有 .env 到 .env.backup${NC}"
fi

# 更新 .env
if [ -f ".env" ]; then
    # 如果 .env 存在，替换 OPENROUTER_API_KEY
    if grep -q "OPENROUTER_API_KEY" .env; then
        # macOS 和 Linux 兼容的 sed
        sed -i.tmp "s|OPENROUTER_API_KEY=.*|OPENROUTER_API_KEY=$NEW_API_KEY|" .env
        rm -f .env.tmp
        echo -e "${GREEN}✅ 已更新 .env 文件${NC}"
    else
        # 追加到文件末尾
        echo "" >> .env
        echo "# OpenRouter" >> .env
        echo "OPENROUTER_API_KEY=$NEW_API_KEY" >> .env
        echo -e "${GREEN}✅ 已添加到 .env 文件${NC}"
    fi
else
    # 创建新 .env
    cat > .env << EOF
# OpenRouter (统一 LLM 网关)
OPENROUTER_API_KEY=$NEW_API_KEY
OPENROUTER_MODEL=anthropic/claude-3-5-sonnet
OPENROUTER_SITE_URL=https://tokendance.ai
OPENROUTER_APP_NAME=TokenDance
EOF
    echo -e "${GREEN}✅ 已创建新 .env 文件${NC}"
fi

echo ""
echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Step 4: 测试新 Key${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# 运行测试
echo "运行连接测试..."
if uv run python test_openrouter_connection.py; then
    echo ""
    echo -e "${GREEN}================================${NC}"
    echo -e "${GREEN}🎉 成功！${NC}"
    echo -e "${GREEN}================================${NC}"
    echo ""
    echo "API Key 已更新并测试通过！"
    echo ""
    echo "下一步："
    echo "1. 删除备份文件: rm .env.backup"
    echo "2. 开始使用 OpenRouter"
else
    echo ""
    echo -e "${RED}================================${NC}"
    echo -e "${RED}测试失败${NC}"
    echo -e "${RED}================================${NC}"
    echo ""
    echo "可能的原因："
    echo "1. API Key 可能需要几分钟才能激活"
    echo "2. 网络连接问题"
    echo "3. OpenRouter 服务暂时不可用"
    echo ""
    echo "如需恢复旧配置: cp .env.backup .env"
fi
