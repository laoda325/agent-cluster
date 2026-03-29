#!/usr/bin/env python3
"""
示例工作流 - 展示如何使用 Agent 集群系统
"""

import sys
from pathlib import Path

# 添加模块路径
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

from cluster_manager import AgentCluster


def example_workflow():
    """示例工作流"""
    
    print("""
╔═══════════════════════════════════════════════════════════╗
║           Agent 集群系统 - 示例工作流                       ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    # 初始化集群管理器
    cluster = AgentCluster("./agent-config.yaml")
    
    # ========== 场景 1: 提交新任务 ==========
    print("\n📌 场景 1: 提交新任务")
    print("-" * 60)
    
    description = "实现用户登录功能，包括邮箱验证和密码重置"
    
    print(f"任务描述: {description}")
    print("\n正在选择最佳 Agent...")
    
    task = cluster.submit_task(
        description=description,
        preferred_agent=None,  # 自动选择
        base_branch="main"
    )
    
    print(f"\n✅ 任务已提交:")
    print(f"   任务 ID: {task.get('id')}")
    print(f"   Agent: {task.get('agent')}")
    print(f"   状态: {task.get('status')}")
    
    # ========== 场景 2: 检查任务状态 ==========
    print("\n\n📌 场景 2: 检查任务状态")
    print("-" * 60)
    
    status = cluster.check_status()
    
    print(f"\n统计信息:")
    print(f"  - 总任务数: {status['stats']['total']}")
    print(f"  - 运行中: {status['stats']['running']}")
    print(f"  - 准备审查: {status['stats']['ready_for_review']}")
    print(f"  - 需要重试: {status['stats']['needs_retry']}")
    
    # ========== 场景 3: Agent 选择策略 ==========
    print("\n\n📌 场景 3: Agent 选择策略")
    print("-" * 60)
    
    test_descriptions = [
        "修复数据库连接超时的Bug",
        "优化登录页面的UI样式",
        "设计新的用户仪表盘原型",
        "重构用户认证逻辑",
        "添加一个按钮组件"
    ]
    
    for desc in test_descriptions:
        agent, analysis = cluster.selector.select_agent(desc)
        print(f"\n描述: {desc[:30]}...")
        print(f"  → 选择: {agent.upper()}")
        print(f"  → 置信度: {analysis.confidence:.1%}")
        print(f"  → 任务类型: {analysis.task_type}")
    
    # ========== 场景 4: 查看仪表盘 ==========
    print("\n\n📌 场景 4: 查看仪表盘")
    print("-" * 60)
    
    dashboard = cluster.get_dashboard()
    print(dashboard)
    
    # ========== 场景 5: 模拟 PR 审查 ==========
    print("\n\n📌 场景 5: PR 审查流程")
    print("-" * 60)
    
    print("\n假设 PR #123 已创建，开始审查...")
    print("（注意：实际运行需要配置 API 密钥）")
    
    # 取消注释以实际运行
    # result = cluster.review_pr(123, reviewers=["codex", "gemini"])
    # print(f"\n审查结果: {result}")
    
    print("\n" + "="*60)
    print("✅ 示例工作流完成")
    print("="*60)


def quick_start():
    """快速启动指南"""
    
    print("""
╔═══════════════════════════════════════════════════════════╗
║              Agent 集群系统 - 快速启动                       ║
╚═══════════════════════════════════════════════════════════╝

📝 快速开始步骤:

1. 安装依赖:
   pip install pyyaml requests

2. 配置通知 (可选):
   编辑 agent-config.yaml，填写 Telegram/Discord 配置

3. 提交第一个任务:
   python cluster_manager.py submit "实现用户登录功能"

4. 查看状态:
   python cluster_manager.py status

5. 启动守护进程:
   python cluster_manager.py daemon

📚 常用命令:

   提交任务:     python cluster_manager.py submit "描述"
   查看状态:     python cluster_manager.py status
   审查PR:       python cluster_manager.py review --pr 123
   查看仪表盘:   python cluster_manager.py dashboard
   启动守护进程: python cluster_manager.py daemon

🔧 配置文件: agent-config.yaml
📁 任务记录:   tasks/
📝 文档:       README.md

祝使用愉快！ 🎉
    """)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Agent 集群示例")
    parser.add_argument("--demo", action="store_true", help="运行示例工作流")
    parser.add_argument("--guide", action="store_true", help="显示快速启动指南")
    
    args = parser.parse_args()
    
    if args.demo:
        example_workflow()
    elif args.guide:
        quick_start()
    else:
        quick_start()
