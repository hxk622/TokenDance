# TokenDance Scripts 目录

本目录包含项目的各种实用脚本。

## Git Security Hooks

### 快速开始

**新成员克隆仓库后首先运行：**

```bash
# 安装 Git hooks
bash scripts/setup_git_hooks.sh
```

这将：
- ✅ 安装 pre-commit hook（防止密钥泄露）
- ✅ 更新 .gitignore（防止 .env 文件被提交）
- ✅ 验证安装是否成功

### 脚本说明

#### 1. `setup_git_hooks.sh` - 安装脚本

**用途**：为项目设置 Git hooks，防止敏感信息泄露

**运行时机**：
- 首次克隆仓库后
- Git hooks 被意外删除后
- 更新到新版本的 hooks

**功能**：
- 安装 pre-commit hook
- 自动更新 .gitignore
- 验证安装状态

```bash
bash scripts/setup_git_hooks.sh
```

#### 2. `test_pre_commit_hook.sh` - 测试脚本

**用途**：验证 pre-commit hook 是否正常工作

**运行时机**：
- 安装 hooks 后验证
- 修改 hooks 后测试
- 定期检查（推荐每月一次）

**测试内容**：
- OpenRouter API Keys
- Anthropic API Keys
- OpenAI API Keys
- 通用密码模式
- JWT Tokens
- AWS Access Keys
- 数据库连接字符串
- 正常文件提交（不应被阻止）

```bash
bash scripts/test_pre_commit_hook.sh
```

**预期输出**：

```
🧪 测试 Pre-commit Hook
========================
✅ Pre-commit hook 已安装

📝 测试各种敏感信息检测...

测试: OpenRouter API Key ... ✅ 通过（成功检测）
测试: Anthropic API Key ... ✅ 通过（成功检测）
测试: OpenAI API Key ... ✅ 通过（成功检测）
测试: 通用密码 ... ✅ 通过（成功检测）
测试: JWT Token ... ✅ 通过（成功检测）
测试: AWS Access Key ... ✅ 通过（成功检测）
测试: 数据库连接字符串 ... ✅ 通过（成功检测）

测试: 正常提交（无敏感信息） ... ✅ 通过

========================
测试结果：
✅ 通过: 8
========================
🎉 所有测试通过！Pre-commit hook 工作正常。
```

### Pre-commit Hook 检测规则

Hook 会自动检测以下类型的敏感信息：

| 类型 | 模式 | 示例 |
|------|------|------|
| OpenRouter API Key | `sk-or-v1-[a-zA-Z0-9]{64}` | `sk-or-v1-abc...` |
| Anthropic API Key | `sk-ant-api[0-9]{2}-[a-zA-Z0-9_-]{95,}` | `sk-ant-api03-abc...` |
| OpenAI API Key | `sk-[a-zA-Z0-9]{48}` | `sk-AbCdEf...` |
| 通用密钥 | `(password\|secret\|token).*=.*"[^"]{8,}"` | `password = "secret123"` |
| JWT Token | `eyJ[a-zA-Z0-9_-]{10,}\.` | `eyJhbGciOi...` |
| AWS Access Key | `AKIA[0-9A-Z]{16}` | `AKIAIOSFODNN7EXAMPLE` |
| 私钥文件 | `BEGIN.*PRIVATE KEY` | `-----BEGIN RSA PRIVATE KEY-----` |
| 数据库连接串 | `(mysql\|postgresql)://.*:.*@` | `postgresql://user:pass@host` |
| .env 文件 | 文件名匹配 | `.env`, `.env.local` |
| 大文件 | 文件大小 > 1MB | 触发警告 |

### 工作流程

#### 正常提交（无敏感信息）

```bash
$ git add file.py
$ git commit -m "Add feature"
🔍 正在检查敏感信息...
✅ 安全检查通过！
[master abc1234] Add feature
```

#### 检测到敏感信息

```bash
$ git add config.py
$ git commit -m "Add config"
🔍 正在检查敏感信息...
❌ 检测到 OpenRouter API Key 泄露！
   请移除明文 API Key 并使用环境变量。
   参考: docs/security/API-Key-Management.md

================================
提交被阻止！发现 1 个安全问题。
================================

解决方案：
1. 移除敏感信息，使用环境变量替代
2. 如果已泄露，立即撤销对应的 API Key
3. 参考: docs/security/API-Key-Management.md

如需跳过检查（不推荐），使用: git commit --no-verify
```

### 跳过 Hook（仅限特殊情况）

**⚠️ 警告：仅在以下情况使用 `--no-verify`：**
- 你明确知道文件不包含敏感信息
- Hook 误判（请报告给团队）
- 紧急修复（事后必须补充正确提交）

```bash
git commit --no-verify -m "Urgent fix"
```

### 常见问题

#### Q: Hook 没有运行？

**检查**：
```bash
# 1. 检查 hook 是否存在
ls -la .git/hooks/pre-commit

# 2. 检查是否可执行
[ -x .git/hooks/pre-commit ] && echo "可执行" || echo "不可执行"

# 3. 重新安装
bash scripts/setup_git_hooks.sh
```

#### Q: Hook 误判怎么办？

1. 确认是否真的是误判
2. 如果确认误判，使用 `--no-verify` 跳过
3. 报告给团队，改进检测规则

#### Q: 如何自定义检测规则？

编辑 `.git/hooks/pre-commit` 文件，添加或修改正则表达式。

建议：将自定义规则贡献回项目，让所有人受益。

#### Q: 团队成员没有安装 hook？

在 onboarding 文档中强调：
- 克隆仓库后必须运行 `bash scripts/setup_git_hooks.sh`
- CI/CD 可以添加检查，验证提交历史中没有密钥

### 最佳实践

1. **定期测试**
   ```bash
   # 每月运行一次
   bash scripts/test_pre_commit_hook.sh
   ```

2. **保持更新**
   ```bash
   # 拉取最新代码后重新安装
   git pull
   bash scripts/setup_git_hooks.sh
   ```

3. **团队协作**
   - 新成员入职时必须安装
   - 在 README 中提及
   - Code Review 时检查是否有误提交

4. **持续改进**
   - 发现新的密钥模式时更新规则
   - 分享误判案例
   - 定期回顾和优化

## 参考文档

- [API Key 安全管理指南](../docs/security/API-Key-Management.md)
- [OpenRouter 集成文档](../docs/integration/OpenRouter-Integration.md)
- [Git Hooks 官方文档](https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks)

## 贡献

发现 bug 或有改进建议？欢迎提交 PR 或 Issue！
