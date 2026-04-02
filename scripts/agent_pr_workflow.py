#!/usr/bin/env python3
"""
Agent PR鍒涘缓宸ヤ綔娴?
==================
Agent瀹屾垚浠ｇ爜 鈫?鎻愪氦 鈫?鎺ㄩ€?鈫?浼佷笟寰俊閫氱煡 鈫?鍒涘缓PR
"""

import subprocess
import json
from pathlib import Path
from datetime import datetime


class AgentPRWorkflow:
    """Agent PR鍒涘缓宸ヤ綔娴?""
    
    def __init__(self, task_id: str, worktree_path: str, gh_token: str):
        self.task_id = task_id
        self.worktree_path = Path(worktree_path)
        self.gh_token = gh_token
        self.branch_name = self._extract_branch_name()
    
    def _extract_branch_name(self) -> str:
        """浠巘ask_id鎻愬彇鍒嗘敮鍚?""
        # task-20260330185004-鍒涗綔-涓夊浗婕斾箟澶栦紶-绗竴绔?鈫?task-20260330185004
        parts = self.task_id.split('-')
        if len(parts) >= 2:
            return f"{parts[0]}-{parts[1]}"
        return self.task_id
    
    def step1_commit_code(self, message: str = None) -> bool:
        """姝ラ1: 鎻愪氦浠ｇ爜"""
        print(f"\n{'='*60}")
        print("馃摑 姝ラ1: 鎻愪氦浠ｇ爜")
        print(f"{'='*60}")
        
        if not message:
            message = f"feat: {self.task_id}\n\nAgent鑷姩鐢熸垚鐨勪唬鐮佹彁浜?
        
        try:
            # 妫€鏌ユ槸鍚︽湁鏈彁浜ょ殑鏇存敼
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.worktree_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if not result.stdout.strip():
                print("鈿狅笍  娌℃湁鏈彁浜ょ殑鏇存敼")
                return False
            
            # 娣诲姞鎵€鏈夋洿鏀?
            subprocess.run(
                ["git", "add", "-A"],
                cwd=self.worktree_path,
                check=True,
                timeout=10
            )
            print("鉁?宸叉殏瀛樻墍鏈夋洿鏀?)
            
            # 鎻愪氦
            subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self.worktree_path,
                check=True,
                timeout=10
            )
            print(f"鉁?宸叉彁浜? {message[:50]}...")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"鉂?鎻愪氦澶辫触: {e}")
            return False
        except Exception as e:
            print(f"鉂?閿欒: {e}")
            return False
    
    def step2_push_code(self) -> bool:
        """姝ラ2: 鎺ㄩ€佷唬鐮?""
        print(f"\n{'='*60}")
        print("馃殌 姝ラ2: 鎺ㄩ€佷唬鐮?)
        print(f"{'='*60}")
        
        try:
            # 鎺ㄩ€佸埌杩滅▼鍒嗘敮
            subprocess.run(
                ["git", "push", "origin", self.branch_name],
                cwd=self.worktree_path,
                check=True,
                timeout=30,
                env={**subprocess.os.environ, "GH_TOKEN": self.gh_token}
            )
            print(f"鉁?宸叉帹閫佸埌 origin/{self.branch_name}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"鉂?鎺ㄩ€佸け璐? {e}")
            return False
        except Exception as e:
            print(f"鉂?閿欒: {e}")
            return False
    
    def step3_notify_wecom(self, pr_url: str = None) -> bool:
        """姝ラ3: 鎺ㄩ€佷紒涓氬井淇￠€氱煡"""
        print(f"\n{'='*60}")
        print("馃挰 姝ラ3: 鎺ㄩ€佷紒涓氬井淇￠€氱煡")
        print(f"{'='*60}")
        
        try:
            # 鏋勫缓閫氱煡娑堟伅
            message = f"""
馃 Agent浠ｇ爜鎻愪氦閫氱煡

**浠诲姟ID**: {self.task_id}
**鍒嗘敮**: {self.branch_name}
**鏃堕棿**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**鐘舵€?*: 鉁?浠ｇ爜宸叉彁浜ゅ苟鎺ㄩ€?

"""
            if pr_url:
                message += f"**PR閾炬帴**: {pr_url}\n"
            
            message += f"""
**鍚庣画姝ラ**:
1. 绛夊緟CI妫€鏌?
2. 浠ｇ爜瀹℃煡
3. 鍚堝苟鍒癿ain鍒嗘敮

---
*鐢盇gent闆嗙兢绯荤粺鑷姩鐢熸垚*
"""
            
            print("馃摛 鍙戦€佷紒涓氬井淇￠€氱煡...")
            print(message)
            
            # 杩欓噷鍙互闆嗘垚浼佷笟寰俊API
            # 鏆傛椂鍙墦鍗版秷鎭?
            print("鉁?閫氱煡宸插噯澶囷紙闇€瑕侀泦鎴愪紒涓氬井淇PI锛?)
            return True
            
        except Exception as e:
            print(f"鉂?閫氱煡澶辫触: {e}")
            return False
    
    def step4_create_pr(self) -> str:
        """姝ラ4: 鍒涘缓PR"""
        print(f"\n{'='*60}")
        print("馃搵 姝ラ4: 鍒涘缓PR")
        print(f"{'='*60}")
        
        try:
            # 浣跨敤 gh pr create --fill 鑷姩濉厖PR淇℃伅
            result = subprocess.run(
                ["gh", "pr", "create", "--fill"],
                cwd=self.worktree_path,
                capture_output=True,
                text=True,
                timeout=30,
                env={**subprocess.os.environ, "GH_TOKEN": self.gh_token}
            )
            
            if result.returncode == 0:
                # 鎻愬彇PR URL
                pr_url = result.stdout.strip()
                print(f"鉁?PR宸插垱寤? {pr_url}")
                return pr_url
            else:
                print(f"鉂?PR鍒涘缓澶辫触: {result.stderr}")
                return None
                
        except subprocess.CalledProcessError as e:
            print(f"鉂?鍒涘缓PR澶辫触: {e}")
            return None
        except Exception as e:
            print(f"鉂?閿欒: {e}")
            return None
    
    def run_workflow(self, commit_message: str = None) -> dict:
        """杩愯瀹屾暣宸ヤ綔娴?""
        print(f"\n{'='*60}")
        print(f"馃攧 Agent PR鍒涘缓宸ヤ綔娴?)
        print(f"浠诲姟ID: {self.task_id}")
        print(f"{'='*60}")
        
        result = {
            "task_id": self.task_id,
            "branch": self.branch_name,
            "timestamp": datetime.now().isoformat(),
            "steps": {}
        }
        
        # 姝ラ1: 鎻愪氦浠ｇ爜
        if not self.step1_commit_code(commit_message):
            result["status"] = "failed"
            result["failed_at"] = "commit"
            return result
        result["steps"]["commit"] = "success"
        
        # 姝ラ2: 鎺ㄩ€佷唬鐮?
        if not self.step2_push_code():
            result["status"] = "failed"
            result["failed_at"] = "push"
            return result
        result["steps"]["push"] = "success"
        
        # 姝ラ3: 浼佷笟寰俊閫氱煡
        self.step3_notify_wecom()
        result["steps"]["notify"] = "success"
        
        # 姝ラ4: 鍒涘缓PR
        pr_url = self.step4_create_pr()
        if pr_url:
            result["steps"]["pr_create"] = "success"
            result["pr_url"] = pr_url
            result["status"] = "success"
            
            # 鍐嶆鍙戦€佷紒涓氬井淇￠€氱煡锛堝寘鍚玃R閾炬帴锛?
            self.step3_notify_wecom(pr_url)
        else:
            result["steps"]["pr_create"] = "failed"
            result["status"] = "partial"
        
        return result


def main():
    """涓诲嚱鏁?""
    import sys
    
    if len(sys.argv) < 2:
        print("鐢ㄦ硶: python agent_pr_workflow.py <task_id> [worktree_path] [gh_token]")
        print("\n绀轰緥:")
        print("  python agent_pr_workflow.py task-20260330185004")
        sys.exit(1)
    
    task_id = sys.argv[1]
    worktree_path = sys.argv[2] if len(sys.argv) > 2 else f"../worktrees/{task_id}"
    gh_token = sys.argv[3] if len(sys.argv) > 3 else "os.environ.get("GH_TOKEN","")"
    
    workflow = AgentPRWorkflow(task_id, worktree_path, gh_token)
    result = workflow.run_workflow()
    
    print(f"\n{'='*60}")
    print("馃搳 宸ヤ綔娴佸畬鎴?)
    print(f"{'='*60}")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 淇濆瓨缁撴灉
    result_file = Path(worktree_path) / ".pr-workflow-result.json"
    result_file.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"\n鉁?缁撴灉宸蹭繚瀛? {result_file}")


if __name__ == "__main__":
    main()

