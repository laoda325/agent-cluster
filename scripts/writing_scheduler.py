#!/usr/bin/env python3
"""
小说创作任务调度器 - Writing Task Scheduler
============================================
基于 Agent 集群系统调度小说创作任务

功能：
1. 管理创作任务队列
2. 调度 Agent 执行写作任务
3. 追踪创作进度
4. 自动生成章节内容
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml


class WritingTask:
    """创作任务"""
    
    def __init__(self, 
                 task_id: str,
                 volume: str,
                 chapter: int,
                 title: str,
                 description: str = "",
                 status: str = "pending",
                 content: str = ""):
        self.task_id = task_id
        self.volume = volume
        self.chapter = chapter
        self.title = title
        self.description = description
        self.status = status  # pending, writing, review, completed, failed
        self.content = content
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
        self.agent_id = None
        self.retry_count = 0
    
    def to_dict(self) -> Dict:
        return {
            "task_id": self.task_id,
            "volume": self.volume,
            "chapter": self.chapter,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "content": self.content,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "agent_id": self.agent_id,
            "retry_count": self.retry_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'WritingTask':
        task = cls(
            task_id=data["task_id"],
            volume=data["volume"],
            chapter=data["chapter"],
            title=data["title"],
            description=data.get("description", ""),
            status=data.get("status", "pending"),
            content=data.get("content", "")
        )
        task.created_at = data.get("created_at", datetime.now().isoformat())
        task.updated_at = data.get("updated_at", datetime.now().isoformat())
        task.agent_id = data.get("agent_id")
        task.retry_count = data.get("retry_count", 0)
        return task


class WritingScheduler:
    """创作调度器"""
    
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.tasks_file = self.output_dir / ".writing_tasks.json"
        self.tasks: List[WritingTask] = []
        self.load_tasks()
    
    def load_tasks(self):
        """加载任务"""
        if self.tasks_file.exists():
            try:
                with open(self.tasks_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.tasks = [WritingTask.from_dict(t) for t in data]
            except Exception as e:
                print(f"⚠️  加载任务失败: {e}")
                self.tasks = []
        else:
            self.tasks = []
    
    def save_tasks(self):
        """保存任务"""
        self.tasks_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.tasks_file, 'w', encoding='utf-8') as f:
            json.dump([t.to_dict() for t in self.tasks], f, indent=2, ensure_ascii=False)
    
    def add_task(self, task: WritingTask):
        """添加任务"""
        # 检查是否已存在
        for t in self.tasks:
            if t.volume == task.volume and t.chapter == task.chapter:
                print(f"⚠️  任务已存在: {task.volume} 第{task.chapter}章")
                return False
        
        self.tasks.append(task)
        self.save_tasks()
        print(f"✅ 任务已添加: {task.volume} 第{task.chapter}章 - {task.title}")
        return True
    
    def get_task(self, task_id: str) -> Optional[WritingTask]:
        """获取任务"""
        for t in self.tasks:
            if t.task_id == task_id:
                return t
        return None
    
    def get_pending_tasks(self) -> List[WritingTask]:
        """获取待处理任务"""
        return [t for t in self.tasks if t.status == "pending"]
    
    def get_next_task(self) -> Optional[WritingTask]:
        """获取下一个待执行任务"""
        pending = self.get_pending_tasks()
        if pending:
            return sorted(pending, key=lambda t: (t.volume, t.chapter))[0]
        return None
    
    def update_task_status(self, task_id: str, status: str, content: str = None):
        """更新任务状态"""
        task = self.get_task(task_id)
        if task:
            task.status = status
            task.updated_at = datetime.now().isoformat()
            if content:
                task.content = content
            self.save_tasks()
            print(f"✅ 任务状态更新: {task_id} → {status}")
    
    def mark_writing(self, task_id: str, agent_id: str):
        """标记为写作中"""
        task = self.get_task(task_id)
        if task:
            task.status = "writing"
            task.agent_id = agent_id
            task.updated_at = datetime.now().isoformat()
            self.save_tasks()
    
    def mark_completed(self, task_id: str, content: str):
        """标记为已完成"""
        task = self.get_task(task_id)
        if task:
            task.status = "completed"
            task.content = content
            task.updated_at = datetime.now().isoformat()
            self.save_tasks()
            
            # 同时保存到文件
            chapter_file = self.output_dir / task.volume / f"chapter_{task.chapter:03d}.md"
            chapter_file.parent.mkdir(parents=True, exist_ok=True)
            with open(chapter_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ 章节已保存: {chapter_file}")
    
    def mark_failed(self, task_id: str, error: str = ""):
        """标记为失败"""
        task = self.get_task(task_id)
        if task:
            task.retry_count += 1
            if task.retry_count >= 3:
                task.status = "failed"
            else:
                task.status = "pending"  # 重试
            task.updated_at = datetime.now().isoformat()
            self.save_tasks()
            print(f"⚠️  任务失败: {task_id} (重试 {task.retry_count}/3)")
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        stats = {
            "total": len(self.tasks),
            "pending": sum(1 for t in self.tasks if t.status == "pending"),
            "writing": sum(1 for t in self.tasks if t.status == "writing"),
            "completed": sum(1 for t in self.tasks if t.status == "completed"),
            "failed": sum(1 for t in self.tasks if t.status == "failed")
        }
        stats["progress"] = f"{stats['completed']}/{stats['total']}" if stats['total'] > 0 else "0/0"
        return stats


class WritingAgent:
    """写作 Agent"""
    
    def __init__(self, agent_id: str, model: str = "gemini"):
        self.agent_id = agent_id
        self.model = model
        self.task = None
    
    def write_chapter(self, task: WritingTask, context: str) -> str:
        """创作章节"""
        print(f"\n{'='*60}")
        print(f"🤖 Agent {self.agent_id} 正在创作...")
        print(f"📖 {task.volume} 第{task.chapter}章: {task.title}")
        print(f"{'='*60}\n")
        
        # 读取大纲获取章节要求
        outline_file = Path(task.volume) / "outline.md"
        if not outline_file.exists():
            outline_file = Path("F:/AI小说风格仿写创作/outline.md")
        
        # 生成章节内容（模拟，实际需要调用 AI API）
        content = self._generate_content(task, context)
        
        return content
    
    def _generate_content(self, task: WritingTask, context: str) -> str:
        """生成章节内容"""
        # 这里应该调用实际的 AI API
        # 目前返回模板，待集成真实 AI
        
        template = f"""# {task.volume}

## 第{task.chapter}章：{task.title}

### 原文

**时间：{task.description}**
**地点：（待定）**

---

（章节内容待创作...）

本章节基于以下上下文创作：
{context[:500]}...

---

**本章完**

---

### 章节注释

**历史背景**
- （待填充）

**人物塑造**
- （待填充）

**伏笔埋设**
- （待填充）

**创作手记**
- （待填充）
"""
        return template


class WritingOrchestrator:
    """写作编排器"""
    
    def __init__(self, 
                 output_dir: str = "F:/AI小说风格仿写创作",
                 novel_config: str = "./novel-config.yaml"):
        self.output_dir = Path(output_dir)
        self.scheduler = WritingScheduler(output_dir)
        self.config = self._load_config(novel_config)
        self.agent = WritingAgent("agent-001", "gemini")
    
    def _load_config(self, config_path: str) -> Dict:
        """加载配置"""
        config_file = Path(config_path)
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        return {}
    
    def initialize_from_outline(self):
        """从大纲初始化任务"""
        outline_file = self.output_dir / "outline.md"
        if not outline_file.exists():
            print(f"⚠️  大纲文件不存在: {outline_file}")
            return
        
        # 解析大纲，生成任务
        # 这里简化处理，直接根据已知的章节规划创建任务
        
        volumes = [
            {
                "name": "vol_907_第一卷：五代乱世",
                "chapters": list(range(1, 21))  # 1-20章
            },
            {
                "name": "vol_960_第二卷：北宋崛起", 
                "chapters": list(range(1, 16))  # 1-15章
            },
            {
                "name": "vol_979_第三卷：宋辽博弈",
                "chapters": list(range(1, 16))  # 1-15章
            }
        ]
        
        print("\n📋 从大纲初始化任务队列...")
        
        for vol in volumes:
            vol_dir = self.output_dir / vol["name"]
            vol_dir.mkdir(parents=True, exist_ok=True)
            
            # 检查已完成的章节
            existing_chapters = set()
            for f in vol_dir.glob("chapter_*.md"):
                try:
                    chapter_num = int(f.stem.split("_")[1])
                    existing_chapters.add(chapter_num)
                except:
                    pass
            
            for ch in vol["chapters"]:
                if ch not in existing_chapters:
                    task_id = f"task_{vol['name']}_ch{ch:03d}"
                    task = WritingTask(
                        task_id=task_id,
                        volume=vol["name"],
                        chapter=ch,
                        title=f"第{ch}章",
                        description=f"待创作章节，第{ch}章"
                    )
                    self.scheduler.add_task(task)
        
        print(f"\n✅ 任务队列初始化完成")
    
    def execute_next(self, context: str = "") -> Optional[WritingTask]:
        """执行下一个任务"""
        task = self.scheduler.get_next_task()
        if not task:
            print("📭 没有待执行的任务")
            return None
        
        # 标记为写作中
        self.scheduler.mark_writing(task.task_id, self.agent.agent_id)
        
        # 获取历史上下文
        if not context:
            context = self._get_context(task)
        
        try:
            # Agent 创作
            content = self.agent.write_chapter(task, context)
            
            # 保存结果
            self.scheduler.mark_completed(task.task_id, content)
            
            return task
            
        except Exception as e:
            print(f"❌ 创作失败: {e}")
            self.scheduler.mark_failed(task.task_id, str(e))
            return None
    
    def _get_context(self, task: WritingTask) -> str:
        """获取上下文"""
        contexts = []
        
        # 人物设定
        chars_file = self.output_dir / "characters.md"
        if chars_file.exists():
            contexts.append(f"【人物设定】\n{chars_file.read_text(encoding='utf-8')[:2000]}")
        
        # 前几章内容（如果有）
        vol_dir = self.output_dir / task.volume
        prev_chapters = []
        for ch in range(max(1, task.chapter - 2), task.chapter):
            ch_file = vol_dir / f"chapter_{ch:03d}.md"
            if ch_file.exists():
                prev_chapters.append(f"【第{ch}章】\n{ch_file.read_text(encoding='utf-8')[:1000]}")
        
        if prev_chapters:
            contexts.append("\n".join(prev_chapters))
        
        return "\n\n".join(contexts) if contexts else ""
    
    def run_batch(self, count: int = 5, context: str = ""):
        """批量执行任务"""
        print(f"\n🚀 开始批量执行 {count} 个任务...")
        print(f"{'='*60}\n")
        
        completed = 0
        for i in range(count):
            task = self.execute_next(context)
            if task:
                completed += 1
                print(f"\n✅ 完成: {task.volume} 第{task.chapter}章\n")
            else:
                break
        
        stats = self.scheduler.get_stats()
        print(f"\n{'='*60}")
        print(f"📊 批量执行完成")
        print(f"   完成: {completed}/{count}")
        print(f"   总进度: {stats['progress']}")
        print(f"{'='*60}")
        
        return completed


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="小说创作任务调度器")
    parser.add_argument("--init", action="store_true", help="初始化任务队列")
    parser.add_argument("--next", action="store_true", help="执行下一个任务")
    parser.add_argument("--batch", type=int, default=0, help="批量执行 N 个任务")
    parser.add_argument("--status", action="store_true", help="查看状态")
    parser.add_argument("--output", default="F:/AI小说风格仿写创作", help="输出目录")
    
    args = parser.parse_args()
    
    orchestrator = WritingOrchestrator(args.output)
    
    if args.init:
        orchestrator.initialize_from_outline()
    
    if args.next:
        orchestrator.execute_next()
    
    if args.batch > 0:
        orchestrator.run_batch(args.batch)
    
    if args.status:
        stats = orchestrator.scheduler.get_stats()
        print(f"""
╔═══════════════════════════════════════════════════════════╗
║         📊 创作进度报告                                   ║
╚═══════════════════════════════════════════════════════════╝

总任务数: {stats['total']}
待创作:  {stats['pending']}
创作中:  {stats['writing']}
已完成:  {stats['completed']}
失败:    {stats['failed']}

进度:    {stats['progress']}
        """)
    
    if not (args.init or args.next or args.batch or args.status):
        print("""
╔═══════════════════════════════════════════════════════════╗
║         📖 小说创作任务调度器                              ║
╚═══════════════════════════════════════════════════════════╝

用法:
  --init     从大纲初始化任务队列
  --next     执行下一个任务
  --batch N  批量执行 N 个任务
  --status   查看创作进度

示例:
  python writing_scheduler.py --init
  python writing_scheduler.py --next
  python writing_scheduler.py --batch 5
  python writing_scheduler.py --status
        """)


if __name__ == "__main__":
    main()
