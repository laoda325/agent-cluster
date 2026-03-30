#!/usr/bin/env python3
"""
上下文收集器 - 从多个数据源自动收集业务上下文

数据源：
1. Obsidian 会议记录
2. 生产数据库（客户配置、使用记录）
3. 任务历史
4. 成功/失败模式库
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml

# 添加脚本目录到路径
SCRIPT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

from scripts.orchestrator import (
    Orchestrator, 
    ObsidianReader, 
    DatabaseConnector, 
    AdminAPIClient,
    ConfigLoader
)


class ContextCollector:
    """上下文收集器"""
    
    def __init__(self, config_path: str = "./integrations-config.yaml"):
        self.config = ConfigLoader(config_path)
        self.orchestrator = Orchestrator(config_path)
    
    def collect_all(self, days_back: int = 7) -> Dict[str, Any]:
        """收集所有上下文"""
        result = {
            'collected_at': datetime.now().isoformat(),
            'sources': {},
            'summary': {}
        }
        
        # 1. 会议记录
        result['sources']['obsidian'] = self._collect_obsidian(days_back)
        
        # 2. 数据库
        result['sources']['database'] = self._collect_database()
        
        # 3. 任务历史
        result['sources']['tasks'] = self._collect_task_history()
        
        # 4. 生成摘要
        result['summary'] = self._generate_summary(result['sources'])
        
        return result
    
    def _collect_obsidian(self, days_back: int) -> Dict[str, Any]:
        """收集 Obsidian 会议记录"""
        reader = ObsidianReader(self.config)
        meetings = reader.find_meetings(days_back)
        
        return {
            'total': len(meetings),
            'recent': [
                {
                    'name': m['name'],
                    'modified': m['modified'],
                    'summary': m['summary'][:200]
                }
                for m in meetings[:10]
            ]
        }
    
    def _collect_database(self) -> Dict[str, Any]:
        """收集数据库信息"""
        db = DatabaseConnector(self.config)
        
        # 测试连接
        connected = db.connect()
        if not connected:
            return {'connected': False, 'error': '未启用或连接失败'}
        
        # 查询示例
        customers = db.query("SELECT id, email, status FROM customers LIMIT 10")
        
        return {
            'connected': True,
            'sample_customers': customers,
            'allowed_tables': list(db.allowed_tables)
        }
    
    def _collect_task_history(self) -> Dict[str, Any]:
        """收集任务历史"""
        tasks_dir = SCRIPT_DIR / "tasks"
        history = []
        
        if tasks_dir.exists():
            for task_file in tasks_dir.glob("*.json"):
                try:
                    with open(task_file, 'r', encoding='utf-8') as f:
                        task = json.load(f)
                        history.append({
                            'id': task.get('id'),
                            'status': task.get('status'),
                            'agent': task.get('agent'),
                            'description': task.get('description', '')[:100]
                        })
                except Exception:
                    pass
        
        return {
            'total': len(history),
            'recent': history[-10:]
        }
    
    def _generate_summary(self, sources: Dict) -> Dict[str, Any]:
        """生成上下文摘要"""
        summary = {
            'meeting_count': sources.get('obsidian', {}).get('total', 0),
            'db_connected': sources.get('database', {}).get('connected', False),
            'task_count': sources.get('tasks', {}).get('total', 0),
            'ready': False
        }
        
        # 判断是否准备好
        summary['ready'] = (
            summary['meeting_count'] > 0 or 
            summary['db_connected'] or 
            summary['task_count'] > 0
        )
        
        return summary
    
    def search_context(self, keyword: str) -> List[Dict[str, Any]]:
        """搜索上下文"""
        results = []
        
        # 搜索 Obsidian
        reader = ObsidianReader(self.config)
        notes = reader.search_notes(keyword)
        for note in notes:
            results.append({
                'source': 'obsidian',
                'name': note['name'],
                'content': note['content'][:500],
                'relevance': 'high' if keyword.lower() in note['content'].lower() else 'medium'
            })
        
        return results


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="上下文收集器")
    parser.add_argument("--days", type=int, default=7, help="回溯天数")
    parser.add_argument("--search", type=str, help="搜索关键词")
    parser.add_argument("--config", default="./integrations-config.yaml", help="配置文件")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    
    args = parser.parse_args()
    
    collector = ContextCollector(args.config)
    
    if args.search:
        # 搜索模式
        results = collector.search_context(args.search)
        if args.json:
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            print(f"\n🔍 搜索 '{args.search}' 结果:\n")
            for r in results:
                print(f"  [{r['source']}] {r['name']} ({r['relevance']})")
                print(f"  {r['content'][:150]}...")
                print()
    else:
        # 收集模式
        context = collector.collect_all(args.days)
        
        if args.json:
            print(json.dumps(context, indent=2, ensure_ascii=False))
        else:
            print(f"""
╔═══════════════════════════════════════════════════════════╗
║           上下文收集报告                                  ║
╚═══════════════════════════════════════════════════════════╝

收集时间: {context['collected_at']}
数据源状态:
  - Obsidian: {context['summary']['meeting_count']} 条会议记录
  - 数据库:    {'已连接' if context['summary']['db_connected'] else '未连接'}
  - 任务历史:  {context['summary']['task_count']} 个任务

准备就绪: {'✅ 是' if context['summary']['ready'] else '❌ 否'}

最近的会议记录:
""")
            for m in context['sources']['obsidian']['recent'][:5]:
                print(f"  📝 {m['name']} ({m['modified'][:10]})")
                print(f"     {m['summary'][:80]}...")
                print()
            
            print("最近的任务:")
            for t in context['sources']['tasks']['recent'][-5:]:
                print(f"  📋 {t['id'][:40]}... → {t['status']}")


if __name__ == "__main__":
    main()
