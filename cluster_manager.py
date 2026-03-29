#!/usr/bin/env python3
"""
Agent 集群主控程序 - 统一入口点
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

# 添加脚本目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from start_agent import AgentLauncher
from monitor_agents import AgentMonitor
from select_agent import AgentSelector
from review_pr import CodeReviewer
from notify import NotificationService


class AgentCluster:
    """Agent 集群管理器"""
    
    def __init__(self, config_path: str = "./agent-config.yaml"):
        self.config_path = Path(config_path)
        self.base_dir = self.config_path.parent
        
        # 初始化组件
        self.launcher = AgentLauncher(config_path)
        self.monitor = AgentMonitor(config_path)
        self.selector = AgentSelector(config_path)
        self.reviewer = CodeReviewer(config_path)
        self.notifier = NotificationService(config_path)
        
        self.load_config()
    
    def load_config(self):
        """加载配置"""
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = {}
    
    def submit_task(self, description: str, 
                   preferred_agent: Optional[str] = None,
                   base_branch: str = "main") -> Dict[str, Any]:
        """提交新任务"""
        print(f"\n{'='*60}")
        print(f"📋 提交新任务")
        print(f"{'='*60}")
        
        # 1. 选择 Agent
        agent, analysis = self.selector.select_agent(description, preferred_agent)
        print(f"\n✅ 选择 Agent: {agent}")
        print(f"   置信度: {analysis.confidence:.1%}")
        print(f"   推理: {analysis.reasoning}")
        
        # 2. 生成任务 ID
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        task_id = f"task-{timestamp}-{description[:20].replace(' ', '-')}"
        
        # 3. 启动 Agent
        print(f"\n🚀 启动 Agent...")
        task_record = self.launcher.launch(
            task_id=task_id,
            description=description,
            agent_type=agent,
            base_branch=base_branch
        )
        
        # 4. 发送通知
        self.notifier.notify_agent_started(
            agent=agent,
            task_id=task_id,
            description=description
        )
        
        return task_record
    
    def check_status(self) -> Dict[str, Any]:
        """检查所有任务状态"""
        print(f"\n{'='*60}")
        print(f"📊 任务状态检查")
        print(f"{'='*60}\n")
        
        results = self.monitor.monitor_all()
        
        # 统计
        stats = {
            "total": len(results),
            "running": sum(1 for r in results if r.get("status") == "running"),
            "ready_for_review": sum(1 for r in results if r.get("ready_for_review")),
            "needs_retry": sum(1 for r in results if r.get("needs_retry"))
        }
        
        print(f"\n统计:")
        print(f"  - 总任务数: {stats['total']}")
        print(f"  - 运行中: {stats['running']}")
        print(f"  - 准备审查: {stats['ready_for_review']}")
        print(f"  - 需要重试: {stats['needs_retry']}")
        
        return {"stats": stats, "results": results}
    
    def review_pr(self, pr_number: int, reviewers: list = None) -> Dict[str, Any]:
        """审查 PR"""
        print(f"\n{'='*60}")
        print(f"🔍 审查 PR #{pr_number}")
        print(f"{'='*60}")
        
        results = self.reviewer.review_pr(pr_number, reviewers)
        
        all_approved = all(r.approved for r in results.values())
        
        return {
            "pr_number": pr_number,
            "all_approved": all_approved,
            "reviewers": list(results.keys())
        }
    
    def get_dashboard(self) -> str:
        """获取仪表盘"""
        tasks = self.monitor.get_all_tasks()
        
        lines = [
            "# Agent 集群仪表盘",
            f"\n更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
            "## 任务概览\n",
            "| 任务 ID | Agent | 状态 | 描述 |",
            "|---------|-------|------|------|"
        ]
        
        for task in tasks:
            lines.append(
                f"| {task['id'][:30]} | {task.get('agent', 'N/A')} | "
                f"{task.get('status', 'unknown')} | {task.get('description', '')[:50]} |"
            )
        
        return "\n".join(lines)
    
    def run_daemon(self, interval_minutes: int = 10):
        """以守护进程模式运行"""
        import time
        
        print(f"\n🤖 Agent 集群守护进程启动")
        print(f"   检查间隔: {interval_minutes} 分钟")
        print(f"   按 Ctrl+C 停止\n")
        
        try:
            while True:
                self.check_status()
                
                # 检查是否需要重试的任务
                tasks = self.monitor.get_all_tasks()
                for task in tasks:
                    if task.get("status") == "needs_retry":
                        retries = task.get("retries", 0)
                        max_retries = task.get("maxRetries", 3)
                        
                        if retries < max_retries:
                            print(f"\n⚠️  重试任务: {task['id']}")
                            # 重新启动 Agent
                            self.launcher.launch(
                                task_id=task['id'],
                                description=task.get('description'),
                                agent_type=task.get('agent'),
                                base_branch="main"
                            )
                            
                            # 更新重试次数
                            self.monitor.update_task_status(
                                task['id'],
                                {"retries": retries + 1, "status": "running"}
                            )
                
                print(f"\n⏰ 等待 {interval_minutes} 分钟...\n")
                time.sleep(interval_minutes * 60)
                
        except KeyboardInterrupt:
            print("\n\n👋 守护进程已停止")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Agent 集群管理器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 提交新任务
  python cluster_manager.py submit "实现用户登录功能" --agent codex
  
  # 检查状态
  python cluster_manager.py status
  
  # 审查 PR
  python cluster_manager.py review --pr 123
  
  # 启动守护进程
  python cluster_manager.py daemon --interval 10
  
  # 查看仪表盘
  python cluster_manager.py dashboard
"""
    )
    
    parser.add_argument("command", 
                       choices=["submit", "status", "review", "daemon", "dashboard"],
                       help="命令")
    parser.add_argument("--config", default="./agent-config.yaml", help="配置文件路径")
    parser.add_argument("--description", help="任务描述")
    parser.add_argument("--agent", help="指定 Agent")
    parser.add_argument("--pr", type=int, help="PR 编号")
    parser.add_argument("--interval", type=int, default=10, help="检查间隔（分钟）")
    parser.add_argument("--base-branch", default="main", help="基础分支")
    
    args = parser.parse_args()
    
    # 切换到配置文件所在目录
    config_dir = Path(args.config).parent
    if config_dir.exists():
        os.chdir(config_dir)
    
    cluster = AgentCluster(args.config)
    
    if args.command == "submit":
        if not args.description:
            print("❌ 请提供任务描述: --description")
            sys.exit(1)
        
        result = cluster.submit_task(
            description=args.description,
            preferred_agent=args.agent,
            base_branch=args.base_branch
        )
        print("\n" + json.dumps(result, indent=2, ensure_ascii=False))
    
    elif args.command == "status":
        result = cluster.check_status()
        print("\n" + json.dumps(result, indent=2, ensure_ascii=False))
    
    elif args.command == "review":
        if not args.pr:
            print("❌ 请提供 PR 编号: --pr")
            sys.exit(1)
        
        result = cluster.review_pr(args.pr)
        print("\n" + json.dumps(result, indent=2, ensure_ascii=False))
    
    elif args.command == "daemon":
        cluster.run_daemon(args.interval)
    
    elif args.command == "dashboard":
        print(cluster.get_dashboard())


if __name__ == "__main__":
    main()
