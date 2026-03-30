#!/usr/bin/env python3
"""
小说创作编排层 - Novel Writing Orchestrator
============================================
专门用于《五代十国宋》历史小说的创作编排

功能：
1. 读取历史事件上下文
2. 管理人物设定
3. 管理世界观设定
4. 规划故事大纲
5. 编排章节创作任务
6. 追踪创作进度
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml


class NovelConfig:
    """小说配置"""
    
    def __init__(self, config_path: str = "./novel-config.yaml"):
        self.config_path = Path(config_path)
        self.load()
    
    def load(self):
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f) or {}
        else:
            self.config = {}
    
    def get(self, key: str, default=None):
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        return value


class HistoricalContextReader:
    """历史上下文读取器"""
    
    def __init__(self, config: NovelConfig):
        self.config = config
        self.events_file = Path(config.get('context.historical_events_file', ''))
    
    def read_events(self) -> str:
        """读取历史事件"""
        if not self.events_file.exists():
            return "（未找到历史事件文件）"
        
        with open(self.events_file, 'r', encoding='utf-8') as f:
            return f.read()
    
    def parse_events_by_period(self) -> Dict[str, List[str]]:
        """按时期解析历史事件"""
        content = self.read_events()
        periods = {
            '五代': [],
            '十国': [],
            '北宋初期': [],
            '宋辽对峙': []
        }
        
        current_period = None
        lines = content.split('\n')
        
        for line in lines:
            if '一、五代的更替' in line or '907' in line:
                current_period = '五代'
            elif '二、十国' in line:
                current_period = '十国'
            elif '三、北宋统一' in line or '960' in line:
                current_period = '北宋初期'
            elif '四、北宋的主要' in line or '979' in line:
                current_period = '宋辽对峙'
            elif '五、北宋建立后' in line:
                current_period = '北宋初期'
            elif '六、北宋建立后' in line:
                current_period = '宋辽对峙'
            
            if current_period and line.strip().startswith('-'):
                periods[current_period].append(line.strip())
        
        return periods


class CharacterManager:
    """人物管理器"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.characters_file = output_dir / "characters.md"
    
    def create_protagonist_template(self) -> str:
        """创建主人公模板"""
        return """# 人物设定

## 主人公

### 基本信息
- **姓名**：（待定）
- **出身**：普通农民/士兵/商人家庭
- **时代**：907年（五代开始）~ 1005年（澶渊之盟）
- **身份**：小人物，无显赫背景

### 家族背景
- 祖籍：（待定）
- 家族世代：以农耕/手艺/小商业为生
- 家族特点：平凡但有韧性

### 人物弧光
- **起点**：乱世中的普通百姓
- **发展**：被时代洪流裹挟，经历各种事件
- **终点**：见证新秩序的建立

### 性格特点
- （待填充）

### 命运节点
- （待填充）

## 配角

### 家族成员
- （待填充）

### 历史人物（客串）
- （待填充）

### 虚构人物
- （待填充）
"""
    
    def create_characters(self):
        """创建人物设定文件"""
        if not self.characters_file.exists():
            with open(self.characters_file, 'w', encoding='utf-8') as f:
                f.write(self.create_protagonist_template())
            print(f"✅ 人物设定文件已创建: {self.characters_file}")
        else:
            print(f"⚠️  人物设定文件已存在: {self.characters_file}")


class WorldSettingManager:
    """世界观设定管理器"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.world_file = output_dir / "world_setting.md"
    
    def create_world_template(self) -> str:
        """创建世界观模板"""
        return """# 世界观设定

## 时代背景

### 五代十国（907-960）
- **时间跨度**：约53年
- **政治特点**：朝代更替频繁，藩镇割据
- **经济状况**：战乱频繁，民生艰难
- **文化特点**：文人地位下降，武人当道

### 北宋初期（960-979）
- **时间跨度**：约19年
- **政治特点**：宋太祖、太宗相继即位
- **军事行动**：统一战争
- **社会变化**：开始稳定

### 宋辽对峙（979-1005）
- **时间跨度**：约26年
- **政治特点**：宋辽长期对峙
- **重大事件**：高梁河之战、雍熙北伐、澶渊之盟
- **社会变化**：和平到来

## 地理设定

### 主要地区
- **中原地区**：政治中心
- **北方边境**：与契丹接壤
- **南方地区**：十国割据

## 社会阶层

### 主要阶层
- 皇室/贵族
- 文官集团
- 武将/藩镇
- 普通百姓
- 商人（地位逐渐上升）
- 农民（最底层）

## 文化特色

### 服饰
- （待填充）

### 饮食
- （待填充）

### 民俗
- （待填充）
"""
    
    def create_world_setting(self):
        """创建世界观设定文件"""
        if not self.world_file.exists():
            with open(self.world_file, 'w', encoding='utf-8') as f:
                f.write(self.create_world_template())
            print(f"✅ 世界观设定文件已创建: {self.world_file}")
        else:
            print(f"⚠️  世界观设定文件已存在: {self.world_file}")


class OutlineManager:
    """大纲管理器"""
    
    def __init__(self, config: NovelConfig, output_dir: Path):
        self.config = config
        self.output_dir = output_dir
        self.outline_file = output_dir / "outline.md"
    
    def create_outline(self, events: Dict[str, List[str]]) -> str:
        """创建整体大纲"""
        volumes = self.config.get('output.volumes', [])
        
        outline = """# 《五代十国宋》整体大纲

## 主题
小人物的视角见证五代十国宋的兴衰更替

## 结构
全书分为三卷，约50章

"""
        
        for i, vol in enumerate(volumes, 1):
            outline += f"""### 第{i}卷：{vol['name']}
- **时间跨度**：{vol['period']}
- **预计章节**：{vol['chapters']}章
- **主要内容**：
  - （待填充）

"""
        
        outline += """## 主人公命运线

### 起点（907年）
- 主人公出生于普通家庭
- 唐朝灭亡，战乱开始
- 家族被迫流离

### 发展（五代时期）
- 家族辗转于各个割据政权之间
- 主人公成长，经历多次政权更替
- 见证各种历史事件

### 高潮（北宋建立）
- 赵匡胤陈桥兵变
- 主人公见证新朝建立
- 家族命运改变

### 终点（1005年）
- 澶渊之盟
- 宋辽和平
- 主人公晚年见证和平

## 关键情节点

### 第一卷关键点
"""
        
        for event in events.get('五代', [])[:5]:
            outline += f"- {event}\n"
        
        outline += """
### 第二卷关键点
"""
        
        for event in events.get('北宋初期', [])[:5]:
            outline += f"- {event}\n"
        
        outline += """
### 第三卷关键点
"""
        
        for event in events.get('宋辽对峙', [])[:5]:
            outline += f"- {event}\n"
        
        return outline
    
    def create_outline_file(self, events: Dict[str, List[str]]):
        """创建大纲文件"""
        outline = self.create_outline(events)
        with open(self.outline_file, 'w', encoding='utf-8') as f:
            f.write(outline)
        print(f"✅ 整体大纲已创建: {self.outline_file}")


class ChapterManager:
    """章节管理器"""
    
    def __init__(self, config: NovelConfig, output_dir: Path):
        self.config = config
        self.output_dir = output_dir
    
    def create_volume_dirs(self):
        """创建分卷目录"""
        volumes = self.config.get('output.volumes', [])
        
        for vol in volumes:
            vol_dir = self.output_dir / f"vol_{vol['period'].split('-')[0]}_{vol['name']}"
            vol_dir.mkdir(parents=True, exist_ok=True)
            print(f"✅ 分卷目录已创建: {vol_dir}")
    
    def create_chapter_template(self, chapter_num: int, vol_name: str) -> str:
        """创建章节模板"""
        return f"""# 第{chapter_num}章

## 基本信息
- **卷名**：
- **章节号**：{chapter_num}
- **时间**：（待定）
- **地点**：（待定）

## 大纲
（待填充）

## 正文

（待创作）

## 创作记录
- 创建时间：
- 状态：草稿/完成
- 字数：
"""


class NovelOrchestrator:
    """小说创作编排层主控制器"""
    
    def __init__(self, 
                 novel_config: str = "./novel-config.yaml",
                 base_output: str = None):
        
        self.config = NovelConfig(novel_config)
        
        # 设置输出目录
        if base_output:
            self.output_dir = Path(base_output)
        else:
            output_path = self.config.get('output.base_dir', './novel_output')
            self.output_dir = Path(output_path)
        
        # 初始化各模块
        self.context_reader = HistoricalContextReader(self.config)
        self.character_mgr = CharacterManager(self.output_dir)
        self.world_mgr = WorldSettingManager(self.output_dir)
        self.outline_mgr = OutlineManager(self.config, self.output_dir)
        self.chapter_mgr = ChapterManager(self.config, self.output_dir)
    
    def setup_project(self):
        """初始化项目"""
        print("""
╔═══════════════════════════════════════════════════════════╗
║         《五代十国宋》小说创作编排层 - 初始化               ║
╚═══════════════════════════════════════════════════════════╝
        """)
        
        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 输出目录: {self.output_dir}")
        
        # 读取历史事件
        print("\n📖 读取历史事件上下文...")
        events = self.context_reader.parse_events_by_period()
        print(f"   - 五代事件: {len(events.get('五代', []))} 条")
        print(f"   - 北宋初期事件: {len(events.get('北宋初期', []))} 条")
        print(f"   - 宋辽对峙事件: {len(events.get('宋辽对峙', []))} 条")
        
        # 创建人物设定
        print("\n👤 创建人物设定...")
        self.character_mgr.create_characters()
        
        # 创建世界观设定
        print("\n🌍 创建世界观设定...")
        self.world_mgr.create_world_setting()
        
        # 创建大纲
        print("\n📝 创建整体大纲...")
        self.outline_mgr.create_outline_file(events)
        
        # 创建分卷目录
        print("\n📚 创建分卷目录...")
        self.chapter_mgr.create_volume_dirs()
        
        print("\n" + "="*60)
        print("✅ 项目初始化完成！")
        print("="*60)
        
        return {
            'output_dir': str(self.output_dir),
            'events_count': {
                'five_dynasties': len(events.get('五代', [])),
                'early_song': len(events.get('北宋初期', [])),
                'song_liao': len(events.get('宋辽对峙', []))
            }
        }
    
    def get_historical_context(self) -> str:
        """获取历史上下文"""
        return self.context_reader.read_events()
    
    def get_project_status(self) -> Dict:
        """获取项目状态"""
        status = {
            'output_dir': str(self.output_dir),
            'files': {},
            'ready': True
        }
        
        # 检查各文件
        files_to_check = [
            ('characters', '人物设定'),
            ('world_setting', '世界观'),
            ('outline', '大纲')
        ]
        
        for key, name in files_to_check:
            if key == 'characters':
                status['files'][name] = self.character_mgr.characters_file.exists()
            elif key == 'world_setting':
                status['files'][name] = self.world_mgr.world_file.exists()
            elif key == 'outline':
                status['files'][name] = self.outline_mgr.outline_file.exists()
        
        return status
    
    def generate_chapter_prompt(self, 
                                chapter_num: int, 
                                volume: str,
                                historical_context: str) -> str:
        """生成章节创作 Prompt"""
        config = self.config
        prompt_config = config.get('prompts.chapter_content', {})
        
        template = prompt_config.get('template', '')
        system = prompt_config.get('system', '')
        
        # 填充模板
        prompt = template.format(
            chapter=chapter_num,
            outline='（待提供大纲）',
            historical_context=historical_context[:2000],
            chapter_time='（待定）',
            chapter_location='（待定）'
        )
        
        return f"{system}\n\n{prompt}"


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="《五代十国宋》小说创作编排层")
    parser.add_argument("--setup", action="store_true", help="初始化项目")
    parser.add_argument("--status", action="store_true", help="查看项目状态")
    parser.add_argument("--context", action="store_true", help="查看历史上下文")
    parser.add_argument("--prompt", type=int, help="生成指定章节的创作 Prompt")
    parser.add_argument("--config", default="./novel-config.yaml", help="配置文件")
    parser.add_argument("--output", help="输出目录")
    
    args = parser.parse_args()
    
    orchestrator = NovelOrchestrator(args.config, args.output)
    
    if args.setup:
        result = orchestrator.setup_project()
        print("\n📊 初始化结果:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif args.status:
        status = orchestrator.get_project_status()
        print("\n📊 项目状态:")
        print(json.dumps(status, indent=2, ensure_ascii=False))
    
    elif args.context:
        context = orchestrator.get_historical_context()
        print("\n📖 历史上下文:")
        print(context[:2000] + "..." if len(context) > 2000 else context)
    
    elif args.prompt:
        context = orchestrator.get_historical_context()
        prompt = orchestrator.generate_chapter_prompt(args.prompt, "第一卷", context)
        print(f"\n📝 第{args.prompt}章创作 Prompt:")
        print(prompt)
    
    else:
        print("""
╔═══════════════════════════════════════════════════════════╗
║         《五代十国宋》小说创作编排层                        ║
╚═══════════════════════════════════════════════════════════╝

用法:
  --setup     初始化项目（创建目录和基础文件）
  --status    查看项目状态
  --context   查看历史上下文
  --prompt N  生成第N章的创作Prompt

示例:
  python novel_orchestrator.py --setup
  python novel_orchestrator.py --status
  python novel_orchestrator.py --prompt 1
        """)


if __name__ == "__main__":
    main()
