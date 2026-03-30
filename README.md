# Agent 集群系统

基于 QClaw + Claude Code/Codex 的 AI Agent 集群系统，实现自动化开发工作流。

## 📋 系统架构

```
┌─────────────────────────────────────────────────────┐
│                   QClaw (编排层)                    │
│  ┌─────────────────────────────────────────────┐   │
│  │  • 持有业务上下文                              │   │
│  │  • 选择合适的 Agent                           │   │
│  │  • 监控任务进度                                │   │
│  │  • 自动重试失败任务                            │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│                  Agent 执行层                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │  Codex   │  │  Claude  │  │  Gemini  │         │
│  │ (主力)    │  │  (快速)   │  │ (设计)    │         │
│  └──────────┘  └──────────┘  └──────────┘         │
└─────────────────────────────────────────────────────┘
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install pyyaml requests
```

### 2. 配置

编辑 `agent-config.yaml`：

```yaml
# 配置 微信 通知
notifications:
  wechat:
    enabled: true
    webhook_url: "YOUR_WECHAT_WEBHOOK_URL"

# 配置 Agent
agents:
  codex:
    enabled: true
    model: "gpt-5.3-codex"
    cli_command_template: "codex --model {model} --cwd \"{worktree}\" --prompt-file \"{prompt_file}\""

  claude_code:
    enabled: true
    model: "claude-opus-4.5"
    cli_command_template: "claude-code --model {model} --cwd \"{worktree}\" --prompt-file \"{prompt_file}\""

  gemini:
    enabled: true
    model: "gemini-2.5-pro"
    cli_command_template: "gemini --model {model} --cwd \"{worktree}\" --prompt-file \"{prompt_file}\""
```

### 3. 提交任务

```bash
# 自动选择 Agent
python cluster_manager.py submit "实现用户登录功能"

# 指定 Agent
python cluster_manager.py submit "修复登录Bug" --agent codex

# 指定基础分支
python cluster_manager.py submit "新功能" --base-branch develop
```

### 4. 检查状态

```bash
# 查看所有任务状态
python cluster_manager.py status

# 查看仪表盘
python cluster_manager.py dashboard
```

### 5. 审查 PR

```bash
# 使用默认审查者
python cluster_manager.py review --pr 123

# 指定审查者
python cluster_manager.py review --pr 123 --reviewers codex gemini
```

### 6. 启动守护进程

```bash
# 每 10 分钟检查一次
python cluster_manager.py daemon --interval 10
```

## 📁 目录结构

```
agent-cluster/
├── agent-config.yaml          # 配置文件
├── cluster_manager.py          # 主控程序
├── scripts/
│   ├── start_agent.py          # Agent 启动器
│   ├── monitor_agents.py       # 监控器
│   ├── select_agent.py         # Agent 选择器
│   ├── review_pr.py            # PR 审查器
│   └── notify.py               # 通知服务
├── tasks/                      # 任务记录
└── README.md                   # 说明文档
```

## 🤖 Agent 选择策略

系统会根据任务描述自动选择最合适的 Agent：

| 任务类型 | 推荐 Agent | 原因 |
|---------|-----------|------|
| 后端逻辑、复杂Bug | Codex | 擅长跨代码库推理、逻辑错误 |
| 前端、快速迭代 | Claude Code | 速度快、权限问题少 |
| UI/UX 设计 | Gemini | 有设计审美 |

### 关键词权重

- **Codex**: backend, api, database, bug, refactor, security
- **Claude Code**: frontend, ui, component, style, quick, fix
- **Gemini**: design, ux, prototype, mockup, visual

## 📊 任务生命周期

```
提交任务 → 选择Agent → 创建worktree → 启动执行会话（tmux/后台进程）→ 执行任务
                                              ↓
                                        创建PR
                                              ↓
                                        CI检查
                                              ↓
                                    AI Review (3个审查者)
                                              ↓
                                      人工Review
                                              ↓
                                        合并PR
```

## ✅ 完成标准

PR 需要满足以下条件才算"完成"：

- ✅ PR 已创建
- ✅ 分支已同步到 main（无冲突）
- ✅ CI 通过（lint、类型检查、单元测试、E2E测试）
- ✅ Codex Reviewer 通过
- ✅ Gemini Reviewer 通过
- ✅ 如果有 UI 改动，必须包含截图

## 🔔 通知

支持 Wechat 和 Discord 通知：

- Agent 启动时
- PR 准备好审查时
- Agent 失败时
- PR 合并时

Windows 环境下会自动回退到后台进程模式，并通过任务心跳文件判断执行状态。

## 🔄 Ralph Loop（改进版）

系统会学习成功的模式：

1. 任务失败时，分析原因并调整 prompt
2. 成功的模式被记录
3. 时间越长，prompt 越精准

```python
# 动态调整示例
if failed:
    new_prompt = f"""
    停。客户要的是 X，不是 Y。
    这是他们在会议里的原话：'{customer_quote}'
    重点做配置复用，不要做新建流程。
    """
```

## ⚙️ 高级配置

### 最大并发 Agent 数

```yaml
cluster:
  max_concurrent_agents: 5
```

### 最大重试次数

```yaml
cluster:
  max_retries: 3
```

### 监控间隔

```yaml
monitoring:
  check_interval_minutes: 10
  min_runtime_minutes_before_retry: 5
```

## 📝 最佳实践

1. **清晰的描述**: 提供详细的任务描述，系统会据此选择最佳 Agent
2. **定期检查**: 运行守护进程自动监控任务状态
3. **及时审查**: 收到通知后尽快审查 PR
4. **学习改进**: 系统会记录成功模式，越用越智能

## 🔐 安全边界

- Agent 永远不会接触生产数据库
- Agent 只拿到完成任务所需的最小上下文
- 所有操作都在隔离的 worktree 中进行

## 📚 参考

- [OpenClaw 文档](https://docs.openclaw.ai)
- [Claude Code 文档](https://docs.anthropic.com)
- [Codex 文档](https://platform.openai.com)

## 📄 License

MIT
