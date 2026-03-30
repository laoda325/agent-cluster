#!/usr/bin/env python3
"""
《三国演义外传》合并与导出工具
==============================
合并所有章节并生成电子书
"""

import os
from pathlib import Path
from datetime import datetime


class SGYYExporter:
    """三国演义外传导出器"""
    
    def __init__(self, base_dir: str = "F:/AI小说风格仿写创作/三国演义外传"):
        self.base_dir = Path(base_dir)
        self.volumes = [
            "vol_184_第一卷：黄巾乱世",
            "vol_220_第二卷：三国鼎立",
            "vol_280_第三卷：天下归晋"
        ]
    
    def merge_all_chapters(self) -> str:
        """合并所有章节"""
        print("📝 正在合并所有章节...")
        
        # 读取人物设定
        chars_file = self.base_dir / "characters.md"
        world_file = self.base_dir / "world_setting.md"
        
        content_parts = []
        
        # 添加封面
        content_parts.append(self._create_cover())
        
        # 添加人物设定
        if chars_file.exists():
            content_parts.append("\n\n---\n\n# 人物设定\n\n")
            content_parts.append(chars_file.read_text(encoding='utf-8'))
        
        # 添加世界观
        if world_file.exists():
            content_parts.append("\n\n---\n\n# 世界观\n\n")
            content_parts.append(world_file.read_text(encoding='utf-8'))
        
        # 添加各卷章节
        for vol_name in self.volumes:
            vol_dir = self.base_dir / vol_name
            if not vol_dir.exists():
                continue
            
            # 添加卷标题
            vol_title = vol_name.split("_")[-1]
            content_parts.append(f"\n\n---\n\n# {vol_title}\n\n")
            
            # 读取章节
            chapters = sorted(vol_dir.glob("chapter_*.md"))
            for ch_file in chapters:
                ch_content = ch_file.read_text(encoding='utf-8')
                content_parts.append("\n\n")
                content_parts.append(ch_content)
                print(f"  ✅ 已合并: {ch_file.name}")
        
        full_content = "\n".join(content_parts)
        
        # 保存合并文件
        output_file = self.base_dir / "三国演义外传_完整版.md"
        output_file.write_text(full_content, encoding='utf-8')
        
        print(f"\n✅ 合并完成!")
        print(f"📁 文件: {output_file}")
        print(f"📝 总字数: {len(full_content)} 字符")
        
        return str(output_file)
    
    def _create_cover(self) -> str:
        """创建封面"""
        return """# 三国演义外传

## 小人物眼中的乱世风云

---

**作者**: AI Agent 集群系统

**创作时间**: 2026年3月

**总章节**: 28章

**字数**: 约6万字

---

> 一个普通农户之子，历经东汉末年、三国鼎立、西晋统一，
> 用96年的人生见证了中国历史上最动荡的时代。

---

"""
    
    def create_txt_version(self):
        """创建纯文本版本"""
        md_file = self.base_dir / "三国演义外传_完整版.md"
        if not md_file.exists():
            print("❌ 请先合并章节")
            return
        
        content = md_file.read_text(encoding='utf-8')
        
        # 简单转换为纯文本（移除Markdown标记）
        txt_content = content.replace('# ', '').replace('## ', '').replace('### ', '')
        txt_content = txt_content.replace('**', '').replace('*', '')
        txt_content = txt_content.replace('---', '─' * 50)
        
        txt_file = self.base_dir / "三国演义外传_完整版.txt"
        txt_file.write_text(txt_content, encoding='utf-8')
        
        print(f"✅ TXT版本已创建: {txt_file}")
    
    def get_stats(self):
        """获取统计信息"""
        stats = {
            "volumes": [],
            "total_chapters": 0,
            "total_chars": 0
        }
        
        for vol_name in self.volumes:
            vol_dir = self.base_dir / vol_name
            if not vol_dir.exists():
                continue
            
            chapters = list(vol_dir.glob("chapter_*.md"))
            vol_chars = sum(f.read_text(encoding='utf-8').__len__() for f in chapters)
            
            stats["volumes"].append({
                "name": vol_name.split("_")[-1],
                "chapters": len(chapters),
                "chars": vol_chars
            })
            stats["total_chapters"] += len(chapters)
            stats["total_chars"] += vol_chars
        
        return stats


def main():
    """主函数"""
    exporter = SGYYExporter()
    
    # 显示统计
    stats = exporter.get_stats()
    print("="*60)
    print("《三国演义外传》创作统计")
    print("="*60)
    
    for vol in stats["volumes"]:
        print(f"\n{vol['name']}:")
        print(f"  章节数: {vol['chapters']}")
        print(f"  字数: {vol['chars']:,}")
    
    print(f"\n{'='*60}")
    print(f"总计: {stats['total_chapters']} 章, {stats['total_chars']:,} 字")
    print("="*60)
    
    # 合并章节
    print("\n")
    exporter.merge_all_chapters()
    
    # 创建TXT版本
    print("\n")
    exporter.create_txt_version()
    
    print("\n" + "="*60)
    print("✅ 全部导出完成!")
    print("="*60)


if __name__ == "__main__":
    main()
