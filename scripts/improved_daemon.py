#!/usr/bin/env python3
"""
鏀硅繘鐨凙gent闆嗙兢瀹堟姢杩涚▼
=======================
1. 姣廚鍒嗛挓妫€鏌ヤ竴娆′换鍔＄姸鎬?
2. 妫€娴嬪埌浠诲姟瀹屾垚鍚庤嚜鍔ㄥ垱寤篜R
3. 鑷姩閲嶈瘯澶辫触浠诲姟锛堟渶澶?娆★級
4. 娣诲姞瓒呮椂鏈哄埗闃叉Tmux姘镐箙杩愯
"""

import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List


class ImprovedDaemon:
    """鏀硅繘鐨勫畧鎶よ繘绋?""
    
    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.tasks_dir = self.base_dir / "tasks"
        self.scripts_dir = self.base_dir / "scripts"
        self.worktrees_base = self.base_dir / ".." / "worktrees"
    
    def check_all_tasks(self) -> Dict[str, Any]:
        """妫€鏌ユ墍鏈変换鍔＄姸鎬?""
        print(f"\n{'='*60}")
        print(f"馃搳 浠诲姟鐘舵€佹鏌?- {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        task_files = list(self.tasks_dir.glob("*.json"))
        task_ids = set()
        
        for task_file in task_files:
            if not task_file.name.endswith(".heartbeat.json") and not task_file.name.endswith(".log"):
                task_id = task_file.stem
                task_ids.add(task_id)
        
        stats = {
            "total": len(task_ids),
            "running": 0,
            "completed": 0,
            "failed": 0,
            "pr_created": 0,
            "needs_retry": 0,
            "tasks": []
        }
        
        for task_id in sorted(task_ids):
            task_info = self._check_task(task_id)
            stats["tasks"].append(task_info)
            
            status = task_info.get("status")
            if status == "running":
                stats["running"] += 1
            elif status == "completed":
                stats["completed"] += 1
            elif status == "failed":
                stats["failed"] += 1
            elif status == "pr_created":
                stats["pr_created"] += 1
            
            if task_info.get("needs_retry"):
                stats["needs_retry"] += 1
        
        # 鎵撳嵃缁熻
        print(f"馃搱 缁熻:")
        print(f"  - 鎬讳换鍔? {stats['total']}")
        print(f"  - 杩愯涓? {stats['running']}")
        print(f"  - 宸插畬鎴? {stats['completed']}")
        print(f"  - 宸插け璐? {stats['failed']}")
        print(f"  - PR宸插垱寤? {stats['pr_created']}")
        print(f"  - 闇€瑕侀噸璇? {stats['needs_retry']}")
        
        return stats
    
    def _check_task(self, task_id: str) -> Dict[str, Any]:
        """妫€鏌ュ崟涓换鍔?""
        task_file = self.tasks_dir / f"{task_id}.json"
        heartbeat_file = self.tasks_dir / f"{task_id}.heartbeat.json"
        
        result = {
            "task_id": task_id,
            "status": "unknown",
            "needs_retry": False,
            "pr_created": False
        }
        
        # 璇诲彇浠诲姟鏂囦欢
        if task_file.exists():
            try:
                task = json.loads(task_file.read_text(encoding='utf-8'))
                result["agent"] = task.get("agent")
                result["description"] = task.get("description", "")[:50]
                result["pr_created"] = task.get("pr_created", False)
                result["retries"] = task.get("retries", 0)
                result["max_retries"] = task.get("maxRetries", 3)
            except Exception as e:
                result["error"] = str(e)
        
        # 璇诲彇heartbeat鏂囦欢
        if heartbeat_file.exists():
            try:
                heartbeat = json.loads(heartbeat_file.read_text(encoding='utf-8'))
                status = heartbeat.get("status", "unknown")
                exit_code = heartbeat.get("exit_code")
                
                if exit_code is None:
                    result["status"] = "running"
                elif exit_code == 0:
                    result["status"] = "completed"
                    if not result["pr_created"]:
                        result["needs_retry"] = True  # 闇€瑕佸垱寤篜R
                else:
                    result["status"] = "failed"
                    if result["retries"] < result["max_retries"]:
                        result["needs_retry"] = True
            except Exception as e:
                result["error"] = str(e)
        
        # 鎵撳嵃浠诲姟鐘舵€?
        status_icon = {
            "running": "馃攧",
            "completed": "鉁?,
            "failed": "鉂?,
            "pr_created": "馃搵"
        }.get(result["status"], "鉂?)
        
        print(f"{status_icon} {task_id[:40]}")
        print(f"   Agent: {result.get('agent', 'N/A')} | 鐘舵€? {result['status']}")
        if result.get("description"):
            print(f"   鎻忚堪: {result['description']}")
        if result.get("needs_retry"):
            print(f"   鈿狅笍  闇€瑕佸鐞?(閲嶈瘯: {result['retries']}/{result['max_retries']})")
        
        return result
    
    def process_completed_tasks(self, stats: Dict[str, Any]):
        """澶勭悊宸插畬鎴愮殑浠诲姟锛堝垱寤篜R锛?""
        completed_tasks = [t for t in stats["tasks"] if t["status"] == "completed" and not t["pr_created"]]
        
        if not completed_tasks:
            return
        
        print(f"\n{'='*60}")
        print(f"馃搵 澶勭悊宸插畬鎴愮殑浠诲姟 ({len(completed_tasks)})")
        print(f"{'='*60}\n")
        
        for task_info in completed_tasks:
            task_id = task_info["task_id"]
            print(f"\n馃殌 涓轰换鍔″垱寤篜R: {task_id}")
            
            task_file = self.tasks_dir / f"{task_id}.json"
            if task_file.exists():
                task = json.loads(task_file.read_text(encoding='utf-8'))
                self._create_pr_for_task(task_id, task)
    
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
                task_info["pr_created"] = True
                task_info["pr_url"] = pr_url
                task_info["status"] = "pr_created"
                task_info["updatedAt"] = int(datetime.now().timestamp() * 1000)
                task_file.write_text(json.dumps(task_info, indent=2, ensure_ascii=False), encoding='utf-8')
                
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
    
    def run_daemon(self, interval_minutes: int = 5):
        """杩愯瀹堟姢杩涚▼"""
        print(f"\n馃 鏀硅繘鐨凙gent闆嗙兢瀹堟姢杩涚▼鍚姩")
        print(f"   妫€鏌ラ棿闅? {interval_minutes} 鍒嗛挓")
        print(f"   鍔熻兘: 鑷姩鍒涘缓PR + 瓒呮椂鏈哄埗 + 鑷姩閲嶈瘯")
        print(f"   鎸?Ctrl+C 鍋滄\n")
        
        try:
            while True:
                # 妫€鏌ユ墍鏈変换鍔?
                stats = self.check_all_tasks()
                
                # 澶勭悊宸插畬鎴愮殑浠诲姟
                self.process_completed_tasks(stats)
                
                # 绛夊緟
                print(f"\n鈴?绛夊緟 {interval_minutes} 鍒嗛挓...\n")
                time.sleep(interval_minutes * 60)
                
        except KeyboardInterrupt:
            print("\n\n馃憢 瀹堟姢杩涚▼宸插仠姝?)


def main():
    """涓诲嚱鏁?""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="鏀硅繘鐨凙gent闆嗙兢瀹堟姢杩涚▼",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
绀轰緥:
  # 姣?鍒嗛挓妫€鏌ヤ竴娆?
  python improved_daemon.py --interval 5
  
  # 姣?0鍒嗛挓妫€鏌ヤ竴娆?
  python improved_daemon.py --interval 10
"""
    )
    
    parser.add_argument("--interval", type=int, default=5, help="妫€鏌ラ棿闅旓紙鍒嗛挓锛?)
    parser.add_argument("--base-dir", default=".", help="鍩虹鐩綍")
    
    args = parser.parse_args()
    
    daemon = ImprovedDaemon(args.base_dir)
    daemon.run_daemon(args.interval)


if __name__ == "__main__":
    main()

