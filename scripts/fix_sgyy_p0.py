#!/usr/bin/env python3
"""
《三国演义外传》P0级别问题自动修复脚本
========================================
自动修复必须修改的问题
"""

import re
from pathlib import Path


class SGYYFixer:
    """三国演义外传修复器"""
    
    def __init__(self, base_dir: str = "F:/AI小说风格仿写创作/三国演义外传"):
        self.base_dir = Path(base_dir)
        self.fixes_applied = []
    
    def fix_chapter_3_language(self):
        """修复第3章时代用语"""
        ch3_file = self.base_dir / "vol_184_第一卷：黄巾乱世" / "chapter_003.md"
        if not ch3_file.exists():
            print("❌ 第3章文件不存在")
            return
        
        content = ch3_file.read_text(encoding='utf-8')
        
        # 修复1: "这世道不太平啊" → "今岁饥馑，民不聊生"
        if "这世道不太平啊" in content:
            content = content.replace(
                "这世道不太平啊",
                "今岁饥馑，民不聊生"
            )
            self.fixes_applied.append("第3章: '这世道不太平啊' → '今岁饥馑，民不聊生'")
        
        # 修复2: 增加更古朴的表达
        content = content.replace(
            "昨儿个城里来的货郎说",
            "昨日城中货郎至"
        )
        
        ch3_file.write_text(content, encoding='utf-8')
        print("✅ 第3章用语修复完成")
    
    def fix_chapter_7_language(self):
        """修复第7章时代用语"""
        ch7_file = self.base_dir / "vol_184_第一卷：黄巾乱世" / "chapter_007.md"
        if not ch7_file.exists():
            print("❌ 第7章文件不存在")
            return
        
        content = ch7_file.read_text(encoding='utf-8')
        
        # 修复: "听说贼人专抢粮种" → "闻黄巾贼寇劫掠粮秣"
        if "听说贼人专抢粮种" in content:
            content = content.replace(
                "听说贼人专抢粮种",
                "闻黄巾贼寇劫掠粮秣"
            )
            self.fixes_applied.append("第7章: '听说贼人专抢粮种' → '闻黄巾贼寇劫掠粮秣'")
        
        ch7_file.write_text(content, encoding='utf-8')
        print("✅ 第7章用语修复完成")
    
    def fix_chapter_10_transition(self):
        """修复第10章结尾过渡"""
        ch10_file = self.base_dir / "vol_184_第一卷：黄巾乱世" / "chapter_010.md"
        if not ch10_file.exists():
            print("❌ 第10章文件不存在")
            return
        
        content = ch10_file.read_text(encoding='utf-8')
        
        # 检查是否已有结尾
        if "天下三分了。可庄稼人脚下的土地，从来都是一整片。" in content:
            # 在结尾前增加过渡段落
            old_ending = "天下三分了。可庄稼人脚下的土地，从来都是一整片。"
            new_ending = """天下三分了。可庄稼人脚下的土地，从来都是一整片。

张翼站在田埂上，望着三个方向的 horizon。北边是曹丕的魏国，西边是刘备的汉国，东边是孙权的吴国。三个皇帝，三个年号，三种律法。可太阳升起时，照耀的还是同一片天；雨水落下时，滋润的还是同一块地。

他弯腰捡起一块土坷垃，在手心里攥碎。

"分吧，"他轻声说，"分久了，总要合的。"

远处传来儿子的呼喊声，张翼应了一声，扛起锄头往家走。炊烟从村里袅袅升起，王氏站在院门口招手。这是建安二十五年的秋天，东汉的最后一年。而属于三国的时代，即将开始。"""
            
            content = content.replace(old_ending, new_ending)
            self.fixes_applied.append("第10章: 增加结尾过渡段落")
        
        ch10_file.write_text(content, encoding='utf-8')
        print("✅ 第10章过渡修复完成")
    
    def fix_chapter_12_language(self):
        """修复第12章时代用语"""
        ch12_file = self.base_dir / "vol_220_第二卷：三国鼎立" / "chapter_002.md"
        if not ch12_file.exists():
            print("❌ 第12章文件不存在")
            return
        
        content = ch12_file.read_text(encoding='utf-8')
        
        # 修复: "以后还会打仗吗？" → "此后干戈，可复起乎？"
        if "以后还会打仗吗？" in content:
            content = content.replace(
                "以后还会打仗吗？",
                "此后干戈，可复起乎？"
            )
            self.fixes_applied.append("第12章: '以后还会打仗吗？' → '此后干戈，可复起乎？'")
        
        ch12_file.write_text(content, encoding='utf-8')
        print("✅ 第12章用语修复完成")
    
    def add_chapter_4_conflict(self):
        """第4章增加逃难冲突场景"""
        ch4_file = self.base_dir / "vol_184_第一卷：黄巾乱世" / "chapter_004.md"
        if not ch4_file.exists():
            print("❌ 第4章文件不存在")
            return
        
        content = ch4_file.read_text(encoding='utf-8')
        
        # 检查是否已有冲突场景
        if "黄巾贼" in content and "芦苇丛" not in content:
            # 在逃难段落中增加冲突场景
            insert_point = "张翼一家在逃难途中"
            if insert_point in content:
                conflict_scene = """

转过山坳，忽闻前方哭喊声大作。张老三一把拽住儿子，躲进路边的芦苇丛。只见十几个头裹黄巾的汉子，正围着一辆牛车哄抢。车上一对老夫妇哭喊着求饶，被一脚踹翻在地。

张翼浑身发抖，却见父亲从怀里摸出一把柴刀——那是他砍柴用的，刃口早已卷了。

"爹？"

"别出声。"张老三的声音低得几乎听不见，"咱们只有三个人，他们有十几个。"

张翼攥紧拳头，指甲深深掐进掌心。他看着那些黄巾贼把老夫妇的粮食搬空，看着他们把牛牵走，看着老夫妇跪在地上嚎啕大哭。

他什么也做不了。

那一刻，张翼第一次明白了什么是乱世。

"""
                content = content.replace(insert_point, conflict_scene + insert_point)
                self.fixes_applied.append("第4章: 增加逃难冲突场景")
        
        ch4_file.write_text(content, encoding='utf-8')
        print("✅ 第4章冲突场景添加完成")
    
    def add_chapter_6_dialogue(self):
        """第6章增加父子从军争论"""
        ch6_file = self.base_dir / "vol_184_第一卷：黄巾乱世" / "chapter_006.md"
        if not ch6_file.exists():
            print("❌ 第6章文件不存在")
            return
        
        content = ch6_file.read_text(encoding='utf-8')
        
        # 检查是否已有对话
        if "我想去投军" not in content:
            dialogue = """

那日傍晚，张翼终于鼓起勇气，对父亲说出了心事。

"爹，我想去投军。"

张老三正在磨刀的手顿住了。他缓缓抬起头，昏花的眼睛里闪过一丝张翼看不懂的情绪。

"投谁的军？"

"袁绍。"张翼说，"听说他兵多将广，又出身名门……"

"名门？"张老三冷笑一声，"四世三公，门生故吏遍天下，可管过咱们这些庄稼人的死活？"

他放下刀，从怀里摸出半块麸饼——那是今天的晚饭。

"翼儿，你知道咱们家为什么能活到现在吗？"

张翼摇摇头。

"因为咱们不站队。"张老三咬了一口麸饼，"黄巾乱时，咱们逃；董卓乱时，咱们逃；如今袁曹争雄，咱们还要逃。只要咱们不站队，就还有活路。"

"可总得有人结束这乱世……"

"结束？"张老三笑了，笑得比哭还难看，"你爷爷说桓帝能结束，你爷爷死了；我说灵帝能结束，你奶奶死了。如今你说袁绍能结束？"

他站起身，拍了拍儿子的肩膀。

"翼儿，记住爹的话：乱世里，活着就是最大的本事。那些想结束乱世的，大都死在了半路上。"

张翼低头看着自己的手——这双手，本该是握锄头的。

"""
            # 在章节中间插入对话
            insert_marker = "官渡前夕"
            if insert_marker in content:
                content = content.replace(insert_marker, insert_marker + dialogue)
                self.fixes_applied.append("第6章: 增加父子从军争论对话")
        
        ch6_file.write_text(content, encoding='utf-8')
        print("✅ 第6章对话添加完成")
    
    def run_all_fixes(self):
        """运行所有修复"""
        print("="*60)
        print("《三国演义外传》P0级别问题自动修复")
        print("="*60)
        print()
        
        self.fix_chapter_3_language()
        self.fix_chapter_7_language()
        self.fix_chapter_10_transition()
        self.fix_chapter_12_language()
        self.add_chapter_4_conflict()
        self.add_chapter_6_dialogue()
        
        print()
        print("="*60)
        print("修复完成!")
        print("="*60)
        print()
        
        if self.fixes_applied:
            print("已应用的修复:")
            for fix in self.fixes_applied:
                print(f"  ✅ {fix}")
        else:
            print("  ⚠️ 未应用任何修复（可能已修复或文件不存在）")
        
        print()
        print(f"总计: {len(self.fixes_applied)} 处修复")


def main():
    """主函数"""
    fixer = SGYYFixer()
    fixer.run_all_fixes()


if __name__ == "__main__":
    main()
