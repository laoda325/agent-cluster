#!/usr/bin/env python3
"""
淇鑴氭湰锛氭鏌ュ苟淇鎵€鏈変换鍔＄殑PR鍒涘缓闂
========================================
1. 妫€鏌ユ墍鏈変换鍔＄殑heartbeat鏂囦欢
2. 濡傛灉浠诲姟宸插畬鎴愶紝鑷姩鍒涘缓PR
3. 濡傛灉浠诲姟澶辫触锛屾爣璁伴渶瑕侀噸璇?
"""

import json
import subprocess
from pathlib import Path
from datetime import datetime


class PRCreationFixer:
    """PR鍒涘缓淇鍣?""
    
    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.tasks_dir = self.base_dir / "tasks"
        self.worktrees_base = self.base_dir / ".." / "worktrees"
    
    def check_task_completion(self, task_id: str) -> dict:
        """妫€鏌ヤ换鍔℃槸鍚﹀凡瀹屾垚"""
        heartbeat_file = self.tasks_dir / f"{task_id}.heartbeat.json"
        task_file = self.tasks_dir / f"{task_id}.json"
        
        result = {
            "task_id": task_id,
            "heartbeat_exists": heartbeat_file.exists(),
            "task_file_exists": task_file.exists(),
            "status": "unknown",
            "exit_code": None,
            "pr_created": False
        }
        
        # 妫€鏌eartbeat鏂囦欢
        if heartbeat_file.exists():
            try:
                heartbeat = json.loads(heartbeat_file.read_text(encoding='utf-8'))
                result["status"] = heartbeat.get("status", "unknown")
                result["exit_code"] = heartbeat.get("exit_code")
                
                # 濡傛灉exit_code瀛樺湪锛岃鏄庝换鍔″凡瀹屾垚
                if result["exit_code"] is not None:
                    result["completed"] = True
                else:
                    result["completed"] = False
            except Exception as e:
                result["error"] = str(e)
        
        # 妫€鏌ヤ换鍔℃枃浠?
        if task_file.exists():
            try:
                task = json.loads(task_file.read_text(encoding='utf-8'))
                result["agent"] = task.get("agent")
                result["branch"] = task.get("branch")
                result["worktree"] = task.get("worktree")
            except Exception as e:
                result["error"] = str(e)
        
        return result
    
    def create_pr_for_task(self, task_id: str, task_info: dict) -> bool:
        """涓轰换鍔″垱寤篜R"""
        if not task_info.get("worktree"):
            print(f"鉂?鏃犳硶鍒涘缓PR: 缂哄皯worktree淇℃伅")
            return False
        
        worktree_path = Path(task_info["worktree"])
        
        if not worktree_path.exists():
            print(f"鉂?Worktree涓嶅瓨鍦? {worktree_path}")
            return False
        
        try:
            # 妫€鏌ユ槸鍚︽湁鏈彁浜ょ殑鏇存敼
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=worktree_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if not result.stdout.strip():
                print(f"鈿狅笍  娌℃湁鏈彁浜ょ殑鏇存敼")
                return False
            
            # 娣诲姞鎵€鏈夋洿鏀?
            subprocess.run(
                ["git", "add", "-A"],
                cwd=worktree_path,
                check=True,
                timeout=10
            )
            print(f"鉁?宸叉殏瀛樻墍鏈夋洿鏀?)
            
            # 鎻愪氦
            commit_msg = f"feat: {task_id}\n\nAgent鑷姩鐢熸垚鐨勪唬鐮佹彁浜?
            subprocess.run(
                ["git", "commit", "-m", commit_msg],
                cwd=worktree_path,
                check=True,
                timeout=10
            )
            print(f"鉁?宸叉彁浜や唬鐮?)
            
            # 鎺ㄩ€?
            branch = task_info.get("branch", "main")
            subprocess.run(
                ["git", "push", "origin", branch],
                cwd=worktree_path,
                check=True,
                timeout=30,
                env={**subprocess.os.environ, "GH_TOKEN": "os.environ.get("GH_TOKEN","")"}
            )
            print(f"鉁?宸叉帹閫佸埌 origin/{branch}")
            
            # 鍒涘缓PR
            result = subprocess.run(
                ["gh", "pr", "create", "--fill"],
                cwd=worktree_path,
                capture_output=True,
                text=True,
                timeout=30,
                env={**subprocess.os.environ, "GH_TOKEN": "os.environ.get("GH_TOKEN","")"}
            )
            
            if result.returncode == 0:
                pr_url = result.stdout.strip()
                print(f"鉁?PR宸插垱寤? {pr_url}")
                return True
            else:
                print(f"鉂?PR鍒涘缓澶辫触: {result.stderr}")
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"鉂?鎿嶄綔澶辫触: {e}")
            return False
        except Exception as e:
            print(f"鉂?閿欒: {e}")
            return False
    
    def fix_all_tasks(self):
        """淇鎵€鏈変换鍔?""
        print("="*60)
        print("馃敡 PR鍒涘缓淇宸ュ叿")
        print("="*60)
        print()
        
        # 鑾峰彇鎵€鏈変换鍔℃枃浠?
        task_files = list(self.tasks_dir.glob("*.json"))
        task_ids = set()
        
        for task_file in task_files:
            # 鎺掗櫎heartbeat鍜屽叾浠栨枃浠?
            if not task_file.name.endswith(".heartbeat.json") and not task_file.name.endswith(".log"):
                task_id = task_file.stem
                task_ids.add(task_id)
        
        if not task_ids:
            print("鉂?娌℃湁鎵惧埌浠讳綍浠诲姟")
            return
        
        print(f"馃搵 鎵惧埌 {len(task_ids)} 涓换鍔n")
        
        completed_count = 0
        pr_created_count = 0
        
        for task_id in sorted(task_ids):
            print(f"\n{'='*60}")
            print(f"妫€鏌ヤ换鍔? {task_id}")
            print(f"{'='*60}")
            
            # 妫€鏌ヤ换鍔＄姸鎬?
            task_info = self.check_task_completion(task_id)
            
            print(f"鐘舵€? {task_info.get('status', 'unknown')}")
            print(f"Exit Code: {task_info.get('exit_code', 'N/A')}")
            
            if task_info.get("completed"):
                completed_count += 1
                print(f"鉁?浠诲姟宸插畬鎴?)
                
                # 灏濊瘯鍒涘缓PR
                if self.create_pr_for_task(task_id, task_info):
                    pr_created_count += 1
            else:
                print(f"鈴?浠诲姟浠嶅湪杩愯鎴栨湭瀹屾垚")
        
        print(f"\n{'='*60}")
        print(f"馃搳 淇瀹屾垚")
        print(f"{'='*60}")
        print(f"宸插畬鎴愪换鍔? {completed_count}")
        print(f"宸插垱寤篜R: {pr_created_count}")


def main():
    """涓诲嚱鏁?""
    import sys
    
    base_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    fixer = PRCreationFixer(base_dir)
    fixer.fix_all_tasks()


if __name__ == "__main__":
    main()

