#!/usr/bin/env python3
"""测试DeepSeek API连接"""
import requests

api_key = "sk-5a1b68c2819b49f49caaf2e73a7d6bc7"
base_url = "https://api.deepseek.com/v1"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

data = {
    "model": "deepseek-chat",
    "messages": [
        {"role": "user", "content": "你好，测试DeepSeek API。请回复\"API连接成功\"。"}
    ],
    "max_tokens": 100
}

print("🔄 测试 DeepSeek API...")
response = requests.post(f"{base_url}/chat/completions", headers=headers, json=data, timeout=30)

if response.status_code == 200:
    result = response.json()
    content = result["choices"][0]["message"]["content"]
    print(f"✅ API连接成功！")
    print(f"回复: {content}")
else:
    print(f"❌ API调用失败: {response.status_code}")
    print(f"错误: {response.text}")
