#!/usr/bin/env python3
"""
《三国演义外传》第一章创作脚本
直接使用 DeepSeek API 创作
"""

import os
import requests
from pathlib import Path


def create_chapter_1():
    """创作第一章"""
    
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("❌ 未设置 DEEPSEEK_API_KEY")
        return
    
    prompt = """你是一位专业的历史小说作家。请创作《三国演义外传》第一章。

## 章节信息
- 标题：第一章：乱世初现
- 时间：公元184年
- 地点：涿郡涿县
- 主人公：张翼（字子翔），普通农户之子

## 情节概要
1. 开篇描写东汉末年的社会背景（宦官专权、民不聊生）
2. 张翼出生在涿郡一个普通农家
3. 同年，黄巾起义爆发，天下大乱
4. 通过张翼父母的对话，展现百姓对时局的担忧
5. 结尾埋下伏笔：刘备（同乡）即将出现

## 写作要求
- 字数：2000字左右
- 风格：朴实厚重，符合历史小说气质
- 视角：第三人称，小人物视角
- 语言：半文半白，有古典韵味

请直接输出章节正文。"""

    print("📝 正在创作第一章...")
    
    try:
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "你是一位专业的历史小说作家，擅长创作三国时期的历史小说。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 4000
            },
            timeout=120
        )
        
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        
        # 保存文件
        output_dir = Path("F:/AI小说风格仿写创作/三国演义外传/vol_184_第一卷：黄巾乱世")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        chapter_file = output_dir / "chapter_001.md"
        chapter_file.write_text(content, encoding='utf-8')
        
        print(f"✅ 第一章创作完成！")
        print(f"📁 保存位置: {chapter_file}")
        print(f"📝 字数: {len(content)} 字符")
        
        # 显示前500字
        print(f"\n{'='*60}")
        print("预览:")
        print(f"{'='*60}")
        print(content[:500] + "..." if len(content) > 500 else content)
        
    except Exception as e:
        print(f"❌ 创作失败: {e}")


if __name__ == "__main__":
    create_chapter_1()
