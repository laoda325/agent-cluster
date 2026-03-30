#!/usr/bin/env python3
"""
Ralph Loop 学习系统 - Ralph Loop Learning System
=================================================
记录成功/失败模式，优化后续任务提示词

功能：
1. 记录任务执行结果
2. 分析成功/失败模式
3. 动态优化提示词
4. 生成最佳实践建议
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict


class RalphLoop:
    """Ralph Loop 学习系统"""
    
    def __init__(self, storage_dir: str = "./context"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.patterns_file = self.storage_dir / "ralph_patterns.json"
        self.learnings_file = self.storage_dir / "ralph_learnings.json"
        self.best_practices_file = self.storage_dir / "best_practices.md"
        
        self.patterns = self._load_json(self.patterns_file, {})
        self.learnings = self._load_json(self.learnings_file, [])
    
    def _load_json(self, file: Path, default: Any) -> Any:
        """加载 JSON 文件"""
        if file.exists():
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return default
        return default
    
    def _save_json(self, file: Path, data: Any):
        """保存 JSON 文件"""
        with open(file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def record_task(self, 
                   task_id: str,
                   description: str,
                   agent: str,
                   success: bool,
                   failure_reason: Optional[str] = None,
                   execution_time: Optional[float] = None,
                   pr_created: bool = False,
                   ci_passed: bool = False):
        """记录任务执行结果"""
        
        learning = {
            "task_id": task_id,
            "description": description,
            "agent": agent,
            "success": success,
            "failure_reason": failure_reason,
            "execution_time": execution_time,
            "pr_created": pr_created,
            "ci_passed": ci_passed,
            "timestamp": datetime.now().isoformat(),
            "keywords": self._extract_keywords(description)
        }
        
        self.learnings.append(learning)
        self._save_json(self.learnings_file, self.learnings)
        
        # 更新模式统计
        self._update_patterns(learning)
        
        print(f"✅ Ralph Loop 已记录: {task_id} ({'成功' if success else '失败'})")
    
    def _extract_keywords(self, description: str) -> List[str]:
        """提取关键词"""
        # 简单的关键词提取
        keywords = []
        keyword_map = {
            "backend": ["后端", "api", "数据库", "server", "backend"],
            "frontend": ["前端", "ui", "界面", "组件", "frontend", "react", "vue"],
            "bug": ["bug", "修复", "错误", "异常", "fix"],
            "feature": ["功能", "新增", "实现", "feature", "implement"],
            "refactor": ["重构", "优化", "refactor", "optimize"],
            "security": ["安全", "权限", "认证", "security", "auth"],
            "test": ["测试", "test", "unittest", "e2e"]
        }
        
        desc_lower = description.lower()
        for category, words in keyword_map.items():
            if any(word in desc_lower for word in words):
                keywords.append(category)
        
        return keywords
    
    def _update_patterns(self, learning: Dict):
        """更新模式统计"""
        for keyword in learning.get("keywords", []):
            if keyword not in self.patterns:
                self.patterns[keyword] = {
                    "total": 0,
                    "success": 0,
                    "fail": 0,
                    "agents": defaultdict(lambda: {"success": 0, "fail": 0}),
                    "failure_reasons": []
                }
            
            pattern = self.patterns[keyword]
            pattern["total"] += 1
            
            if learning["success"]:
                pattern["success"] += 1
                pattern["agents"][learning["agent"]]["success"] += 1
            else:
                pattern["fail"] += 1
                pattern["agents"][learning["agent"]]["fail"] += 1
                if learning.get("failure_reason"):
                    pattern["failure_reasons"].append(learning["failure_reason"])
        
        self._save_json(self.patterns_file, self.patterns)
    
    def get_agent_recommendation(self, description: str) -> Dict[str, Any]:
        """根据历史数据推荐最佳 Agent"""
        keywords = self._extract_keywords(description)
        
        recommendations = {}
        
        for keyword in keywords:
            if keyword in self.patterns:
                pattern = self.patterns[keyword]
                for agent, stats in pattern["agents"].items():
                    total = stats["success"] + stats["fail"]
                    if total > 0:
                        success_rate = stats["success"] / total
                        if agent not in recommendations:
                            recommendations[agent] = {"total": 0, "success": 0}
                        recommendations[agent]["total"] += total
                        recommendations[agent]["success"] += stats["success"]
        
        # 计算成功率并排序
        for agent, stats in recommendations.items():
            stats["success_rate"] = stats["success"] / stats["total"] if stats["total"] > 0 else 0
        
        sorted_recommendations = sorted(
            recommendations.items(),
            key=lambda x: (x[1]["success_rate"], x[1]["total"]),
            reverse=True
        )
        
        return {
            "keywords": keywords,
            "recommendations": sorted_recommendations[:3],
            "best_agent": sorted_recommendations[0][0] if sorted_recommendations else None
        }
    
    def generate_best_practices(self) -> str:
        """生成最佳实践文档"""
        
        content = f"""# Ralph Loop 最佳实践

> 自动生成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
> 基于 {len(self.learnings)} 次任务执行记录

## 📊 整体统计

| 指标 | 数值 |
|------|------|
| 总任务数 | {len(self.learnings)} |
| 成功 | {sum(1 for l in self.learnings if l['success'])} |
| 失败 | {sum(1 for l in self.learnings if not l['success'])} |
| 成功率 | {sum(1 for l in self.learnings if l['success']) / len(self.learnings) * 100 if self.learnings else 0:.1f}% |

## 🎯 Agent 表现

"""
        
        # 统计 Agent 表现
        agent_stats = defaultdict(lambda: {"success": 0, "fail": 0})
        for learning in self.learnings:
            agent = learning["agent"]
            if learning["success"]:
                agent_stats[agent]["success"] += 1
            else:
                agent_stats[agent]["fail"] += 1
        
        content += "| Agent | 成功 | 失败 | 成功率 |\n"
        content += "|-------|------|------|--------|\n"
        
        for agent, stats in sorted(agent_stats.items(), 
                                   key=lambda x: x[1]["success"] / (x[1]["success"] + x[1]["fail"]) if (x[1]["success"] + x[1]["fail"]) > 0 else 0,
                                   reverse=True):
            total = stats["success"] + stats["fail"]
            rate = stats["success"] / total * 100 if total > 0 else 0
            content += f"| {agent} | {stats['success']} | {stats['fail']} | {rate:.1f}% |\n"
        
        content += "\n## 📈 任务类型成功率\n\n"
        content += "| 类型 | 成功 | 失败 | 成功率 | 推荐 Agent |\n"
        content += "|------|------|------|--------|------------|\n"
        
        for keyword, pattern in sorted(self.patterns.items(), 
                                       key=lambda x: x[1]["success"] / x[1]["total"] if x[1]["total"] > 0 else 0,
                                       reverse=True):
            total = pattern["total"]
            success = pattern["success"]
            rate = success / total * 100 if total > 0 else 0
            
            # 找出最佳 Agent
            best_agent = None
            best_rate = 0
            for agent, stats in pattern["agents"].items():
                agent_total = stats["success"] + stats["fail"]
                if agent_total > 0:
                    agent_rate = stats["success"] / agent_total
                    if agent_rate > best_rate:
                        best_rate = agent_rate
                        best_agent = agent
            
            content += f"| {keyword} | {success} | {pattern['fail']} | {rate:.1f}% | {best_agent or 'N/A'} |\n"
        
        content += "\n## ⚠️ 常见失败原因\n\n"
        
        # 收集失败原因
        failure_reasons = []
        for learning in self.learnings:
            if not learning["success"] and learning.get("failure_reason"):
                failure_reasons.append(learning["failure_reason"])
        
        if failure_reasons:
            from collections import Counter
            common_reasons = Counter(failure_reasons).most_common(10)
            for reason, count in common_reasons:
                content += f"- **{reason}** ({count} 次)\n"
        else:
            content += "暂无失败记录\n"
        
        content += "\n## 💡 优化建议\n\n"
        content += self._generate_suggestions()
        
        # 保存文件
        self.best_practices_file.write_text(content, encoding='utf-8')
        
        return content
    
    def _generate_suggestions(self) -> str:
        """生成优化建议"""
        suggestions = []
        
        # 分析失败模式
        for keyword, pattern in self.patterns.items():
            if pattern["total"] >= 3:  # 至少有3个样本
                success_rate = pattern["success"] / pattern["total"]
                
                if success_rate < 0.5:
                    suggestions.append(
                        f"- **{keyword}** 类型任务成功率较低 ({success_rate*100:.1f}%)，"
                        f"建议增加更详细的任务描述或拆分为更小的子任务"
                    )
                
                # 找出表现最好的 Agent
                best_agent = None
                best_rate = 0
                for agent, stats in pattern["agents"].items():
                    agent_total = stats["success"] + stats["fail"]
                    if agent_total >= 2:
                        agent_rate = stats["success"] / agent_total
                        if agent_rate > best_rate:
                            best_rate = agent_rate
                            best_agent = agent
                
                if best_agent and best_rate > 0.7:
                    suggestions.append(
                        f"- **{keyword}** 类型任务推荐使用 **{best_agent}** "
                        f"(成功率 {best_rate*100:.1f}%)"
                    )
        
        if not suggestions:
            suggestions.append("- 数据样本不足，建议继续执行任务以积累更多数据")
        
        return "\n".join(suggestions)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total = len(self.learnings)
        success = sum(1 for l in self.learnings if l["success"])
        
        return {
            "total_tasks": total,
            "success_count": success,
            "fail_count": total - success,
            "success_rate": success / total if total > 0 else 0,
            "patterns_count": len(self.patterns),
            "last_updated": datetime.now().isoformat()
        }


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Ralph Loop 学习系统")
    parser.add_argument("--stats", action="store_true", help="查看统计")
    parser.add_argument("--report", action="store_true", help="生成最佳实践报告")
    parser.add_argument("--recommend", type=str, help="获取 Agent 推荐（输入任务描述）")
    
    args = parser.parse_args()
    
    ralph = RalphLoop()
    
    if args.stats:
        stats = ralph.get_stats()
        print(f"""
╔═══════════════════════════════════════════════════════════╗
║         📊 Ralph Loop 统计                                ║
╚═══════════════════════════════════════════════════════════╝

总任务数: {stats['total_tasks']}
成功: {stats['success_count']}
失败: {stats['fail_count']}
成功率: {stats['success_rate']*100:.1f}%
模式数: {stats['patterns_count']}
        """)
    
    elif args.report:
        content = ralph.generate_best_practices()
        print(f"✅ 最佳实践报告已生成: {ralph.best_practices_file}")
        print("\n" + "="*60)
        print(content[:2000])
        print("..." if len(content) > 2000 else "")
    
    elif args.recommend:
        rec = ralph.get_agent_recommendation(args.recommend)
        print(f"\n任务描述: {args.recommend}")
        print(f"关键词: {', '.join(rec['keywords'])}")
        print(f"\n推荐 Agent:")
        for agent, stats in rec['recommendations']:
            print(f"  - {agent}: {stats['success_rate']*100:.1f}% 成功率 ({stats['success']}/{stats['total']})")
    
    else:
        print("""
╔═══════════════════════════════════════════════════════════╗
║         🧠 Ralph Loop 学习系统                            ║
╚═══════════════════════════════════════════════════════════╝

用法:
  --stats          查看统计信息
  --report         生成最佳实践报告
  --recommend "xxx" 获取 Agent 推荐

示例:
  python ralph_loop.py --stats
  python ralph_loop.py --report
  python ralph_loop.py --recommend "实现用户登录功能"
        """)


if __name__ == "__main__":
    main()
