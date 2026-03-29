#!/usr/bin/env python3
"""
Agent 集群系统 - 安装脚本
"""

import os
import sys
from pathlib import Path


def check_python_version():
    """检查 Python 版本"""
    version = sys.version_info
    print(f"✓ Python 版本: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ 需要 Python 3.8 或更高版本")
        return False
    
    return True


def install_dependencies():
    """安装依赖"""
    print("\n📦 安装依赖...")
    
    dependencies = [
        "pyyaml",
        "requests"
    ]
    
    for dep in dependencies:
        print(f"  安装 {dep}...")
        os.system(f"pip install {dep}")
    
    print("✓ 依赖安装完成")


def create_directories():
    """创建必要目录"""
    print("\n📁 创建目录结构...")
    
    directories = [
        "tasks",
        "worktrees",
        "context"
    ]
    
    for dir_name in directories:
        dir_path = Path(dir_name)
        dir_path.mkdir(exist_ok=True)
        print(f"  ✓ {dir_name}/")
    
    print("✓ 目录创建完成")


def check_tools():
    """检查必要工具"""
    print("\n🔧 检查工具...")
    
    tools = {
        "git": "Git 版本控制",
        "gh": "GitHub CLI",
        "tmux": "终端复用器（可选）"
    }
    
    for tool, desc in tools.items():
        result = os.system(f"which {tool} 2>/dev/null" if os.name != "nt" 
                          else f"where {tool} >nul 2>&1")
        
        if result == 0:
            print(f"  ✓ {tool}: {desc}")
        else:
            if tool == "tmux":
                print(f"  ⚠ {tool}: {desc} (未安装，将使用后台进程)")
            else:
                print(f"  ❌ {tool}: {desc} (未安装)")


def create_default_config():
    """创建默认配置"""
    config_path = Path("agent-config.yaml")
    
    if config_path.exists():
        print("\n⚠️  配置文件已存在，跳过创建")
        return
    
    print("\n📝 创建默认配置...")
    
    default_config = """# Agent 集群配置文件
# 请根据实际情况修改

cluster:
  name: "AgentCluster"
  version: "1.0.0"
  max_concurrent_agents: 5
  max_retries: 3

agents:
  codex:
    enabled: true
    model: "gpt-5.3-codex"
    priority: 1
    description: "主力Agent - 后端逻辑、复杂bug、多文件重构"
    use_cases:
      - backend_logic
      - complex_bugs
      - multi_file_refactor
    weight: 0.9

  claude_code:
    enabled: true
    model: "claude-opus-4.5"
    priority: 2
    description: "速度型Agent - 前端工作、git操作"
    use_cases:
      - frontend_work
      - git_operations
      - quick_fixes
    weight: 0.7

  gemini:
    enabled: true
    model: "gemini-2.5-pro"
    priority: 3
    description: "设计师Agent - UI/UX设计"
    use_cases:
      - ui_design
      - design_specs
    weight: 0.5

reviewers:
  codex_reviewer:
    enabled: true
    model: "gpt-5.3-codex"
    focus: "边界情况、逻辑错误"
    trust_level: "high"

  gemini_reviewer:
    enabled: true
    model: "gemini-code-assist"
    focus: "安全问题、扩展性"
    trust_level: "medium"

monitoring:
  check_interval_minutes: 10
  max_idle_minutes: 120
  notify_on:
    - pr_ready
    - agent_failed

notifications:
  telegram:
    enabled: false
    bot_token: "YOUR_BOT_TOKEN"
    chat_id: "YOUR_CHAT_ID"
  
  discord:
    enabled: false
    webhook_url: ""

storage:
  tasks_dir: "./tasks"
  worktrees_base: "../worktrees"
  context_dir: "./context"

completion_criteria:
  pr_created: true
  branch_synced: true
  ci_passed: true
  codex_reviewer_passed: true
  gemini_reviewer_passed: true
  ui_screenshots: true
"""
    
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(default_config)
    
    print("✓ 配置文件已创建: agent-config.yaml")
    print("\n⚠️  请编辑配置文件，填写必要的信息")


def main():
    """主函数"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║         Agent 集群系统 - 安装向导                          ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    # 检查 Python 版本
    if not check_python_version():
        sys.exit(1)
    
    # 安装依赖
    install_dependencies()
    
    # 创建目录
    create_directories()
    
    # 检查工具
    check_tools()
    
    # 创建配置
    create_default_config()
    
    print("\n" + "="*60)
    print("✅ 安装完成！")
    print("="*60)
    
    print("""
📚 下一步:

1. 编辑配置文件:
   nano agent-config.yaml  # 或使用你喜欢的编辑器

2. 配置 Telegram/Discord 通知（可选）

3. 运行示例工作流:
   python example_workflow.py --demo

4. 提交第一个任务:
   python cluster_manager.py submit "你的任务描述"

5. 查看帮助:
   python cluster_manager.py --help

祝使用愉快！ 🎉
    """)


if __name__ == "__main__":
    main()
