#!/usr/bin/env python3
"""
《三国演义外传》批量创作脚本
使用 DeepSeek API 批量创作章节
"""

import os
import requests
import time
from pathlib import Path
from typing import List, Dict


class SGYYWriter:
    """三国演义外传批量创作器"""
    
    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        self.output_dir = Path("F:/AI小说风格仿写创作/三国演义外传")
        
        # 三卷结构
        self.volumes = [
            {
                "name": "vol_184_第一卷：黄巾乱世",
                "chapters": [
                    {"num": 1, "title": "乱世初现", "year": 184, "desc": "张翼出生，黄巾起义爆发"},
                    {"num": 2, "title": "童年动荡", "year": 185, "desc": "黄巾战乱，家人离散"},
                    {"num": 3, "title": "少年立志", "year": 190, "desc": "董卓入京，天下大乱"},
                    {"num": 4, "title": "逃难冀州", "year": 191, "desc": "随家逃难，定居异乡"},
                    {"num": 5, "title": "初识英雄", "year": 195, "desc": "曹操崛起，偶遇刘备"},
                    {"num": 6, "title": "官渡前夕", "year": 199, "desc": "袁曹对峙，百姓苦不堪言"},
                    {"num": 7, "title": "战火纷飞", "year": 200, "desc": "官渡之战，命运转折"},
                    {"num": 8, "title": "战后余波", "year": 205, "desc": "曹操统一北方"},
                    {"num": 9, "title": "赤壁战前", "year": 207, "desc": "刘孙联合，备战赤壁"},
                    {"num": 10, "title": "三分天下", "year": 220, "desc": "曹丕篡汉，三国鼎立"}
                ]
            },
            {
                "name": "vol_220_第二卷：三国鼎立",
                "chapters": [
                    {"num": 1, "title": "刘备称帝", "year": 221, "desc": "蜀汉建立，刘备称帝"},
                    {"num": 2, "title": "夷陵之战", "year": 222, "desc": "吴蜀交兵，亲人离散"},
                    {"num": 3, "title": "白帝托孤", "year": 223, "desc": "刘备病逝，诸葛亮辅政"},
                    {"num": 4, "title": "诸葛亮北伐", "year": 228, "desc": "六出祁山，星落五丈原"},
                    {"num": 5, "title": "司马崛起", "year": 249, "desc": "高平陵之变，司马氏掌权"},
                    {"num": 6, "title": "曹魏衰落", "year": 254, "desc": "司马昭弑君"},
                    {"num": 7, "title": "蜀汉末日", "year": 263, "desc": "邓艾偷渡，蜀汉灭亡"},
                    {"num": 8, "title": "钟会之乱", "year": 264, "desc": "姜维谋反，身死乱中"},
                    {"num": 9, "title": "西晋建立", "year": 265, "desc": "司马炎篡魏，晋朝建立"},
                    {"num": 10, "title": "东吴覆灭", "year": 279, "desc": "晋军南下，孙皓投降"}
                ]
            },
            {
                "name": "vol_280_第三卷：天下归晋",
                "chapters": [
                    {"num": 1, "title": "太康盛世", "year": 280, "desc": "天下一统，太康之治"},
                    {"num": 2, "title": "故人凋零", "year": 282, "desc": "故友相继离世"},
                    {"num": 3, "title": "回忆往事", "year": 285, "desc": "张翼回忆一生"},
                    {"num": 4, "title": "子孙满堂", "year": 288, "desc": "家族传承"},
                    {"num": 5, "title": "历史轮回", "year": 290, "desc": "分久必合，合久必分"},
                    {"num": 6, "title": "人生感悟", "year": 295, "desc": "看透世事"},
                    {"num": 7, "title": "最后的时光", "year": 298, "desc": "安度晚年"},
                    {"num": 8, "title": "后记", "year": 300, "desc": "百年沧桑"}
                ]
            }
        ]
    
    # 每章专属的开头切入方式，确保多样性
    CHAPTER_OPENERS = {
        "vol_184_第一卷：黄巾乱世": {
            1: ("环境描写", "从自然景象或季节切入"),
            2: ("对话开场", "从人物对话直接切入"),
            3: ("动作开场", "从人物正在进行的动作切入"),
            4: ("行进场景", "从赶路或逃难的动态场景切入"),
            5: ("偶遇场景", "从意外相遇的瞬间切入"),
            6: ("紧张时刻", "从危险或紧急情况切入"),
            7: ("声音开场", "从远处传来的声音或消息切入"),
            8: ("战后场景", "从战争结束后的废墟或余波切入"),
            9: ("内心独白", "从主人公的心理活动切入"),
            10: ("时间流逝", "从季节更替或岁月感慨切入"),
        },
        "vol_220_第二卷：三国鼎立": {
            1: ("仪式场景", "从盛大的典礼或仪式切入"),
            2: ("战场边缘", "从战场附近的普通人视角切入"),
            3: ("雨夜场景", "从雨夜守城的孤独氛围切入"),
            4: ("出征前夕", "从军队集结或出发前的场景切入"),
            5: ("政变消息", "从突然传来的政治消息切入"),
            6: ("市井传言", "从街头巷尾的议论声切入"),
            7: ("末日氛围", "从城破前夕的绝望气氛切入"),
            8: ("乱军之中", "从混乱的战场或逃亡场景切入"),
            9: ("新朝气象", "从新王朝建立后的变化切入"),
            10: ("江边送别", "从江边目送或离别场景切入"),
        },
        "vol_280_第三卷：天下归晋": {
            1: ("渔网劳作", "从老年张翼的日常劳作切入"),
            2: ("噩耗传来", "从得知故人离世的消息切入"),
            3: ("独坐回忆", "从独自坐在某处陷入回忆切入"),
            4: ("家族聚会", "从子孙绕膝的热闹场景切入"),
            5: ("历史感慨", "从目睹某个历史重演的场景切入"),
            6: ("夕阳黄昏", "从黄昏时分的沉思切入"),
            7: ("病榻之上", "从身体衰老的感受切入"),
            8: ("临终回望", "从生命最后时刻的回望切入"),
        }
    }

    def call_api(self, prompt: str, chapter_info: str = "", opener_hint: str = "") -> str:
        """调用 DeepSeek API"""
        system_prompt = f"""你是一位专业的历史小说作家，擅长创作三国时期的历史小说。

【本章专属开头方式 - 必须严格遵守】
开头类型：{opener_hint}
你必须用这种方式开头，不得使用其他方式。

【绝对禁止的重复模式】
- 禁止："XX的XX总是这样，XX地贴着人的脸"
- 禁止："XX背着XX，沿着XX慢慢走着"
- 禁止：任何与前文章节相同或相似的开头句式
- 禁止：以"张翼站在XX外"作为开头
- 禁止：以"XX的晨雾"作为开头

【写作要求】
- 风格：朴实厚重，半文半白
- 视角：第三人称小人物视角
- 字数：1500-2500字
- 情节必须紧扣本章概要，有实质性推进

【本章信息】
{chapter_info}

直接输出正文，第一句话必须符合上述"本章专属开头方式"。"""

        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.9,
                "max_tokens": 4000,
                "presence_penalty": 0.6,   # 惩罚重复词汇
                "frequency_penalty": 0.4   # 降低高频词出现概率
            },
            timeout=180
        )
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    
    def create_chapter(self, volume_name: str, chapter: Dict, context: str = "") -> bool:
        """创作单个章节"""
        num = chapter["num"]
        title = chapter["title"]
        year = chapter["year"]
        desc = chapter["desc"]
        
        print(f"\n{'='*60}")
        print(f"📝 创作中: {volume_name} 第{num}章 - {title}")
        print(f"{'='*60}")
        
        # 获取本章专属开头方式
        vol_openers = self.CHAPTER_OPENERS.get(volume_name, {})
        opener_type, opener_desc = vol_openers.get(num, ("自由开头", "用最适合本章的方式切入"))
        
        # 章节信息
        chapter_info = f"""
- 卷名：{volume_name}
- 章节：第{num}章《{title}》
- 时间：公元{year}年
- 概要：{desc}
- 主人公：张翼，字子翔，184年生于涿郡，现年{year - 184}岁
"""
        
        # 提取前文最后一段作为衔接依据
        last_para = ""
        if context:
            paras = [p.strip() for p in context.split('\n') if p.strip()]
            last_para = paras[-1][:150] if paras else ""
        
        prompt = f"""请创作《三国演义外传》{volume_name}第{num}章《{title}》。

## 本章核心信息
- 时间：公元{year}年，张翼{year - 184}岁
- 核心事件：{desc}
- 张翼在此事件中的角色：亲历者或旁观者，以小人物视角呈现

## 开头要求（必须严格执行）
开头类型：【{opener_type}】
具体方式：{opener_desc}
{"前文最后一句：「" + last_para + "」（开头必须与此不同，形成自然过渡）" if last_para else "本章为全书开篇，直接切入场景。"}

## 内容要求
1. 围绕"{desc}"展开，有具体的人物、对话、行动
2. 体现张翼作为普通人的视角和感受
3. 结尾留有余韵，为下一章做铺垫

直接输出正文，不要标题，不要说明。"""
        
        try:
            content = self.call_api(prompt, chapter_info, f"{opener_type}：{opener_desc}")
            
            # 保存文件
            vol_dir = self.output_dir / volume_name
            vol_dir.mkdir(parents=True, exist_ok=True)
            
            chapter_file = vol_dir / f"chapter_{num:03d}.md"
            chapter_file.write_text(content, encoding='utf-8')
            
            print(f"✅ 完成: {chapter_file.name} ({len(content)} 字) | 开头方式: {opener_type}")
            return True
            
        except Exception as e:
            print(f"❌ 失败: {e}")
            return False
    
    def run_batch(self, count: int = 5):
        """批量创作"""
        print(f"\n🚀 开始批量创作 {count} 章...")
        print(f"📁 输出目录: {self.output_dir}")
        print(f"{'='*60}\n")
        
        created = 0
        for volume in self.volumes:
            volume_name = volume["name"]
            chapters = volume["chapters"]
            
            for chapter in chapters:
                if created >= count:
                    break
                
                # 检查是否已存在
                vol_dir = self.output_dir / volume_name
                chapter_file = vol_dir / f"chapter_{chapter['num']:03d}.md"
                if chapter_file.exists():
                    print(f"⏭️  跳过已存在: {volume_name} 第{chapter['num']}章")
                    continue
                
                # 获取前文上下文
                prev_chapters = []
                for i in range(1, chapter["num"]):
                    prev_file = vol_dir / f"chapter_{i:03d}.md"
                    if prev_file.exists():
                        prev = prev_file.read_text(encoding='utf-8')
                        prev_chapters.append(prev[:500])
                
                context = "\n".join(reversed(prev_chapters)) if prev_chapters else ""
                
                success = self.create_chapter(volume_name, chapter, context)
                if success:
                    created += 1
                    time.sleep(1)  # 避免 API 限流
                
                if created >= count:
                    break
            
            if created >= count:
                break
        
        print(f"\n{'='*60}")
        print(f"✅ 批量创作完成: {created}/{count} 章")
        print(f"{'='*60}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="《三国演义外传》批量创作")
    parser.add_argument("--count", type=int, default=5, help="创作章节数")
    parser.add_argument("--all", action="store_true", help="创作所有章节")
    
    args = parser.parse_args()
    
    writer = SGYYWriter()
    
    if args.all:
        writer.run_batch(28)  # 创作全部28章
    else:
        writer.run_batch(args.count)


if __name__ == "__main__":
    main()
