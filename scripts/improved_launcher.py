#!/usr/bin/env python3
"""
鏀硅繘鐨凙gent鍚姩娴佺▼
==================
1. 鍚姩Agent鎵ц
2. 鐩戞帶鎵ц杩涘害锛堝甫瓒呮椂鏈哄埗锛?
3. Agent瀹屾垚鍚庤嚜鍔ㄥ垱寤篜R
4. 鍙戦€佸畬鎴愰€氱煡
"""

import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any


class ImprovedAgentLauncher:
    """鏀硅繘鐨凙gent鍚姩鍣?""
    
    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.tasks_dir = self.base_dir / "tasks"
        self.scripts_dir = self.base_dir / "scripts"
        self.worktrees_base = self.base_dir / ".." / "worktrees"
    
    def monitor_and_complete_task(self, task_id: str, timeout_minutes: int = 30):
        """
        鐩戞帶浠诲姟鎵ц锛屽畬鎴愬悗鑷姩鍒涘缓PR
        
        Args:
            task_id: 浠诲姟ID
            timeout_minutes: 瓒呮椂鏃堕棿锛堝垎閽燂級
        """
        print(f"\n{'='*60}")
        print(f"馃攧 鐩戞帶浠诲姟: {task_id}")
        print(f"瓒呮椂鏃堕棿: {timeout_minutes} 鍒嗛挓")
        print(f"{'='*60}\n")
        
        heartbeat_file = self.tasks_dir / f"{task_id}.heartbeat.json"
        task_file = self.tasks_dir / f"{task_id}.json"
        
        if not task_file.exists():
            print(f"鉂?浠诲姟鏂囦欢涓嶅瓨鍦? {task_file}")
            return False
        
        # 璇诲彇浠诲姟淇℃伅
        task_info = json.loads(task_file.read_text(encoding='utf-8'))
        
        start_time = time.time()
        timeout_seconds = timeout_minutes * 60
        check_interval = 5  # 姣?绉掓鏌ヤ竴娆?
        
        while True:
            elapsed = time.time() - start_time
            elapsed_minutes = elapsed / 60
            
            # 妫€鏌ユ槸鍚﹁秴鏃?
            if elapsed > timeout_seconds:
                print(f"\n鈴憋笍  浠诲姟瓒呮椂锛坽timeout_minutes}鍒嗛挓锛?)
                print(f"鉂?寮哄埗鍋滄浠诲姟")
                self._kill_task(task_id, task_info)
                return False
            
            # 妫€鏌eartbeat鏂囦欢
            if heartbeat_file.exists():
                try:
                    heartbeat = json.loads(heartbeat_file.read_text(encoding='utf-8'))
                    status = heartbeat.get("status", "unknown")
                    exit_code = heartbeat.get("exit_code")
                    
                    # 鎵撳嵃杩涘害
                    if exit_code is None:
                        print(f"鈴?杩愯涓?.. ({elapsed_minutes:.1f}鍒嗛挓) | 鐘舵€? {status}")
                    else:
                        # 浠诲姟宸插畬鎴?
                        print(f"\n鉁?浠诲姟宸插畬鎴?)
                        print(f"   鐘舵€? {status}")
                        print(f"   Exit Code: {exit_code}")
                        print(f"   鑰楁椂: {elapsed_minutes:.1f}鍒嗛挓")
                        
                        # 鑷姩鍒涘缓PR
                        if exit_code == 0:
                            print(f"\n馃殌 鑷姩鍒涘缓PR...")
                            if self._create_pr_for_task(task_id, task_info):
                                print(f"鉁?PR鍒涘缓鎴愬姛")
                                return True
                            else:
                                print(f"鈿狅笍  PR鍒涘缓澶辫触锛屼絾浠诲姟宸插畬鎴?)
                                return True
                        else:
                            print(f"\n鉂?浠诲姟鎵ц澶辫触 (exit code: {exit_code})")
                            return False
                        
                except json.JSONDecodeError:
                    pass
            
            time.sleep(check_interval)
    
    def _kill_task(self, task_id: str, task_info: dict):
        """鏉€姝讳换鍔¤繘绋?""
        process_id = task_info.get("processId")
        if process_id:
            try:
                subprocess.run(
                    ["taskkill", "/PID", str(process_id), "/F"],
                    check=False,
                    timeout=10
                )
                print(f"鉁?杩涚▼宸叉潃姝? PID {process_id}")
            except Exception as e:
                print(f"鈿狅笍  鏃犳硶鏉€姝昏繘绋? {e}")
    
    def _create_pr_for_task(self, task_id: str, task_info: dict) -> bool:
        """涓轰换鍔″垱寤篜R"""
        worktree = task_info.get("worktree")
        if not worktree:
            print(f"鉂?缂哄皯worktree淇℃伅")
            return False
        
        worktree_path = Path(worktree)
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
            env = {**subprocess.os.environ, "GH_TOKEN": "os.environ.get("GH_TOKEN","")"}
            subprocess.run(
                ["git", "push", "origin", branch],
                cwd=worktree_path,
                check=True,
                timeout=30,
                env=env
            )
            print(f"鉁?宸叉帹閫佸埌 origin/{branch}")
            
            # 鍒涘缓PR
            result = subprocess.run(
                ["gh", "pr", "create", "--fill"],
                cwd=worktree_path,
                capture_output=True,
                text=True,
                timeout=30,
                env=env
            )
            
            if result.returncode == 0:
                pr_url = result.stdout.strip()
                print(f"鉁?PR宸插垱寤? {pr_url}")
                
                # 鏇存柊浠诲姟璁板綍
                task_file = self.tasks_dir / f"{task_id}.json"
                if task_file.exists():
                    task = json.loads(task_file.read_text(encoding='utf-8'))
                    task["pr_created"] = True
                    task["pr_url"] = pr_url
                    task["status"] = "pr_created"
                    task["updatedAt"] = int(datetime.now().timestamp() * 1000)
                    task_file.write_text(json.dumps(task, indent=2, ensure_ascii=False), encoding='utf-8')
                
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


def main():
    """涓诲嚱鏁?""
    if len(sys.argv) < 2:
        print("鐢ㄦ硶: python improved_launcher.py <task_id> [timeout_minutes]")
        print("\n绀轰緥:")
        print("  python improved_launcher.py task-20260401083432")
        print("  python improved_launcher.py task-20260401083432 60")
        sys.exit(1)
    
    task_id = sys.argv[1]
    timeout_minutes = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    
    launcher = ImprovedAgentLauncher(".")
    success = launcher.monitor_and_complete_task(task_id, timeout_minutes)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

