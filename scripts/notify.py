#!/usr/bin/env python3
"""
通知服务 - 发送 微信/Discord 通知
"""

import json
import sys
from datetime import datetime
from typing import Dict, Optional
import yaml


class NotificationService:
    """通知服务"""
    
    def __init__(self, config_path: str = "./agent-config.yaml"):
        self.config_path = config_path
        self.load_config()
    
    def load_config(self):
        """加载配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
        except Exception:
            self.config = {}
    
    def send_wechat(self, message: str) -> bool:
        """发送企业微信机器人通知"""
        wechat_config = self.config.get('notifications', {}).get('wechat', {})
        
        if not wechat_config.get('enabled'):
            print("⚠️  微信通知未启用")
            return False
        
        webhook_url = wechat_config.get('webhook_url')
        
        if not webhook_url:
            print("⚠️  微信配置不完整")
            return False
        
        try:
            import requests
            data = {
                "msgtype": "text",
                "text": {
                    "content": message
                }
            }
            
            response = requests.post(webhook_url, json=data, timeout=10)
            result = response.json() if response.text else {}
            
            if response.status_code == 200 and result.get("errcode") == 0:
                print("✅ 微信通知发送成功")
                return True
            else:
                print(f"⚠️  微信通知发送失败: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 微信通知发送失败: {e}")
            return False
    
    def send_discord(self, message: str) -> bool:
        """发送 Discord 通知"""
        discord_config = self.config.get('notifications', {}).get('discord', {})
        
        if not discord_config.get('enabled'):
            print("⚠️  Discord 通知未启用")
            return False
        
        webhook_url = discord_config.get('webhook_url')
        
        if not webhook_url:
            print("⚠️  Discord 配置不完整")
            return False
        
        try:
            import requests
            data = {
                "content": message
            }
            
            response = requests.post(webhook_url, json=data, timeout=10)
            
            if response.status_code == 204:
                print("✅ Discord 通知发送成功")
                return True
            else:
                print(f"⚠️  Discord 通知发送失败: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Discord 通知发送失败: {e}")
            return False
    
    def notify_pr_ready(self, pr_number: int, pr_url: str, 
                       task_id: str, description: str):
        """通知 PR 准备好审查"""
        message = f"""
🎉 **PR 准备好审查**

📋 **任务**: {task_id}
📝 **描述**: {description}
🔢 **PR 编号**: #{pr_number}
🔗 **链接**: {pr_url}

✅ CI 通过
✅ AI Review 通过
✅ 所有检查完成

请尽快审查。
"""
        self.send_wechat(message)
        self.send_discord(message)
    
    def notify_agent_started(self, agent: str, task_id: str, description: str):
        """通知 Agent 已启动"""
        message = f"""
🚀 **Agent 已启动**

🤖 **Agent**: {agent}
📋 **任务**: {task_id}
📝 **描述**: {description}
⏰ **时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        self.send_wechat(message)
    
    def notify_agent_failed(self, agent: str, task_id: str, error: str):
        """通知 Agent 失败"""
        message = f"""
❌ **Agent 运行失败**

🤖 **Agent**: {agent}
📋 **任务**: {task_id}
⚠️  **错误**: {error}
⏰ **时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

需要人工介入。
"""
        self.send_wechat(message)
    
    def notify_pr_merged(self, pr_number: int, task_id: str):
        """通知 PR 已合并"""
        message = f"""
✅ **PR 已合并**

📋 **任务**: {task_id}
🔢 **PR 编号**: #{pr_number}
⏰ **时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        self.send_wechat(message)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="通知服务")
    parser.add_argument("--type", required=True, 
                       choices=["pr_ready", "agent_started", "agent_failed", "pr_merged"],
                       help="通知类型")
    parser.add_argument("--config", default="./agent-config.yaml", help="配置文件路径")
    
    # 根据通知类型添加不同参数
    parser.add_argument("--pr-number", type=int, help="PR 编号")
    parser.add_argument("--pr-url", help="PR URL")
    parser.add_argument("--task-id", help="任务 ID")
    parser.add_argument("--description", help="描述")
    parser.add_argument("--agent", help="Agent 名称")
    parser.add_argument("--error", help="错误信息")
    
    args = parser.parse_args()
    
    notifier = NotificationService(args.config)
    
    if args.type == "pr_ready":
        notifier.notify_pr_ready(
            pr_number=args.pr_number,
            pr_url=args.pr_url,
            task_id=args.task_id,
            description=args.description
        )
    elif args.type == "agent_started":
        notifier.notify_agent_started(
            agent=args.agent,
            task_id=args.task_id,
            description=args.description
        )
    elif args.type == "agent_failed":
        notifier.notify_agent_failed(
            agent=args.agent,
            task_id=args.task_id,
            error=args.error
        )
    elif args.type == "pr_merged":
        notifier.notify_pr_merged(
            pr_number=args.pr_number,
            task_id=args.task_id
        )


if __name__ == "__main__":
    main()
