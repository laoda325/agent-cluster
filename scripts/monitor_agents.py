#!/usr/bin/env python3
"""
Agent 监控器 - 定期检查所有 Agent 的状态
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml


class AgentMonitor:
    """Agent 监控器"""
    
    def __init__(self, config_path: str = "./agent-config.yaml"):
        self.config_path = Path(config_path)
        self.tasks_dir = Path("./tasks")
        self.load_config()
    
    def load_config(self):
        """加载配置"""
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = {}
    
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """获取所有任务记录"""
        tasks = []
        if not self.tasks_dir.exists():
            return tasks
        
        for task_file in self.tasks_dir.glob("*.json"):
            try:
                with open(task_file, 'r', encoding='utf-8') as f:
                    task = json.load(f)
                    tasks.append(task)
            except Exception as e:
                print(f"⚠️  读取任务文件失败 {task_file}: {e}")
        
        return tasks
    
    def check_tmux_session(self, session_name: str) -> bool:
        """检查 tmux 会话是否存活"""
        try:
            result = subprocess.run(
                ["tmux", "has-session", "-t", session_name],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def check_pr_exists(self, branch: str, repo: str = None) -> Optional[Dict]:
        """检查 PR 是否存在"""
        try:
            # 使用 gh 命令检查 PR
            result = subprocess.run(
                ["gh", "pr", "list", "--head", branch, "--json", "number,state,url,title"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and result.stdout.strip():
                prs = json.loads(result.stdout)
                if prs:
                    return prs[0]
        except Exception as e:
            print(f"⚠️  检查 PR 失败: {e}")
        
        return None
    
    def check_ci_status(self, branch: str) -> Dict[str, Any]:
        """检查 CI 状态"""
        try:
            # 使用 gh 命令检查 CI
            result = subprocess.run(
                ["gh", "run", "list", "--branch", branch, "--limit", "1", "--json", "status,conclusion"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and result.stdout.strip():
                runs = json.loads(result.stdout)
                if runs:
                    return {
                        "status": runs[0].get("status"),
                        "conclusion": runs[0].get("conclusion"),
                        "passed": runs[0].get("conclusion") == "success"
                    }
        except Exception as e:
            print(f"⚠️  检查 CI 失败: {e}")
        
        return {"status": "unknown", "conclusion": None, "passed": False}
    
    def check_reviewers_passed(self, pr_number: int) -> Dict[str, bool]:
        """检查 Code Review 状态"""
        reviewers = {
            "codex_reviewer": False,
            "gemini_reviewer": False,
            "claude_reviewer": False
        }
        
        try:
            # 获取 PR reviews
            result = subprocess.run(
                ["gh", "pr", "view", str(pr_number), "--json", "reviews"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                pr_data = json.loads(result.stdout)
                reviews = pr_data.get("reviews", [])
                
                for review in reviews:
                    reviewer = review.get("author", {}).get("login", "").lower()
                    state = review.get("state")
                    
                    if "codex" in reviewer and state == "APPROVED":
                        reviewers["codex_reviewer"] = True
                    elif "gemini" in reviewer and state == "APPROVED":
                        reviewers["gemini_reviewer"] = True
                    elif "claude" in reviewer and state == "APPROVED":
                        reviewers["claude_reviewer"] = True
        except Exception as e:
            print(f"⚠️  检查 Reviewers 失败: {e}")
        
        return reviewers
    
    def check_ui_screenshots(self, pr_number: int) -> bool:
        """检查 UI 截图"""
        try:
            result = subprocess.run(
                ["gh", "pr", "view", str(pr_number), "--json", "body"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                pr_data = json.loads(result.stdout)
                body = pr_data.get("body", "")
                
                # 检查是否包含图片
                if "![" in body or "<img" in body.lower():
                    return True
        except Exception as e:
            print(f"⚠️  检查截图失败: {e}")
        
        return False
    
    def evaluate_completion(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """评估任务完成度"""
        completion = {
            "task_id": task["id"],
            "status": task.get("status"),
            "checks": {
                "tmux_alive": False,
                "pr_created": False,
                "branch_synced": False,
                "ci_passed": False,
                "codex_reviewer_passed": False,
                "gemini_reviewer_passed": False,
                "ui_screenshots": False
            },
            "pr": None,
            "ready_for_review": False,
            "needs_retry": False
        }
        
        # 1. 检查 tmux 会话
        tmux_session = task.get("tmuxSession")
        if tmux_session:
            completion["checks"]["tmux_alive"] = self.check_tmux_session(tmux_session)
        
        # 2. 检查 PR
        branch = task.get("branch")
        pr = self.check_pr_exists(branch)
        if pr:
            completion["checks"]["pr_created"] = True
            completion["pr"] = pr
            
            # 3. 检查 CI
            ci = self.check_ci_status(branch)
            completion["checks"]["ci_passed"] = ci.get("passed", False)
            
            # 4. 检查 Reviewers
            pr_number = pr.get("number")
            reviewers = self.check_reviewers_passed(pr_number)
            completion["checks"]["codex_reviewer_passed"] = reviewers["codex_reviewer"]
            completion["checks"]["gemini_reviewer_passed"] = reviewers["gemini_reviewer"]
            
            # 5. 检查截图
            completion["checks"]["ui_screenshots"] = self.check_ui_screenshots(pr_number)
            
            # 6. 检查分支同步
            try:
                result = subprocess.run(
                    ["git", "fetch", "origin", branch],
                    capture_output=True,
                    timeout=30
                )
                if result.returncode == 0:
                    completion["checks"]["branch_synced"] = True
            except Exception:
                pass
        
        # 评估是否准备好 review
        criteria = self.config.get('completion_criteria', {})
        ready = True
        for key, required in criteria.items():
            if required and not completion["checks"].get(key.replace("_", "_")):
                ready = False
                break
        
        completion["ready_for_review"] = ready
        
        # 检查是否需要重试
        if task.get("status") == "running":
            # 检查是否超时
            started_at = task.get("startedAt", 0)
            max_idle = self.config.get('monitoring', {}).get('max_idle_minutes', 120)
            elapsed_minutes = (datetime.now().timestamp() * 1000 - started_at) / 60000
            
            if elapsed_minutes > max_idle and not completion["checks"]["tmux_alive"]:
                completion["needs_retry"] = True
        
        return completion
    
    def update_task_status(self, task_id: str, updates: Dict[str, Any]):
        """更新任务状态"""
        task_file = self.tasks_dir / f"{task_id}.json"
        if not task_file.exists():
            return
        
        try:
            with open(task_file, 'r', encoding='utf-8') as f:
                task = json.load(f)
            
            task.update(updates)
            
            with open(task_file, 'w', encoding='utf-8') as f:
                json.dump(task, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️  更新任务状态失败: {e}")
    
    def monitor_all(self) -> List[Dict[str, Any]]:
        """监控所有任务"""
        tasks = self.get_all_tasks()
        results = []
        
        print(f"\n{'='*60}")
        print(f"Agent 监控报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        for task in tasks:
            if task.get("status") in ["completed", "merged"]:
                continue
            
            print(f"📋 任务: {task['id']}")
            print(f"   Agent: {task.get('agent')}")
            print(f"   状态: {task.get('status')}")
            
            completion = self.evaluate_completion(task)
            results.append(completion)
            
            # 打印检查结果
            checks = completion["checks"]
            print(f"   检查结果:")
            print(f"     - Tmux 存活: {'✅' if checks['tmux_alive'] else '❌'}")
            print(f"     - PR 创建: {'✅' if checks['pr_created'] else '❌'}")
            print(f"     - CI 通过: {'✅' if checks['ci_passed'] else '❌'}")
            print(f"     - Codex Review: {'✅' if checks['codex_reviewer_passed'] else '❌'}")
            print(f"     - Gemini Review: {'✅' if checks['gemini_reviewer_passed'] else '❌'}")
            print(f"     - UI 截图: {'✅' if checks['ui_screenshots'] else '❌'}")
            
            if completion["ready_for_review"]:
                print(f"   🎉 准备好进行 Review!")
                self.update_task_status(task["id"], {"status": "ready_for_review"})
            
            if completion["needs_retry"]:
                print(f"   ⚠️  需要重试")
                self.update_task_status(task["id"], {"status": "needs_retry"})
            
            print()
        
        return results
    
    def send_notification(self, message: str, task: Dict = None):
        """发送通知"""
        telegram_config = self.config.get('notifications', {}).get('telegram', {})
        
        if telegram_config.get('enabled') and telegram_config.get('bot_token'):
            # 发送 Telegram 通知
            try:
                import requests
                url = f"https://api.telegram.org/bot{telegram_config['bot_token']}/sendMessage"
                data = {
                    "chat_id": telegram_config['chat_id'],
                    "text": message,
                    "parse_mode": "Markdown"
                }
                requests.post(url, data=data, timeout=10)
            except Exception as e:
                print(f"⚠️  发送 Telegram 通知失败: {e}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Agent 监控器")
    parser.add_argument("--config", default="./agent-config.yaml", help="配置文件路径")
    parser.add_argument("--once", action="store_true", help="只运行一次")
    parser.add_argument("--interval", type=int, default=10, help="监控间隔（分钟）")
    
    args = parser.parse_args()
    
    monitor = AgentMonitor(args.config)
    
    if args.once:
        monitor.monitor_all()
    else:
        import time
        while True:
            monitor.monitor_all()
            print(f"\n⏰ 等待 {args.interval} 分钟后再次检查...\n")
            time.sleep(args.interval * 60)


if __name__ == "__main__":
    main()
