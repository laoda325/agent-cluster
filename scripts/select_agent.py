#!/usr/bin/env python3
"""
Agent 选择器 - 根据任务类型智能选择 Agent
"""

import json
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import yaml


@dataclass
class TaskAnalysis:
    """任务分析结果"""
    task_type: str
    keywords: List[str]
    suggested_agent: str
    confidence: float
    reasoning: str


class AgentSelector:
    """Agent 智能选择器"""
    
    # 任务类型与 Agent 的映射
    TASK_AGENT_MAPPING = {
        # 后端任务 -> Codex
        "backend_logic": "codex",
        "api_development": "codex",
        "database_schema": "codex",
        "authentication": "codex",
        "server_side": "codex",
        "microservices": "codex",
        
        # 复杂任务 -> Codex
        "complex_bugs": "codex",
        "multi_file_refactor": "codex",
        "cross_codebase_reasoning": "codex",
        "performance_optimization": "codex",
        "security_fixes": "codex",
        
        # 前端任务 -> Claude Code
        "frontend_work": "claude_code",
        "ui_components": "claude_code",
        "styling": "claude_code",
        "responsive_design": "claude_code",
        "state_management": "claude_code",
        
        # 快速任务 -> Claude Code
        "quick_fixes": "claude_code",
        "git_operations": "claude_code",
        "minor_changes": "claude_code",
        "documentation": "claude_code",
        
        # 设计任务 -> Gemini
        "ui_design": "gemini",
        "ux_improvements": "gemini",
        "design_specs": "gemini",
        "html_css": "gemini",
        "prototypes": "gemini",
    }
    
    # 关键词权重
    KEYWORD_WEIGHTS = {
        # Codex 关键词
        "backend": (1.0, "codex"),
        "api": (0.9, "codex"),
        "database": (0.9, "codex"),
        "sql": (0.9, "codex"),
        "server": (0.8, "codex"),
        "bug": (0.8, "codex"),
        "refactor": (0.9, "codex"),
        "performance": (0.7, "codex"),
        "security": (0.8, "codex"),
        "authentication": (0.9, "codex"),
        "logic": (0.7, "codex"),
        "complex": (0.8, "codex"),
        "algorithm": (0.9, "codex"),
        
        # Claude Code 关键词
        "frontend": (1.0, "claude_code"),
        "ui": (0.8, "claude_code"),
        "component": (0.7, "claude_code"),
        "style": (0.8, "claude_code"),
        "css": (0.8, "claude_code"),
        "quick": (0.7, "claude_code"),
        "fix": (0.6, "claude_code"),
        "button": (0.6, "claude_code"),
        "form": (0.6, "claude_code"),
        "page": (0.5, "claude_code"),
        
        # Gemini 关键词
        "design": (1.0, "gemini"),
        "ux": (0.9, "gemini"),
        "prototype": (0.8, "gemini"),
        "mockup": (0.9, "gemini"),
        "visual": (0.8, "gemini"),
        "layout": (0.7, "gemini"),
        "animation": (0.7, "gemini"),
        "responsive": (0.6, "gemini"),
    }
    
    def __init__(self, config_path: str = "./agent-config.yaml"):
        self.config_path = config_path
        self.load_config()
    
    def load_config(self):
        """加载配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
        except Exception:
            self.config = {}
    
    def extract_keywords(self, description: str) -> List[str]:
        """提取关键词"""
        # 转小写
        text = description.lower()
        
        # 提取关键词
        keywords = []
        for keyword in self.KEYWORD_WEIGHTS.keys():
            if keyword in text:
                keywords.append(keyword)
        
        return keywords
    
    def calculate_agent_scores(self, keywords: List[str]) -> Dict[str, float]:
        """计算每个 Agent 的得分"""
        scores = {
            "codex": 0.0,
            "claude_code": 0.0,
            "gemini": 0.0
        }
        
        for keyword in keywords:
            if keyword in self.KEYWORD_WEIGHTS:
                weight, agent = self.KEYWORD_WEIGHTS[keyword]
                scores[agent] += weight
        
        # 归一化
        total = sum(scores.values())
        if total > 0:
            for agent in scores:
                scores[agent] /= total
        
        return scores
    
    def analyze_task(self, description: str) -> TaskAnalysis:
        """分析任务"""
        keywords = self.extract_keywords(description)
        scores = self.calculate_agent_scores(keywords)
        
        # 选择得分最高的 Agent
        best_agent = max(scores, key=scores.get)
        confidence = scores[best_agent]
        
        # 生成推理说明
        reasoning = self._generate_reasoning(best_agent, keywords, scores)
        
        # 确定任务类型
        task_type = self._determine_task_type(description, keywords)
        
        return TaskAnalysis(
            task_type=task_type,
            keywords=keywords,
            suggested_agent=best_agent,
            confidence=confidence,
            reasoning=reasoning
        )
    
    def _determine_task_type(self, description: str, keywords: List[str]) -> str:
        """确定任务类型"""
        desc_lower = description.lower()
        
        # 检查特定模式
        if any(k in desc_lower for k in ["bug", "fix", "error", "issue"]):
            return "bug_fix"
        elif any(k in desc_lower for k in ["feature", "add", "new", "implement"]):
            return "feature_development"
        elif any(k in desc_lower for k in ["refactor", "improve", "optimize"]):
            return "refactoring"
        elif any(k in desc_lower for k in ["design", "ui", "ux"]):
            return "design"
        elif any(k in desc_lower for k in ["document", "readme", "comment"]):
            return "documentation"
        else:
            return "general"
    
    def _generate_reasoning(self, agent: str, keywords: List[str], 
                           scores: Dict[str, float]) -> str:
        """生成推理说明"""
        agent_names = {
            "codex": "Codex (GPT-5.3)",
            "claude_code": "Claude Code (Opus 4.5)",
            "gemini": "Gemini (2.5 Pro)"
        }
        
        reasoning_parts = [
            f"推荐使用 {agent_names.get(agent, agent)}",
            f"匹配关键词: {', '.join(keywords[:5]) if keywords else '无'}",
            f"置信度: {scores[agent]:.1%}",
            f"得分详情: Codex={scores['codex']:.2f}, Claude Code={scores['claude_code']:.2f}, Gemini={scores['gemini']:.2f}"
        ]
        
        return " | ".join(reasoning_parts)
    
    def select_agent(self, description: str, 
                     preferred_agent: Optional[str] = None) -> Tuple[str, TaskAnalysis]:
        """选择 Agent"""
        analysis = self.analyze_task(description)
        
        # 如果有首选 Agent 且可用，使用首选
        if preferred_agent:
            agent_config = self.config.get('agents', {}).get(preferred_agent, {})
            if agent_config.get('enabled', True):
                analysis.suggested_agent = preferred_agent
                analysis.reasoning = f"使用用户指定的 Agent | {analysis.reasoning}"
        
        # 检查 Agent 是否启用
        agent_config = self.config.get('agents', {}).get(analysis.suggested_agent, {})
        if not agent_config.get('enabled', True):
            # 选择次优 Agent
            analysis.reasoning += f" | {analysis.suggested_agent} 已禁用，选择备选 Agent"
            analysis.suggested_agent = self._select_fallback_agent()
        
        return analysis.suggested_agent, analysis
    
    def _select_fallback_agent(self) -> str:
        """选择备选 Agent"""
        # 按优先级选择启用的 Agent
        agents = self.config.get('agents', {})
        for agent_name in ['codex', 'claude_code', 'gemini']:
            if agents.get(agent_name, {}).get('enabled', True):
                return agent_name
        return 'codex'  # 默认
    
    def get_agent_capabilities(self, agent: str) -> Dict:
        """获取 Agent 能力"""
        return self.config.get('agents', {}).get(agent, {})


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Agent 选择器")
    parser.add_argument("description", help="任务描述")
    parser.add_argument("--config", default="./agent-config.yaml", help="配置文件路径")
    parser.add_argument("--preferred", help="首选 Agent")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")
    
    args = parser.parse_args()
    
    selector = AgentSelector(args.config)
    agent, analysis = selector.select_agent(args.description, args.preferred)
    
    if args.json:
        result = {
            "suggested_agent": agent,
            "analysis": {
                "task_type": analysis.task_type,
                "keywords": analysis.keywords,
                "confidence": analysis.confidence,
                "reasoning": analysis.reasoning
            }
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"\n{'='*60}")
        print(f"Agent 选择结果")
        print(f"{'='*60}")
        print(f"推荐 Agent: {agent.upper()}")
        print(f"任务类型: {analysis.task_type}")
        print(f"匹配关键词: {', '.join(analysis.keywords)}")
        print(f"置信度: {analysis.confidence:.1%}")
        print(f"推理: {analysis.reasoning}")
        print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
