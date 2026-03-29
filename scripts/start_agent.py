#!/usr/bin/env python3
"""
Agent 启动器 - 创建 worktree、启动 tmux 会话、运行 Agent
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any


class AgentLauncher:
    """Agent 启动器"""
    
    def __init__(self, config_path: str = "./agent-config.yaml"):
        self.config_path = Path(config_path)
        self.tasks_dir = Path("./tasks")
        self.worktrees_base = Path("../worktrees")
        self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        import yaml
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = {}
    
    def create_worktree(self, task_id: str, branch_name: str, base_branch: str = "main") -> Path:
        """创建 git worktree"""
        worktree_path = self.worktrees_base / task_id
        
        # 检查是否已存在
        if worktree_path.exists():
            print(f"⚠️  Worktree 已存在: {worktree_path}")
            return worktree_path
        
        # 创建 worktree
        cmd = [
            "git", "worktree", "add",
            str(worktree_path),
            "-b", branch_name,
            f"origin/{base_branch}"
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"✅ Worktree 创建成功: {worktree_path}")
            return worktree_path
        except subprocess.CalledProcessError as e:
            print(f"❌ 创建 worktree 失败: {e}")
            raise
    
    def install_dependencies(self, worktree_path: Path):
        """安装依赖"""
        lock_file = worktree_path / "pnpm-lock.yaml"
        if lock_file.exists():
            cmd = ["pnpm", "install"]
        elif (worktree_path / "yarn.lock").exists():
            cmd = ["yarn", "install"]
        elif (worktree_path / "package-lock.json").exists():
            cmd = ["npm", "install"]
        else:
            print("⚠️  未找到包管理器，跳过依赖安装")
            return
        
        try:
            subprocess.run(cmd, cwd=worktree_path, check=True, capture_output=True)
            print(f"✅ 依赖安装成功")
        except subprocess.CalledProcessError as e:
            print(f"❌ 依赖安装失败: {e}")
    
    def start_tmux_session(self, task_id: str, worktree_path: Path, 
                           agent_type: str, model: str, description: str) -> str:
        """启动 tmux 会话"""
        session_name = f"{agent_type}-{task_id[:20]}"
        
        # 构建启动命令
        run_script = f"""
#!/bin/bash
cd {worktree_path}
echo "Starting {agent_type} agent..."
echo "Model: {model}"
echo "Task: {description}"
# 在这里调用实际的 Agent 运行脚本
# 例如: codex-agent run --model {model}
"""
        
        # 创建 tmux 会话
        cmd = [
            "tmux", "new-session", "-d",
            "-s", session_name,
            "-c", str(worktree_path),
            run_script
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"✅ Tmux 会话启动: {session_name}")
            return session_name
        except subprocess.CalledProcessError as e:
            print(f"❌ Tmux 会话启动失败: {e}")
            # 如果 tmux 不可用，使用后台进程
            return self.start_background_process(task_id, worktree_path, agent_type, model)
    
    def start_background_process(self, task_id: str, worktree_path: Path,
                                  agent_type: str, model: str) -> str:
        """启动后台进程（Windows 兼容）"""
        import threading
        import time
        
        # 创建启动脚本
        script_path = worktree_path / f"run_{agent_type}.sh"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(f"""#!/bin/bash
cd {worktree_path}
echo "Starting {agent_type} agent..."
echo "Model: {model}"
# 在这里调用实际的 Agent 运行脚本
""")
        
        # 记录进程信息
        pid_file = self.tasks_dir / f"{task_id}.pid"
        return str(pid_file)
    
    def create_task_record(self, task_id: str, agent_type: str, model: str,
                           description: str, repo: str, branch: str,
                           worktree: Path, tmux_session: str) -> Dict[str, Any]:
        """创建任务记录"""
        task_record = {
            "id": task_id,
            "tmuxSession": tmux_session,
            "agent": agent_type,
            "model": model,
            "description": description,
            "repo": repo,
            "worktree": str(worktree),
            "branch": branch,
            "startedAt": int(datetime.now().timestamp() * 1000),
            "status": "running",
            "notifyOnComplete": True,
            "retries": 0,
            "maxRetries": self.config.get('cluster', {}).get('max_retries', 3)
        }
        
        # 保存到文件
        self.tasks_dir.mkdir(parents=True, exist_ok=True)
        task_file = self.tasks_dir / f"{task_id}.json"
        with open(task_file, 'w', encoding='utf-8') as f:
            json.dump(task_record, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 任务记录已保存: {task_file}")
        return task_record
    
    def launch(self, task_id: str, description: str, agent_type: str = "codex",
               model: str = None, base_branch: str = "main") -> Dict[str, Any]:
        """启动 Agent"""
        
        # 获取配置
        agent_config = self.config.get('agents', {}).get(agent_type, {})
        if not model:
            model = agent_config.get('model', 'gpt-5.3-codex')
        
        # 生成分支名
        branch_name = f"feat/{task_id[:50]}"
        
        print(f"\n🚀 启动 Agent: {agent_type}")
        print(f"   任务ID: {task_id}")
        print(f"   模型: {model}")
        print(f"   描述: {description}")
        print()
        
        try:
            # 1. 创建 worktree
            worktree = self.create_worktree(task_id, branch_name, base_branch)
            
            # 2. 安装依赖
            self.install_dependencies(worktree)
            
            # 3. 启动 tmux 会话或后台进程
            tmux_session = self.start_tmux_session(
                task_id, worktree, agent_type, model, description
            )
            
            # 4. 创建任务记录
            task_record = self.create_task_record(
                task_id=task_id,
                agent_type=agent_type,
                model=model,
                description=description,
                repo=os.path.basename(os.getcwd()),
                branch=branch_name,
                worktree=worktree,
                tmux_session=tmux_session
            )
            
            return task_record
            
        except Exception as e:
            print(f"❌ Agent 启动失败: {e}")
            return {"error": str(e)}


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Agent 启动器")
    parser.add_argument("--task-id", required=True, help="任务ID")
    parser.add_argument("--description", required=True, help="任务描述")
    parser.add_argument("--agent", default="codex", help="Agent类型 (codex/claude_code/gemini)")
    parser.add_argument("--model", help="模型名称")
    parser.add_argument("--base-branch", default="main", help="基础分支")
    parser.add_argument("--config", default="./agent-config.yaml", help="配置文件路径")
    
    args = parser.parse_args()
    
    launcher = AgentLauncher(args.config)
    result = launcher.launch(
        task_id=args.task_id,
        description=args.description,
        agent_type=args.agent,
        model=args.model,
        base_branch=args.base_branch
    )
    
    print("\n" + "="*60)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
