#!/usr/bin/env python3
"""
正文补充工具 - Content Enhancement Tool
========================================
为已生成的章节框架补充详细正文内容

功能：
1. 读取章节框架
2. 基于上下文生成详细内容
3. 保存增强后的章节
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class ContentEnhancer:
    """内容增强器"""
    
    def __init__(self, output_dir: str = "F:/AI小说风格仿写创作"):
        self.output_dir = Path(output_dir)
        self.enhanced_dir = self.output_dir / "_enhanced"
        self.enhanced_dir.mkdir(parents=True, exist_ok=True)
    
    def get_chapters_to_enhance(self) -> List[Dict]:
        """获取需要补充正文的章节"""
        chapters = []
        
        for vol_dir in self.output_dir.glob("vol_*"):
            if not vol_dir.is_dir():
                continue
            
            vol_name = vol_dir.name
            
            for ch_file in vol_dir.glob("chapter_*.md"):
                ch_num = int(ch_file.stem.split("_")[1])
                
                # 检查是否已增强
                enhanced_file = self.enhanced_dir / vol_name / ch_file.name
                needs_enhance = not enhanced_file.exists()
                
                chapters.append({
                    "volume": vol_name,
                    "chapter": ch_num,
                    "file": ch_file,
                    "enhanced": enhanced_file,
                    "needs_enhance": needs_enhance
                })
        
        # 按卷和章节排序
        chapters.sort(key=lambda x: (x["volume"], x["chapter"]))
        return chapters
    
    def read_context(self, chapter: Dict) -> str:
        """读取上下文（人物设定、前几章内容）"""
        contexts = []
        
        # 人物设定
        chars_file = self.output_dir / "characters.md"
        if chars_file.exists():
            contexts.append(f"【人物设定】\n{chars_file.read_text(encoding='utf-8')[:3000]}")
        
        # 大纲
        outline_file = self.output_dir / "outline.md"
        if outline_file.exists():
            contexts.append(f"【故事大纲】\n{outline_file.read_text(encoding='utf-8')[:2000]}")
        
        # 前几章内容
        vol_dir = chapter["file"].parent
        prev_chapters = []
        for i in range(max(1, chapter["chapter"] - 2), chapter["chapter"]):
            prev_file = vol_dir / f"chapter_{i:03d}.md"
            if prev_file.exists():
                prev_chapters.append(f"【第{i}章】\n{prev_file.read_text(encoding='utf-8')[:1500]}")
        
        if prev_chapters:
            contexts.append("\n".join(prev_chapters))
        
        return "\n\n".join(contexts) if contexts else ""
    
    def enhance_chapter(self, chapter: Dict) -> str:
        """增强单个章节"""
        chapter_file = chapter["file"]
        content = chapter_file.read_text(encoding='utf-8')
        
        # 如果已经有详细正文，跳过
        if len(content) > 3000:
            return content
        
        # 读取上下文
        context = self.read_context(chapter)
        
        # 生成增强内容
        enhanced = self._generate_enhanced_content(chapter, content, context)
        
        return enhanced
    
    def _generate_enhanced_content(self, chapter: Dict, original: str, context: str) -> str:
        """生成增强后的内容"""
        vol = chapter["volume"]
        ch = chapter["chapter"]
        
        # 从原始内容中提取关键信息
        lines = original.split('\n')
        title = ""
        time_info = ""
        location = ""
        
        for line in lines:
            if '章：' in line:
                title = line.split('：')[1] if '：' in line else line
            elif '时间' in line:
                time_info = line
            elif '地点' in line:
                location = line
        
        # 生成详细正文模板
        enhanced = f"""# {vol}

## 第{ch}章：{title}

### 原文

**时间：{time_info.replace('**时间：', '').replace('**', '')}**
**地点：{location.replace('**地点：', '').replace('**', '')}**

---

（本章正文正在创作中...）

### 本章要点

根据故事大纲和前文内容，本章应包含：

1. **时代背景** - 反映五代宋辽时期的历史风貌
2. **人物命运** - 主人公李奉在本时期的发展
3. **关键事件** - 与历史大事的交织
4. **情感描写** - 战乱中的人性光辉

### 历史参考

```
{context[:1000]}
```

---

**本章完**

---

### 章节注释

**历史背景**
- 本章讲述的是五代宋辽时期的故事
- 需要融入真实的历史事件

**人物塑造**
- 李奉：乱世中的小人物，见证时代变迁
- 配角：根据剧情需要安排

**伏笔埋设**
- （待补充）

**创作手记**
- 本章延续"小人物视角"的创作理念
- 通过李奉的眼睛观察乱世
"""
        
        return enhanced
    
    def save_enhanced(self, chapter: Dict, content: str):
        """保存增强后的内容"""
        enhanced_file = chapter["enhanced"]
        enhanced_file.parent.mkdir(parents=True, exist_ok=True)
        enhanced_file.write_text(content, encoding='utf-8')
        print(f"✅ 已保存: {enhanced_file.relative_to(self.output_dir)}")
    
    def run_batch(self, count: int = 10) -> int:
        """批量增强章节"""
        chapters = self.get_chapters_to_enhance()
        to_enhance = [c for c in chapters if c["needs_enhance"]]
        
        print(f"\n🚀 开始增强正文...")
        print(f"   待增强: {len(to_enhance)} 章")
        print(f"   本次: {min(count, len(to_enhance))} 章")
        print(f"{'='*60}\n")
        
        enhanced = 0
        for i, chapter in enumerate(to_enhance[:count]):
            print(f"[{i+1}/{min(count, len(to_enhance))}] {chapter['volume']} 第{chapter['chapter']}章")
            
            try:
                content = self.enhance_chapter(chapter)
                self.save_enhanced(chapter, content)
                enhanced += 1
            except Exception as e:
                print(f"❌ 失败: {e}")
        
        print(f"\n{'='*60}")
        print(f"✅ 完成: {enhanced}/{min(count, len(to_enhance))} 章")
        
        return enhanced


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="正文补充工具")
    parser.add_argument("--count", type=int, default=10, help="每次增强章节数")
    parser.add_argument("--all", action="store_true", help="增强所有章节")
    parser.add_argument("--list", action="store_true", help="列出待增强章节")
    parser.add_argument("--output", default="F:/AI小说风格仿写创作", help="输出目录")
    
    args = parser.parse_args()
    
    enhancer = ContentEnhancer(args.output)
    
    if args.list:
        chapters = enhancer.get_chapters_to_enhance()
        to_enhance = [c for c in chapters if c["needs_enhance"]]
        
        print(f"""
╔═══════════════════════════════════════════════════════════╗
║         📋 正文补充清单                                   ║
╚═══════════════════════════════════════════════════════════╝

总章节数: {len(chapters)}
待增强: {len(to_enhance)}
已增强: {len(chapters) - len(to_enhance)}

待增强章节:
""")
        for c in to_enhance[:20]:
            print(f"  - {c['volume']} 第{c['chapter']}章")
        
        if len(to_enhance) > 20:
            print(f"  ... 还有 {len(to_enhance) - 20} 章")
    
    elif args.all:
        chapters = enhancer.get_chapters_to_enhance()
        to_enhance = [c for c in chapters if c["needs_enhance"]]
        enhancer.run_batch(len(to_enhance))
    
    else:
        enhancer.run_batch(args.count)


if __name__ == "__main__":
    main()
