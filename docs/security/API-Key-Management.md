# API Key 安全管理指南

## ⚠️ 紧急提醒

**你在对话中提到的 OpenRouter API Key 已经泄露，必须立即采取行动！**

```
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
```

## 立即行动清单

### 1. 撤销泄露的 Key（最高优先级）

1. 访问 [OpenRouter Dashboard](https://openrouter.ai/keys)
2. 登录你的账户
3. 找到上述 API Key
4. 点击 **Revoke** 或 **Delete** 按钮
5. 确认撤销操作

### 2. 生成新的 API Key

1. 在 OpenRouter Dashboard 中
2. 点击 **Create New API Key**
3. 设置描述：`TokenDance Production`
4. **立即复制新 Key 并保存到安全位置**

### 3. 更新环境变量

```bash
# 不要在代码中硬编码！
# .env (本地开发)
OPENROUTER_API_KEY=sk-or-v1-NEW_KEY_HERE

# 生产环境：使用密钥管理服务
# AWS Secrets Manager / Azure Key Vault / Google Secret Manager
```

### 4. 检查历史记录

```bash
# 检查 Git 历史中是否有泄露
cd /path/to/TokenDance
git log -p --all -S "sk-or-v1" -- "*.py" "*.md" "*.env"

# 如果发现泄露，使用 git-filter-repo 清理历史
# 参考：https://github.com/newren/git-filter-repo
```

## 安全最佳实践

### ✅ 应该做的事

1. **使用环境变量**
   ```python
   import os
   api_key = os.getenv("OPENROUTER_API_KEY")
   ```

2. **使用 .env 文件（加入 .gitignore）**
   ```bash
   # .gitignore
   .env
   .env.local
   .env.*.local
   ```

3. **使用密钥管理服务**
   ```python
   # AWS Secrets Manager
   import boto3
   client = boto3.client('secretsmanager')
   response = client.get_secret_value(SecretId='openrouter-api-key')
   api_key = response['SecretString']
   ```

4. **定期轮换密钥**
   - 设置提醒：每 90 天轮换一次
   - 使用版本化管理（v1, v2, ...）

5. **限制 Key 权限**
   - 只授予必要的权限
   - 为不同环境使用不同的 Key

### ❌ 绝对不要做的事

1. **硬编码到代码中**
   ```python
   # ❌ 错误示例
   api_key = "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"
   ```

2. **提交到 Git**
   ```bash
   # ❌ 错误
   git add .env
   git commit -m "Add config"
   ```

3. **在对话/文档中明文展示**
   ```markdown
   # ❌ 错误
   My API Key: sk-or-v1-xxxxx
   
   # ✅ 正确
   My API Key: {{OPENROUTER_API_KEY}}  # 使用占位符
   ```

4. **通过 HTTP 传输（必须 HTTPS）**

5. **与他人分享**

## TokenDance 项目配置

### 开发环境

```bash
# 1. 复制示例配置
cp backend/.env.example backend/.env

# 2. 编辑 .env，填入新的 API Key
vim backend/.env
# OPENROUTER_API_KEY=sk-or-v1-NEW_KEY

# 3. 验证配置
cd backend
uv run python -c "import os; print('API Key:', os.getenv('OPENROUTER_API_KEY')[:20] + '...')"
```

### 生产环境

**推荐方案：使用 Docker Secrets 或 Kubernetes Secrets**

```yaml
# docker-compose.yml
services:
  backend:
    environment:
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
    secrets:
      - openrouter_key

secrets:
  openrouter_key:
    external: true
```

```bash
# 创建 Docker Secret
echo "sk-or-v1-NEW_KEY" | docker secret create openrouter_key -
```

## 检测泄露

### 1. 使用 Git Pre-commit Hook

```bash
# .git/hooks/pre-commit
#!/bin/bash
if git diff --cached | grep -E "sk-or-v1-[a-zA-Z0-9]{64}"; then
    echo "❌ 检测到 OpenRouter API Key 泄露！"
    echo "请移除 API Key 并使用环境变量。"
    exit 1
fi
```

### 2. 使用 GitHub Secret Scanning

GitHub 会自动扫描提交中的密钥，如果检测到泄露会发送警报。

### 3. 使用 git-secrets 工具

```bash
# 安装
brew install git-secrets  # macOS
apt-get install git-secrets  # Ubuntu

# 配置
cd /path/to/TokenDance
git secrets --install
git secrets --register-aws  # 默认包含 API Key 模式
git secrets --add 'sk-or-v1-[a-zA-Z0-9]{64}'
```

## 泄露响应流程

如果发现 API Key 泄露：

1. **立即撤销** (< 5 分钟)
2. **生成新 Key** (< 10 分钟)
3. **更新所有环境** (< 30 分钟)
4. **检查使用日志** - 查看是否有异常调用
5. **审查权限** - 确认泄露范围
6. **记录事件** - 文档化处理过程

## 监控与审计

### 1. 设置使用量告警

```python
# 集成到 TokenDance 监控系统
from app.monitoring import alert_if_anomaly

async def monitor_api_usage():
    usage = await get_openrouter_usage()
    if usage.daily_cost > THRESHOLD:
        alert_if_anomaly("OpenRouter 使用量异常")
```

### 2. 定期审计日志

```sql
-- 查询最近的 LLM 调用
SELECT 
    session_id,
    model,
    timestamp,
    cost_usd
FROM llm_audit_log
WHERE provider = 'openrouter'
ORDER BY timestamp DESC
LIMIT 100;
```

## 参考资料

- [OpenRouter Security](https://openrouter.ai/docs/security)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [GitHub Secret Scanning](https://docs.github.com/en/code-security/secret-scanning)
- [AWS Secrets Manager Best Practices](https://docs.aws.amazon.com/secretsmanager/latest/userguide/best-practices.html)

## 紧急联系

如有安全问题，请联系：
- 项目维护者：[GitHub Issues](https://github.com/your-repo/TokenDance/issues)
- OpenRouter 支持：support@openrouter.ai
