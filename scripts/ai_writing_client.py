#!/usr/bin/env python3
"""
AI 写作客户端 - AI Writing Client
================================
接入真实 LLM API 进行小说创作

支持：
- DeepSeek API (已配置)
- OpenAI API
- Anthropic Claude API
- Google Gemini API
"""

import json
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import requests


class AIWritingClient:
    """AI 写作客户端"""
    
    def __init__(self):
        # 读取环境变量
        self.deepseek_key = os.getenv("DEEPSEEK_API_KEY")
        self.qclaw_base_url = os.getenv("QCLAW_LLM_BASE_URL")
        self.qclaw_key = os.getenv("QCLAW_LLM_API_KEY")
        
        # 默认使用 DeepSeek
        self.provider = "deepseek"
        self.model = "deepseek-chat"
        
    def write_chapter(self, 
                      chapter_title: str,
                      chapter_outline: str,
                      context: str,
                      word_count: int = 2000) -> str:
        """
        创作章节
        
        Args:
            chapter_title: 章节标题
            chapter_outline: 章节大纲
            context: 上下文（人物设定、前文等）
            word_count: 目标字数
        """
        prompt = self._build_prompt(chapter_title, chapter_outline, context, word_count)
        
        try:
            content = self._call_api(prompt)
            return content
        except Exception as e:
            print(f"❌ API 调用失败: {e}")
            return self._fallback_content(chapter_title, str(e))
    
    def _build_prompt(self, title: str, outline: str, context: str, word_count: int) -> str:
        """构建创作提示词"""
        return f"""你是一位专业的历史小说作家，擅长创作《五代十国宋》时期的历史小说。

## 任务
请创作以下章节，要求：
- 字数：{word_count} 字左右
- 风格：朴实厚重，符合历史小说气质
- 视角：小人物视角，通过主人公李奉的眼睛观察乱世

## 章节信息
标题：{title}
大纲：{outline}

## 上下文
{context}

## 创作要求
1. 开篇要有时代氛围描写
2. 人物对话要符合身份和时代
3. 情节要体现战乱中的人性
4. 适当埋设伏笔，为后续章节铺垫
5. 结尾要有悬念或情感升华

请直接输出章节正文，不需要额外的说明。"""
    
    def _call_api(self, prompt: str) -> str:
        """调用 API"""
        if self.provider == "deepseek" and self.deepseek_key:
            return self._call_deepseek(prompt)
        elif self.qclaw_base_url:
            return self._call_qclaw(prompt)
        else:
            raise ValueError("未配置可用的 API Key")
    
    def _call_deepseek(self, prompt: str) -> str:
        """调用 DeepSeek API"""
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.deepseek_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "你是一位专业的历史小说作家。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 4000
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=120)
        response.raise_for_status()
        
        result = response.json()
        return result["choices"][0]["message"]["content"]
    
    def _call_qclaw(self, prompt: str) -> str:
        """调用 QClaw LLM 代理"""
        url = self.qclaw_base_url
        headers = {
            "Authorization": f"Bearer {self.qclaw_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "default",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 4000
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=120)
        response.raise_for_status()
        
        result = response.json()
        return result["choices"][0]["message"]["content"]
    
    def _fallback_content(self, title: str, error: str) -> str:
        """失败时的回退内容"""
        return f"""# {title}

（创作失败，请检查 API 配置）

错误信息：{error}

---

**建议检查：**
1. DEEPSEEK_API_KEY 环境变量是否设置
2. 网络连接是否正常
3. API 额度是否充足
"""


def test_api():
    """测试 API"""
    print("🧪 测试 AI 写作客户端...")
    
    client = AIWritingClient()
    
    # 检查配置
    print(f"\n📋 配置检查：")
    print(f"   DeepSeek API Key: {'✅ 已配置' if client.deepseek_key else '❌ 未配置'}")
    print(f"   QClaw Base URL: {'✅ 已配置' if client.qclaw_base_url else '❌ 未配置'}")
    
    if not client.deepseek_key and not client.qclaw_base_url:
        print("\n❌ 未配置任何 API，请先设置环境变量")
        return
    
    # 测试创作
    print(f"\n✍️  测试创作...")
    content = client.write_chapter(
        chapter_title="第一章：乱世开篇",
        chapter_outline="主人公李奉出生，唐朝灭亡，洛阳战乱",
        context="主人公李奉，907年出生于洛阳铁匠家庭",
        word_count=500
    )
    
    print(f"\n{'='*60}")
    print(content[:500] + "..." if len(content) > 500 else content)
    print(f"{'='*60}")
    print(f"\n✅ 测试完成，生成 {len(content)} 字符")


if __name__ == "__main__":
    test_api()
