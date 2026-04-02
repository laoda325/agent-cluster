#!/usr/bin/env python3
"""
DeepSeek Agent 鍚姩鍣?
====================
浣跨敤 DeepSeek API 鎵ц浠诲姟
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any


class DeepSeekAgent:
    """DeepSeek Agent"""
    
    def __init__(self, api_key: str = os.environ.get("DEEPSEEK_API_KEY",""),
                 base_url: str = "https://api.deepseek.com/v1",
                 model: str = "deepseek-chat"):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.tasks_dir = Path("./tasks")
        self.worktrees_base = Path("../worktrees")
    
    def call_api(self, prompt: str, max_tokens: int = 4000) -> str:
        """璋冪敤 DeepSeek API"""
        import requests
        
        # 澧炲己鐨勭郴缁熸彁绀鸿瘝锛岀‘淇濈洿鎺ヨ緭鍑哄唴瀹?
        system_prompt = """浣犳槸涓€涓笓涓氱殑鍐呭鍒涗綔Agent銆備綘鐨勪换鍔℃槸鐩存帴杈撳嚭鎵€瑕佹眰鐨勫唴瀹癸紝鑰屼笉鏄緭鍑哄浣曞垱寤哄唴瀹圭殑璇存槑鎴栧懡浠ゃ€?

閲嶈瑙勫垯锛?
1. 鐩存帴杈撳嚭灏忚鍐呭銆佹枃绔犲唴瀹规垨鍏朵粬鍒涗綔鍐呭
2. 涓嶈杈撳嚭Shell鍛戒护銆乥ash鑴氭湰鎴栨搷浣滆鏄?
3. 涓嶈璇?鎴戝皢鍒涘缓..."鎴?璁╂垜鍏堟鏌ョ幆澧?.."
4. 绔嬪嵆寮€濮嬭緭鍑哄疄闄呭唴瀹?
5. 浣跨敤娓呮櫚鐨凪arkdown鏍煎紡

濡傛灉浠诲姟鏄垱浣滃皬璇达細
- 鐩存帴杈撳嚭灏忚鏍囬鍜屾鏂?
- 浣跨敤绔犺妭鏍囬鍒嗛殧
- 杈撳嚭瀹屾暣鐨勬晠浜嬪唴瀹?

濡傛灉浠诲姟鏄啓浠ｇ爜锛?
- 鐩存帴杈撳嚭浠ｇ爜
- 浣跨敤浠ｇ爜鍧楁牸寮?
- 鍖呭惈蹇呰鐨勬敞閲?""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": 0.8
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=data,
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        else:
            raise Exception(f"API璋冪敤澶辫触: {response.status_code} - {response.text}")
    
    def run_task(self, task_id: str, prompt_file: str, worktree: str) -> Dict[str, Any]:
        """鎵ц浠诲姟"""
        print(f"\n{'='*60}")
        print(f"馃 DeepSeek Agent 鎵ц浠诲姟")
        print(f"浠诲姟ID: {task_id}")
        print(f"{'='*60}\n")
        
        # 璇诲彇鎻愮ず璇?
        prompt_path = Path(prompt_file)
        if not prompt_path.exists():
            return {"success": False, "error": "鎻愮ず璇嶆枃浠朵笉瀛樺湪"}
        
        prompt = prompt_path.read_text(encoding='utf-8')
        print(f"馃摑 璇诲彇鎻愮ず璇? {len(prompt)} 瀛楃")
        
        # 璋冪敤 API
        try:
            print(f"馃攧 璋冪敤 DeepSeek API...")
            result = self.call_api(prompt)
            print(f"鉁?API 璋冪敤鎴愬姛: {len(result)} 瀛楃")
            
            # 淇濆瓨缁撴灉
            output_file = Path(worktree) / "output.md"
            output_file.write_text(result, encoding='utf-8')
            print(f"馃捑 缁撴灉宸蹭繚瀛? {output_file}")
            
            return {
                "success": True,
                "result": result,
                "output_file": str(output_file)
            }
            
        except Exception as e:
            print(f"鉂?API 璋冪敤澶辫触: {e}")
            return {"success": False, "error": str(e)}
    
    def create_pr(self, task_id: str, worktree: str, branch: str) -> Dict[str, Any]:
        """鍒涘缓 PR"""
        worktree_path = Path(worktree)
        
        try:
            # 妫€鏌ユ洿鏀?
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=worktree_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if not result.stdout.strip():
                return {"success": False, "error": "娌℃湁鏈彁浜ょ殑鏇存敼"}
            
            # 娣诲姞骞舵彁浜?
            subprocess.run(["git", "add", "-A"], cwd=worktree_path, check=True, timeout=10)
            subprocess.run(
                ["git", "commit", "-m", f"feat: {task_id}\n\nDeepSeek Agent 鑷姩鐢熸垚"],
                cwd=worktree_path,
                check=True,
                timeout=10
            )
            print(f"鉁?宸叉彁浜や唬鐮?)
            
            # 鎺ㄩ€?
            env = {**os.environ, "GH_TOKEN": "os.environ.get("GH_TOKEN","")"}
            subprocess.run(
                ["git", "push", "origin", branch],
                cwd=worktree_path,
                check=True,
                timeout=30,
                env=env
            )
            print(f"鉁?宸叉帹閫?)
            
            # 鍒涘缓 PR
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
                print(f"鉁?PR 宸插垱寤? {pr_url}")
                return {"success": True, "pr_url": pr_url}
            else:
                return {"success": False, "error": result.stderr}
                
        except Exception as e:
            return {"success": False, "error": str(e)}


def main():
    """涓诲嚱鏁?""
    if len(sys.argv) < 4:
        print("鐢ㄦ硶: python deepseek_agent.py <task_id> <prompt_file> <worktree>")
        print("\n绀轰緥:")
        print("  python deepseek_agent.py task-xxx prompt.md /path/to/worktree")
        sys.exit(1)
    
    task_id = sys.argv[1]
    prompt_file = sys.argv[2]
    worktree = sys.argv[3]
    
    agent = DeepSeekAgent()
    
    # 鎵ц浠诲姟
    result = agent.run_task(task_id, prompt_file, worktree)
    
    if result.get("success"):
        # 鑾峰彇鍒嗘敮鍚?
        import subprocess
        worktree_path = Path(worktree)
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=worktree_path,
            capture_output=True,
            text=True,
            timeout=10
        )
        branch = result.stdout.strip() or "main"
        
        # 鍒涘缓 PR
        pr_result = agent.create_pr(task_id, worktree, branch)
        
        if pr_result.get("success"):
            print(f"\n馃帀 浠诲姟瀹屾垚锛丳R: {pr_result['pr_url']}")
            sys.exit(0)
        else:
            print(f"\n鈿狅笍 浠诲姟瀹屾垚锛屼絾 PR 鍒涘缓澶辫触: {pr_result.get('error')}")
            sys.exit(1)
    else:
        print(f"\n鉂?浠诲姟澶辫触: {result.get('error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()

