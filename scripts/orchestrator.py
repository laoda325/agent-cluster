#!/usr/bin/env python3
"""
编排层集成模块 - Orchestrator Integration
============================================
持有所有业务上下文，调度各子系统，为 Agent 提供精准的 prompt。

核心功能：
1. 读取 Obsidian 会议记录
2. 访问生产数据库（只读）
3. 管理员 API（充值、解除阻塞）
4. 上下文管理
5. Agent 调度
"""

import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml

# 尝试导入数据库驱动
try:
    import psycopg2
    HAS_POSTGRES = True
except ImportError:
    HAS_POSTGRES = False

try:
    import pymysql
    HAS_MYSQL = True
except ImportError:
    HAS_MYSQL = False


class ConfigLoader:
    """配置加载器"""
    
    def __init__(self, config_path: str = "./integrations-config.yaml"):
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
            value = value.get(k, default) if isinstance(value, dict) else default
        return value


class ObsidianReader:
    """Obsidian 笔记读取器"""
    
    def __init__(self, config: ConfigLoader):
        self.config = config
        self.vault_path = Path(config.get('obsidian.vault_path', ''))
        self.notes_subdir = config.get('obsidian.notes_subdir', 'meetings')
        self.enabled = config.get('obsidian.enabled', False)
    
    def find_meetings(self, days_back: int = 30) -> List[Dict[str, Any]]:
        """查找会议记录"""
        if not self.enabled or not self.vault_path.exists():
            print(f"⚠️  Obsidian 未启用或路径无效: {self.vault_path}")
            return []
        
        meetings_dir = self.vault_path / self.notes_subdir
        if not meetings_dir.exists():
            # 尝试在根目录查找
            meetings_dir = self.vault_path
        
        cutoff_date = datetime.now() - timedelta(days=days_back)
        results = []
        
        for md_file in meetings_dir.glob("**/*.md"):
            try:
                stat = md_file.stat()
                mtime = datetime.fromtimestamp(stat.st_mtime)
                
                if mtime >= cutoff_date:
                    with open(md_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    results.append({
                        'file': str(md_file.relative_to(self.vault_path)),
                        'name': md_file.stem,
                        'modified': mtime.isoformat(),
                        'content': content,
                        'summary': self._extract_summary(content)
                    })
            except Exception as e:
                print(f"⚠️  读取 {md_file} 失败: {e}")
        
        # 按日期排序
        results.sort(key=lambda x: x['modified'], reverse=True)
        return results
    
    def _extract_summary(self, content: str, max_lines: int = 10) -> str:
        """提取摘要"""
        lines = content.split('\n')
        summary_lines = []
        in_frontmatter = False
        
        for line in lines:
            if line.strip() == '---':
                in_frontmatter = not in_frontmatter
                continue
            if in_frontmatter:
                continue
            if line.strip().startswith('#'):
                continue
            if line.strip():
                summary_lines.append(line.strip())
            if len(summary_lines) >= max_lines:
                break
        
        return '\n'.join(summary_lines)
    
    def search_notes(self, keyword: str, days_back: int = 30) -> List[Dict[str, Any]]:
        """搜索笔记"""
        meetings = self.find_meetings(days_back)
        keyword_lower = keyword.lower()
        
        results = []
        for meeting in meetings:
            if keyword_lower in meeting['content'].lower():
                results.append(meeting)
        
        return results


class DatabaseConnector:
    """数据库连接器（只读）"""
    
    def __init__(self, config: ConfigLoader):
        self.config = config
        self.enabled = config.get('database.enabled', False)
        self.db_type = config.get('database.type', 'postgresql')
        self.read_only = config.get('database.read_only', True)
        self.allowed_tables = set(config.get('database.allowed_tables', []))
        self.conn = None
    
    def connect(self) -> bool:
        """建立连接"""
        if not self.enabled:
            return False
        
        try:
            if self.db_type == 'postgresql' and HAS_POSTGRES:
                self.conn = psycopg2.connect(
                    host=self.config.get('database.host'),
                    port=self.config.get('database.port', 5432),
                    database=self.config.get('database.database'),
                    user=self.config.get('database.user'),
                    password=self.config.get('database.password'),
                    connect_timeout=self.config.get('database.timeout_seconds', 30)
                )
                print("✅ PostgreSQL 连接成功")
                return True
            
            elif self.db_type == 'mysql' and HAS_MYSQL:
                self.conn = pymysql.connect(
                    host=self.config.get('database.host'),
                    port=self.config.get('database.port', 3306),
                    database=self.config.get('database.database'),
                    user=self.config.get('database.user'),
                    password=self.config.get('database.password'),
                    connect_timeout=self.config.get('database.timeout_seconds', 30)
                )
                print("✅ MySQL 连接成功")
                return True
            
            else:
                print(f"⚠️  数据库类型 {self.db_type} 不可用或驱动未安装")
                return False
                
        except Exception as e:
            print(f"❌ 数据库连接失败: {e}")
            return False
    
    def disconnect(self):
        """断开连接"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def query(self, sql: str, params: tuple = None) -> List[Dict]:
        """查询（只读）"""
        if not self.conn:
            if not self.connect():
                return []
        
        # 安全检查：只允许查询白名单表
        sql_lower = sql.lower()
        for table in self.allowed_tables:
            if table.lower() in sql_lower:
                if 'insert' in sql_lower or 'update' in sql_lower or 'delete' in sql_lower or 'drop' in sql_lower or 'truncate' in sql_lower:
                    print(f"⚠️  拒绝写入操作，仅允许只读查询")
                    return []
                break
        else:
            print(f"⚠️  拒绝查询未授权的表")
            return []
        
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(sql, params)
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            print(f"❌ 查询失败: {e}")
            return []
    
    def get_customer_config(self, customer_id: str) -> Optional[Dict]:
        """获取客户配置"""
        if 'customers' in self.allowed_tables:
            results = self.query(
                "SELECT * FROM customers WHERE id = %s",
                (customer_id,)
            )
            return results[0] if results else None
        return None
    
    def get_customer_usage(self, customer_id: str, days: int = 30) -> List[Dict]:
        """获取客户使用记录"""
        if 'usage_logs' in self.allowed_tables:
            return self.query(
                """
                SELECT * FROM usage_logs 
                WHERE customer_id = %s AND created_at >= NOW() - INTERVAL %s DAY
                ORDER BY created_at DESC
                """,
                (customer_id, days)
            )
        return []


class AdminAPIClient:
    """管理员 API 客户端"""
    
    def __init__(self, config: ConfigLoader):
        self.config = config
        self.enabled = config.get('admin_api.enabled', False)
        self.base_url = config.get('admin_api.base_url', '').rstrip('/')
        self.api_key = config.get('admin_api.api_key', '')
        self.allowed_actions = set(config.get('admin_api.allowed_actions', []))
        self.rate_limit = config.get('admin_api.rate_limit_per_minute', 10)
        self.request_log = []
    
    def _check_rate_limit(self) -> bool:
        """检查速率限制"""
        now = datetime.now()
        self.request_log = [
            t for t in self.request_log 
            if (now - t).total_seconds() < 60
        ]
        if len(self.request_log) >= self.rate_limit:
            print(f"⚠️  API 速率限制: {self.rate_limit}/分钟")
            return False
        self.request_log.append(now)
        return True
    
    def _request(self, method: str, endpoint: str, data: dict = None) -> Optional[Dict]:
        """发送请求"""
        if not self.enabled:
            print("⚠️  管理员 API 未启用")
            return None
        
        if not self._check_rate_limit():
            return None
        
        try:
            import requests
            url = f"{self.base_url}{endpoint}"
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            if method.upper() == 'GET':
                resp = requests.get(url, headers=headers, timeout=30)
            elif method.upper() == 'POST':
                resp = requests.post(url, headers=headers, json=data, timeout=30)
            elif method.upper() == 'PUT':
                resp = requests.put(url, headers=headers, json=data, timeout=30)
            else:
                return None
            
            resp.raise_for_status()
            return resp.json() if resp.content else {}
            
        except Exception as e:
            print(f"❌ API 请求失败: {e}")
            return None
    
    def recharge_credit(self, customer_id: str, amount: float, reason: str = "") -> bool:
        """客户充值"""
        if 'credit_recharge' not in self.allowed_actions:
            print("⚠️  credit_recharge 操作未授权")
            return False
        
        result = self._request('POST', '/admin/credit/recharge', {
            'customer_id': customer_id,
            'amount': amount,
            'reason': reason,
            'operator': 'orchestrator'
        })
        
        if result and result.get('success'):
            print(f"✅ 已为客户 {customer_id} 充值 {amount}")
            return True
        return False
    
    def unblock_account(self, customer_id: str, reason: str = "") -> bool:
        """解除账户阻塞"""
        if 'unblock_account' not in self.allowed_actions:
            print("⚠️  unblock_account 操作未授权")
            return False
        
        result = self._request('POST', '/admin/account/unblock', {
            'customer_id': customer_id,
            'reason': reason
        })
        
        if result and result.get('success'):
            print(f"✅ 已解除客户 {customer_id} 的账户阻塞")
            return True
        return False
    
    def extend_trial(self, customer_id: str, days: int, reason: str = "") -> bool:
        """延长试用期"""
        if 'extend_trial' not in self.allowed_actions:
            print("⚠️  extend_trial 操作未授权")
            return False
        
        result = self._request('POST', '/admin/trial/extend', {
            'customer_id': customer_id,
            'days': days,
            'reason': reason
        })
        
        if result and result.get('success'):
            print(f"✅ 已为客户 {customer_id} 延长试用期 {days} 天")
            return True
        return False


class ContextManager:
    """上下文管理器"""
    
    def __init__(self, config: ConfigLoader):
        self.config = config
        self.max_tokens = config.get('context_manager.max_context_tokens', 50000)
        self.priority_sources = config.get('context_manager.priority_sources', [])
        self.time_window = config.get('context_manager.context_window', '7d')
        self.summary_enabled = config.get('context_manager.summary_enabled', True)
    
    def build_context(self, 
                      obsidian: ObsidianReader,
                      database: DatabaseConnector,
                      task_history: List[Dict] = None,
                      successful_patterns: List[Dict] = None,
                      customer_id: str = None) -> str:
        """构建完整上下文"""
        context_parts = []
        
        # 1. 会议记录（最高优先级）
        if 'obsidian_meetings' in self.priority_sources:
            meetings = obsidian.find_meetings(days_back=self._parse_days(self.time_window))
            if meetings:
                context_parts.append("## 📋 最近会议记录\n")
                for m in meetings[:5]:  # 最近5个
                    context_parts.append(f"### {m['name']} ({m['modified'][:10]})")
                    context_parts.append(m['summary'])
                    context_parts.append("")
        
        # 2. 客户配置
        if customer_id and 'database_customer_config' in self.priority_sources:
            customer_config = database.get_customer_config(customer_id)
            if customer_config:
                context_parts.append("## 👤 客户配置\n")
                # 脱敏处理
                safe_config = self._sanitize_config(customer_config)
                context_parts.append(json.dumps(safe_config, indent=2, ensure_ascii=False))
                context_parts.append("")
        
        # 3. 任务历史
        if task_history and 'task_history' in self.priority_sources:
            context_parts.append("## 📝 任务历史\n")
            for t in task_history[-10:]:  # 最近10个
                context_parts.append(f"- **{t.get('id', 'N/A')}**: {t.get('description', '')} → {t.get('status', '')}")
            context_parts.append("")
        
        # 4. 成功模式
        if successful_patterns and 'successful_patterns' in self.priority_sources:
            context_parts.append("## ✅ 成功模式（已验证的有效策略）\n")
            for p in successful_patterns[-5:]:
                context_parts.append(f"- {p.get('pattern', '')}: {p.get('success_rate', '')}")
            context_parts.append("")
        
        return '\n'.join(context_parts)
    
    def _parse_days(self, window: str) -> int:
        """解析时间窗口"""
        match = re.match(r'(\d+)d', window)
        return int(match.group(1)) if match else 7
    
    def _sanitize_config(self, config: Dict) -> Dict:
        """脱敏配置，移除敏感信息"""
        sensitive_keys = {'password', 'secret', 'token', 'api_key', 'credit_card'}
        safe = {}
        for k, v in config.items():
            if any(s in k.lower() for s in sensitive_keys):
                safe[k] = '***'
            else:
                safe[k] = v
        return safe


class Orchestrator:
    """编排层主控制器"""
    
    def __init__(self, 
                 integrations_config: str = "./integrations-config.yaml",
                 agent_config: str = "./agent-config.yaml"):
        
        self.config = ConfigLoader(integrations_config)
        self.obsidian = ObsidianReader(self.config)
        self.database = DatabaseConnector(self.config)
        self.admin_api = AdminAPIClient(self.config)
        self.context = ContextManager(self.config)
        
        # 加载 Agent 配置
        agent_config_path = Path(agent_config)
        if agent_config_path.exists():
            with open(agent_config_path, 'r', encoding='utf-8') as f:
                self.agent_config = yaml.safe_load(f) or {}
        else:
            self.agent_config = {}
    
    def get_full_context(self, customer_id: str = None) -> str:
        """获取完整业务上下文"""
        return self.context.build_context(
            obsidian=self.obsidian,
            database=self.database,
            customer_id=customer_id
        )
    
    def generate_prompt(self, 
                        task_description: str, 
                        customer_id: str = None,
                        additional_context: str = "") -> str:
        """生成带上下文的精确 prompt"""
        context = self.get_full_context(customer_id)
        
        prompt_parts = []
        
        if context:
            prompt_parts.append("=== 业务上下文 ===")
            prompt_parts.append(context)
            prompt_parts.append("")
        
        if additional_context:
            prompt_parts.append("=== 额外说明 ===")
            prompt_parts.append(additional_context)
            prompt_parts.append("")
        
        prompt_parts.append("=== 当前任务 ===")
        prompt_parts.append(task_description)
        
        return '\n'.join(prompt_parts)
    
    def handle_customer_request(self, 
                                customer_id: str, 
                                request: str,
                                auto_unblock: bool = True) -> Dict[str, Any]:
        """处理客户请求（带自动解除阻塞）"""
        result = {
            'success': False,
            'context': None,
            'prompt': None,
            'actions_taken': []
        }
        
        # 1. 检查客户状态
        customer = self.database.get_customer_config(customer_id)
        if not customer:
            result['error'] = f"客户 {customer_id} 不存在"
            return result
        
        # 2. 检查是否被阻塞，如果是则自动解除
        if customer.get('status') == 'blocked' and auto_unblock:
            if self.admin_api.unblock_account(customer_id, "客户请求自动解除"):
                result['actions_taken'].append(f"已自动解除客户 {customer_id} 的阻塞")
        
        # 3. 构建上下文
        result['context'] = self.context.build_context(
            obsidian=self.obsidian,
            database=self.database,
            customer_id=customer_id
        )
        
        # 4. 生成 prompt
        result['prompt'] = self.generate_prompt(request, customer_id)
        result['success'] = True
        
        return result
    
    def build_agent_task(self,
                        task_description: str,
                        agent_type: str = "codex",
                        customer_id: str = None) -> Dict[str, Any]:
        """构建 Agent 任务"""
        
        # 获取上下文
        context = self.get_full_context(customer_id)
        
        # 根据任务类型选择 Agent
        task_prompt = self.generate_prompt(task_description, customer_id, context)
        
        return {
            'task_description': task_description,
            'agent_type': agent_type,
            'prompt': task_prompt,
            'context_used': bool(context),
            'customer_id': customer_id,
            'created_at': datetime.now().isoformat()
        }


def main():
    """测试/演示"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║         编排层集成模块 - 测试                               ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    orchestrator = Orchestrator()
    
    # 测试上下文构建
    print("\n📋 构建完整上下文...")
    context = orchestrator.get_full_context()
    print(context[:500] + "..." if len(context) > 500 else context)
    
    # 测试 prompt 生成
    print("\n\n📝 生成带上下文的 prompt...")
    prompt = orchestrator.generate_prompt(
        "实现客户定制化邮件模板功能",
        customer_id="cust_12345"
    )
    print(prompt[:800] + "..." if len(prompt) > 800 else prompt)
    
    print("\n✅ 编排层集成模块测试完成")


if __name__ == "__main__":
    main()
