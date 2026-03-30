#!/usr/bin/env python3
"""
Prompt 构建器 - 基于上下文生成精确的 Agent Prompt

核心思路：
- 传统：直接用任务描述生成 Prompt
- 改进版：结合业务上下文、历史模式、成功经验生成精准 Prompt
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml

SCRIPT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

from scripts.orchestrator import (
    Orchestrator,
    ConfigLoader
)


class PromptBuilder:
    """Prompt 构建器"""
    
    # 任务类型对应的系统提示模板
    TASK_TEMPLATES = {
        'bug_fix': {
            'system': """你是一个经验丰富的后端工程师，专注于 Bug 修复。
重点关注：
1. 复现问题 - 先确认 Bug 的具体表现
2. 定位根因 - 不要只修表面，要找到根本原因
3. 编写测试 - 确保 Bug 被修复且不会回归
4. 最小改动 - 只改必要的代码，不要引入新问题""",
            'format': """
## Bug 信息
{bug_description}

## 客户场景
{customer_context}

## 历史类似 Bug（如有）
{similar_bugs}

## 修复要求
1. 先分析问题根因
2. 提供修复方案
3. 编写或更新测试用例
4. 确保不破坏现有功能"""
        },
        
        'feature': {
            'system': """你是一个全栈工程师，专注于功能开发。
重点关注：
1. 需求理解 - 明确客户的真实需求，不是表面描述
2. 架构设计 - 考虑扩展性、可维护性
3. 代码质量 - 遵循最佳实践，编写清晰的代码
4. 测试覆盖 - 确保功能被充分测试""",
            'format': """
## 功能需求
{feature_description}

## 客户背景
{customer_context}

## 成功案例参考（如有）
{success_patterns}

## 开发要求
1. 先理解需求背景和客户场景
2. 设计合理的实现方案
3. 编写测试用例
4. 更新相关文档"""
        },
        
        'refactor': {
            'system': """你是一个代码重构专家，专注于改进代码质量。
重点关注：
1. 保持行为 - 重构不能改变现有功能
2. 渐进式改进 - 每次只改一小部分
3. 充分测试 - 确保重构后所有测试通过
4. 清晰命名 - 让代码自解释""",
            'format': """
## 重构目标
{refactor_description}

## 代码现状
{code_context}

## 技术约束
{technical_constraints}

## 重构要求
1. 先分析现有代码的问题
2. 设计改进方案
3. 逐步重构，每次提交
4. 确保测试全部通过"""
        },
        
        'design': {
            'system': """你是一个 UI/UX 设计师，专注于用户体验。
重点关注：
1. 用户需求 - 理解用户想完成什么任务
2. 简洁直观 - 界面越简单越好
3. 一致性 - 与现有设计语言保持一致
4. 响应式 - 考虑不同屏幕尺寸""",
            'format': """
## 设计需求
{design_description}

## 目标用户
{user_context}

## 设计约束
{design_constraints}

## 输出要求
1. 提供设计方案或规范
2. 考虑组件复用
3. 遵循设计系统规范"""
        }
    }
    
    def __init__(self, config_path: str = "./integrations-config.yaml"):
        self.config = ConfigLoader(config_path)
        self.orchestrator = Orchestrator(config_path)
    
    def identify_task_type(self, description: str) -> str:
        """识别任务类型"""
        desc_lower = description.lower()
        
        if any(k in desc_lower for k in ['bug', 'fix', 'error', 'crash', 'broken']):
            return 'bug_fix'
        elif any(k in desc_lower for k in ['design', 'ui', 'ux', 'mockup', 'prototype']):
            return 'design'
        elif any(k in desc_lower for k in ['refactor', '重构', '优化', 'improve']):
            return 'refactor'
        else:
            return 'feature'
    
    def build(self,
              task_description: str,
              customer_id: str = None,
              task_type: str = None,
              additional_context: str = "") -> Dict[str, str]:
        """构建完整 Prompt"""
        
        # 自动识别任务类型
        if not task_type:
            task_type = self.identify_task_type(task_description)
        
        template = self.TASK_TEMPLATES.get(task_type, self.TASK_TEMPLATES['feature'])
        
        # 获取上下文
        context = self.orchestrator.get_full_context(customer_id)
        
        # 加载历史任务和成功模式
        similar_bugs = self._find_similar_bugs(task_description)
        success_patterns = self._get_success_patterns(task_description, task_type)
        
        # 构建各个部分
        prompt_parts = {
            'system': template['system'],
            'task': task_description,
            'customer_context': context or "（无可用上下文）",
            'similar_bugs': self._format_similar_bugs(similar_bugs),
            'success_patterns': self._format_success_patterns(success_patterns),
            'additional': additional_context
        }
        
        # 生成格式化 Prompt
        formatted = template['format'].format(
            bug_description=task_description,
            feature_description=task_description,
            refactor_description=task_description,
            design_description=task_description,
            customer_context=context or "（无可用上下文）",
            similar_bugs=self._format_similar_bugs(similar_bugs),
            success_patterns=self._format_success_patterns(success_patterns),
            code_context="（需分析现有代码）",
            technical_constraints="（遵循项目代码规范）",
            user_context="（目标用户：企业客户）",
            design_constraints="（遵循设计系统规范）"
        )
        
        return {
            'task_type': task_type,
            'system_prompt': template['system'],
            'task_prompt': formatted,
            'full_prompt': f"{template['system']}\n{formatted}",
            'metadata': {
                'customer_id': customer_id,
                'context_used': bool(context),
                'similar_bugs_found': len(similar_bugs),
                'patterns_found': len(success_patterns),
                'built_at': datetime.now().isoformat()
            }
        }
    
    def _find_similar_bugs(self, description: str) -> List[Dict]:
        """查找类似的 Bug"""
        # 从任务历史中查找
        tasks_dir = SCRIPT_DIR / "tasks"
        similar = []
        
        if tasks_dir.exists():
            for task_file in tasks_dir.glob("*.json"):
                try:
                    with open(task_file, 'r', encoding='utf-8') as f:
                        task = json.load(f)
                        if task.get('status') == 'completed' and 'bug' in task.get('description', '').lower():
                            similar.append(task)
                except Exception:
                    pass
        
        return similar[:3]
    
    def _get_success_patterns(self, description: str, task_type: str) -> List[Dict]:
        """获取成功模式"""
        patterns_file = SCRIPT_DIR / "patterns.json"
        
        if patterns_file.exists():
            try:
                with open(patterns_file, 'r', encoding='utf-8') as f:
                    patterns = json.load(f)
                    return [p for p in patterns if p.get('task_type') == task_type][:3]
            except Exception:
                pass
        
        return []
    
    def _format_similar_bugs(self, bugs: List[Dict]) -> str:
        """格式化类似 Bug"""
        if not bugs:
            return "（未找到类似 Bug）"
        
        lines = []
        for bug in bugs:
            lines.append(f"- [{bug.get('id')}] {bug.get('description', '')[:80]}")
            if bug.get('solution'):
                lines.append(f"  解决方案: {bug['solution'][:100]}")
        
        return '\n'.join(lines) or "（未找到类似 Bug）"
    
    def _format_success_patterns(self, patterns: List[Dict]) -> str:
        """格式化成功模式"""
        if not patterns:
            return "（未找到成功模式）"
        
        lines = []
        for p in patterns:
            lines.append(f"- {p.get('pattern', '')} (成功率: {p.get('success_rate', 'N/A')})")
            lines.append(f"  Prompt: {p.get('example_prompt', '')[:100]}")
        
        return '\n'.join(lines) or "（未找到成功模式）"
    
    def build_dynamic(self,
                     task_description: str,
                     failure_context: str = None) -> str:
        """
        动态构建 Prompt（用于失败重试）
        
        这是 Ralph Loop 的核心改进：
        不是用同样的 Prompt 重试，
        而是分析失败原因，生成更有针对性的 Prompt
        """
        base_prompt = self.build(task_description)
        
        if failure_context:
            # 分析失败原因，生成改进提示
            improvement = self._analyze_failure(failure_context)
            
            enhanced = f"""{base_prompt['full_prompt']}

{'='*60}
## 🔄 改进指导（基于上次失败经验）
{'='*60}

失败原因分析: {failure_context}

改进要点:
{improvement}

请根据以上分析，调整你的实现策略。
"""
            return enhanced
        
        return base_prompt['full_prompt']
    
    def _analyze_failure(self, failure_context: str) -> str:
        """分析失败原因并给出改进建议"""
        context_lower = failure_context.lower()
        
        improvements = []
        
        if 'timeout' in context_lower or '超时' in context_lower:
            improvements.append("1. 任务执行超时，建议分段处理，减少单次操作复杂度")
        
        if 'error' in context_lower or '错误' in context_lower:
            improvements.append("2. 遇到执行错误，建议先检查输入参数和环境配置")
        
        if 'wrong' in context_lower or '错误' in context_lower or '不对' in context_lower:
            improvements.append("3. 方向可能不对，建议先理解客户的真实需求背景")
        
        if 'context' in context_lower or '上下文' in context_lower:
            improvements.append("4. 缺少必要上下文，已在下方补充相关信息")
        
        if not improvements:
            improvements.append("1. 建议重新审视任务要求，按步骤逐步实现")
        
        return '\n'.join(improvements)


def main():
    """测试"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Prompt 构建器")
    parser.add_argument("--task", required=True, help="任务描述")
    parser.add_argument("--customer", help="客户 ID")
    parser.add_argument("--type", choices=['bug_fix', 'feature', 'refactor', 'design'], help="任务类型")
    parser.add_argument("--failure", help="失败上下文（用于动态改进）")
    parser.add_argument("--config", default="./integrations-config.yaml")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--system-only", action="store_true", help="只输出系统提示")
    parser.add_argument("--task-only", action="store_true", help="只输出任务提示")
    
    args = parser.parse_args()
    
    builder = PromptBuilder(args.config)
    
    if args.failure:
        prompt = builder.build_dynamic(args.task, args.failure)
    else:
        result = builder.build(args.task, args.customer, args.type)
        prompt = result['full_prompt']
    
    if args.json:
        print(json.dumps(builder.build(args.task, args.customer, args.type), indent=2, ensure_ascii=False))
    elif args.system_only:
        print(builder.build(args.task)['system_prompt'])
    elif args.task_only:
        print(builder.build(args.task)['task_prompt'])
    else:
        print(prompt)


if __name__ == "__main__":
    main()
