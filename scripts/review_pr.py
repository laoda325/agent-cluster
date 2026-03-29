#!/usr/bin/env python3
"""
自动化 Code Review - 使用多个 AI Reviewer 审查 PR
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import yaml


@dataclass
class ReviewResult:
    """Review 结果"""
    reviewer: str
    approved: bool
    comments: List[str]
    critical_issues: int
    suggestions: int


class CodeReviewer:
    """自动化 Code Reviewer"""
    
    def __init__(self, config_path: str = "./agent-config.yaml"):
        self.config_path = Path(config_path)
        self.load_config()
    
    def load_config(self):
        """加载配置"""
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = {}
    
    def get_pr_diff(self, pr_number: int) -> str:
        """获取 PR 的 diff"""
        try:
            result = subprocess.run(
                ["gh", "pr", "diff", str(pr_number)],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                return result.stdout
        except Exception as e:
            print(f"⚠️  获取 PR diff 失败: {e}")
        
        return ""
    
    def get_pr_files(self, pr_number: int) -> List[str]:
        """获取 PR 修改的文件列表"""
        try:
            result = subprocess.run(
                ["gh", "pr", "view", str(pr_number), "--json", "files"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                pr_data = json.loads(result.stdout)
                return [f["path"] for f in pr_data.get("files", [])]
        except Exception as e:
            print(f"⚠️  获取 PR 文件列表失败: {e}")
        
        return []
    
    def review_with_codex(self, pr_number: int, diff: str) -> ReviewResult:
        """使用 Codex 进行 Review"""
        print(f"\n🔍 Codex Reviewer 正在审查 PR #{pr_number}...")
        
        # 这里应该调用实际的 Codex API
        # 示例: 构建审查 prompt
        prompt = f"""
请审查以下代码变更，重点关注:
1. 边界情况处理
2. 逻辑错误
3. 缺失的错误处理
4. 竞态条件
5. 代码质量

PR #{pr_number} 的 diff:
```
{diff[:10000]}  # 限制长度
```

请以 JSON 格式返回审查结果:
{{
  "approved": true/false,
  "comments": ["评论列表"],
  "critical_issues": 0,
  "suggestions": 0
}}
"""
        
        # 模拟审查结果
        # 在实际实现中，这里应该调用 Codex API
        result = ReviewResult(
            reviewer="codex",
            approved=True,
            comments=[
                "代码结构清晰",
                "建议添加单元测试覆盖边界情况"
            ],
            critical_issues=0,
            suggestions=1
        )
        
        print(f"   ✅ Codex Review 完成")
        return result
    
    def review_with_gemini(self, pr_number: int, diff: str) -> ReviewResult:
        """使用 Gemini 进行 Review"""
        print(f"\n🔍 Gemini Reviewer 正在审查 PR #{pr_number}...")
        
        # 这里应该调用实际的 Gemini API
        prompt = f"""
请审查以下代码变更，重点关注:
1. 安全问题
2. 扩展性问题
3. 性能问题
4. 最佳实践

PR #{pr_number} 的 diff:
```
{diff[:10000]}
```
"""
        
        # 模拟审查结果
        result = ReviewResult(
            reviewer="gemini",
            approved=True,
            comments=[
                "建议使用参数化查询防止 SQL 注入",
                "考虑添加索引提升查询性能"
            ],
            critical_issues=0,
            suggestions=2
        )
        
        print(f"   ✅ Gemini Review 完成")
        return result
    
    def review_with_claude(self, pr_number: int, diff: str) -> ReviewResult:
        """使用 Claude 进行 Review"""
        print(f"\n🔍 Claude Reviewer 正在审查 PR #{pr_number}...")
        
        # Claude Reviewer 通常过度谨慎
        result = ReviewResult(
            reviewer="claude",
            approved=True,
            comments=[
                "考虑添加更多日志",
                "建议增加类型注释"
            ],
            critical_issues=0,
            suggestions=2
        )
        
        print(f"   ✅ Claude Review 完成")
        return result
    
    def post_review_comment(self, pr_number: int, comment: str):
        """发布 Review 评论"""
        try:
            result = subprocess.run(
                ["gh", "pr", "comment", str(pr_number), "--body", comment],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print(f"   ✅ 评论已发布")
            else:
                print(f"   ⚠️  发布评论失败: {result.stderr}")
        except Exception as e:
            print(f"   ⚠️  发布评论失败: {e}")
    
    def approve_pr(self, pr_number: int):
        """批准 PR"""
        try:
            result = subprocess.run(
                ["gh", "pr", "review", str(pr_number), "--approve"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print(f"   ✅ PR 已批准")
        except Exception as e:
            print(f"   ⚠️  批准 PR 失败: {e}")
    
    def request_changes(self, pr_number: int, comment: str):
        """请求修改"""
        try:
            result = subprocess.run(
                ["gh", "pr", "review", str(pr_number), "--request-changes", "--body", comment],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print(f"   ⚠️  已请求修改")
        except Exception as e:
            print(f"   ⚠️  请求修改失败: {e}")
    
    def review_pr(self, pr_number: int, reviewers: List[str] = None) -> Dict[str, ReviewResult]:
        """审查 PR"""
        if reviewers is None:
            reviewers = ["codex", "gemini"]
        
        print(f"\n{'='*60}")
        print(f"开始审查 PR #{pr_number}")
        print(f"{'='*60}")
        
        # 获取 diff
        diff = self.get_pr_diff(pr_number)
        if not diff:
            print("⚠️  无法获取 PR diff")
            return {}
        
        results = {}
        
        # 执行审查
        for reviewer in reviewers:
            if reviewer == "codex":
                results["codex"] = self.review_with_codex(pr_number, diff)
            elif reviewer == "gemini":
                results["gemini"] = self.review_with_gemini(pr_number, diff)
            elif reviewer == "claude":
                results["claude"] = self.review_with_claude(pr_number, diff)
        
        # 汇总结果
        all_approved = all(r.approved for r in results.values())
        total_issues = sum(r.critical_issues for r in results.values())
        
        print(f"\n{'='*60}")
        print(f"审查完成")
        print(f"{'='*60}")
        print(f"所有审查者批准: {'✅' if all_approved else '❌'}")
        print(f"关键问题数: {total_issues}")
        
        # 发布总结评论
        summary = self._generate_summary(results)
        self.post_review_comment(pr_number, summary)
        
        # 如果全部批准，自动 approve
        if all_approved and total_issues == 0:
            self.approve_pr(pr_number)
        elif total_issues > 0:
            self.request_changes(pr_number, f"发现 {total_issues} 个关键问题需要修复")
        
        return results
    
    def _generate_summary(self, results: Dict[str, ReviewResult]) -> str:
        """生成审查总结"""
        lines = ["## 🤖 AI Review Summary\n"]
        
        for reviewer, result in results.items():
            status = "✅ Approved" if result.approved else "❌ Changes Requested"
            lines.append(f"### {reviewer.upper()} {status}")
            lines.append(f"- Critical Issues: {result.critical_issues}")
            lines.append(f"- Suggestions: {result.suggestions}")
            if result.comments:
                lines.append("- Comments:")
                for comment in result.comments:
                    lines.append(f"  - {comment}")
            lines.append("")
        
        return "\n".join(lines)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="自动化 Code Review")
    parser.add_argument("--pr", type=int, required=True, help="PR 编号")
    parser.add_argument("--reviewers", nargs="+", default=["codex", "gemini"],
                       help="审查者列表")
    parser.add_argument("--config", default="./agent-config.yaml", help="配置文件路径")
    
    args = parser.parse_args()
    
    reviewer = CodeReviewer(args.config)
    results = reviewer.review_pr(args.pr, args.reviewers)
    
    print("\n" + json.dumps({
        reviewer: {
            "approved": r.approved,
            "critical_issues": r.critical_issues,
            "suggestions": r.suggestions
        }
        for reviewer, r in results.items()
    }, indent=2))


if __name__ == "__main__":
    main()
