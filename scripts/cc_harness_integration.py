#!/usr/bin/env python3
"""
CC Harness Skills 深度集成模块
================================
将6个CC Harness Skills统一集成到Agent集群工作流中。

技能列表:
1. dream-memory       — 内存整合
2. memory-extractor   — 记忆提取
3. verification-gate  — 验证门控
4. swarm-coordinator  — 群体协调
5. structured-context-compressor — 上下文压缩
6. kairos-lite        — 轻量级主动任务
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

SKILLS_DIR = Path(os.environ.get("USERPROFILE", "~")).expanduser() / ".openclaw/workspace/skills"
MEMORY_ROOT = Path("C:/Users/1978w/.qclaw/skill-mini-workspace/memory")
REPO_ROOT   = Path("C:/Users/1978w/.qclaw/skill-mini-workspace/agent-cluster")


def _run_skill_script(skill: str, script: str, args: list[str]) -> dict:
    """运行技能脚本并返回JSON结果"""
    script_path = SKILLS_DIR / skill / "scripts" / script
    cmd = [sys.executable, str(script_path)] + args + ["--json"]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        return {"error": result.stderr.strip()}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"output": result.stdout.strip()}


# ─────────────────────────────────────────────
# 1. dream-memory — 内存整合
# ─────────────────────────────────────────────
def run_dream_memory(verbose: bool = True) -> dict:
    """检查并整合内存目录状态"""
    print("\n🧠 [dream-memory] 检查内存目录...")
    report = _run_skill_script("dream-memory", "dream_memory.py",
                               ["--memory-root", str(MEMORY_ROOT)])
    if verbose:
        idx = report.get("index", {})
        topics = report.get("topic_files", [])
        print(f"   MEMORY.md: {'存在' if idx.get('exists') else '不存在'} | "
              f"{idx.get('line_count', 0)}行 / {idx.get('byte_count', 0)}字节")
        print(f"   主题文件: {len(topics)} 个")
        for t in topics:
            print(f"     - {t['name']} ({t['size_bytes']} bytes)")
        if idx.get("over_line_cap"):
            print("   ⚠️  MEMORY.md 超过200行，建议整合")
        if idx.get("over_byte_cap"):
            print("   ⚠️  MEMORY.md 超过25KB，建议整合")
        else:
            print("   ✅ 内存状态正常")
    return report


# ─────────────────────────────────────────────
# 2. memory-extractor — 记忆提取
# ─────────────────────────────────────────────
def run_memory_extractor(verbose: bool = True) -> list:
    """扫描记忆清单，返回已分类的记忆文件"""
    print("\n📋 [memory-extractor] 扫描记忆清单...")
    manifest = _run_skill_script("memory-extractor", "memory_manifest.py",
                                 ["--memory-root", str(MEMORY_ROOT)])
    if isinstance(manifest, list) and verbose:
        typed   = [m for m in manifest if m.get("type")]
        untyped = [m for m in manifest if not m.get("type")]
        print(f"   已分类: {len(typed)} 个 | 未分类: {len(untyped)} 个")
        for m in typed:
            print(f"     [{m['type']:10s}] {m['file']} — {m.get('title', '-')}")
        if untyped:
            print(f"   ⚠️  {len(untyped)} 个文件缺少frontmatter分类:")
            for m in untyped:
                print(f"     - {m['file']}")
    return manifest if isinstance(manifest, list) else []


# ─────────────────────────────────────────────
# 3. verification-gate — 验证门控
# ─────────────────────────────────────────────
def run_verification_gate(repo: Path = REPO_ROOT, verbose: bool = True) -> dict:
    """收集git仓库验证上下文"""
    print(f"\n🔍 [verification-gate] 验证仓库: {repo.name}...")
    ctx = _run_skill_script("verification-gate", "verification_context.py",
                            ["--repo", str(repo)])
    if verbose and "error" not in ctx:
        print(f"   分支: {ctx.get('branch')} | HEAD: {ctx.get('head')}")
        changed = ctx.get("changed_files", [])
        status_lines = [l for l in ctx.get("status", "").splitlines() if l.strip()]
        print(f"   修改文件: {len(changed)} 个 | 状态行: {len(status_lines)} 条")
        untracked = [l for l in status_lines if l.startswith("??")]
        modified  = [l for l in status_lines if l.startswith(" M") or l.startswith("M ")]
        print(f"   未跟踪: {len(untracked)} | 已修改: {len(modified)}")
        if modified:
            print("   ⚠️  有未提交的修改，建议提交后再验证")
        else:
            print("   ✅ 工作区干净")
    return ctx


# ─────────────────────────────────────────────
# 4. swarm-coordinator — 群体协调
# ─────────────────────────────────────────────
def run_swarm_coordinator(goal: str, workers: list[str] = None,
                          fmt: str = "markdown", verbose: bool = True) -> dict:
    """生成任务分解看板"""
    print(f"\n🐝 [swarm-coordinator] 分解任务: {goal[:50]}...")
    workers = workers or ["research", "synthesis", "implementation", "verification"]
    worker_args = []
    for w in workers:
        worker_args += ["--worker", w]
    # 不传 --json，用 --format markdown
    script_path = SKILLS_DIR / "swarm-coordinator" / "scripts" / "task_board.py"
    cmd = [sys.executable, str(script_path),
           "--goal", goal, "--format", fmt] + worker_args
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if fmt == "json":
        try:
            board = json.loads(result.stdout)
        except Exception:
            board = {"output": result.stdout}
    else:
        board = {"markdown": result.stdout}

    if verbose:
        if fmt == "markdown":
            print(result.stdout)
        else:
            for phase in board.get("phases", []):
                print(f"   [{phase['phase']:15s}] owner={phase['owner']} → {phase['deliverable']}")
    return board


# ─────────────────────────────────────────────
# 5. structured-context-compressor — 上下文压缩
# ─────────────────────────────────────────────
def run_context_compressor(verbose: bool = True) -> str:
    """渲染9部分续集摘要模板"""
    print("\n📦 [structured-context-compressor] 渲染续集模板...")
    script_path = SKILLS_DIR / "structured-context-compressor" / "scripts" / "render_template.py"
    result = subprocess.run([sys.executable, str(script_path)],
                            capture_output=True, text=True, encoding="utf-8")
    output = result.stdout.strip() or result.stderr.strip()
    if verbose:
        lines = output.splitlines()
        print(f"   模板行数: {len(lines)}")
        for line in lines[:8]:
            print(f"   {line}")
        if len(lines) > 8:
            print(f"   ... (共{len(lines)}行)")
    return output


# ─────────────────────────────────────────────
# 6. kairos-lite — 轻量级主动任务
# ─────────────────────────────────────────────
def run_kairos_lite(name: str, prompt: str, schedule: str,
                    mode: str = "recurring", expiry_days: int = 7,
                    verbose: bool = True) -> dict:
    """创建定时任务规范"""
    print(f"\n⏰ [kairos-lite] 创建任务规范: {name}...")
    script_path = SKILLS_DIR / "kairos-lite" / "scripts" / "job_spec.py"
    cmd = [sys.executable, str(script_path),
           "--name", name,
           "--prompt", prompt,
           "--schedule", schedule,
           "--mode", mode,
           "--expiry-days", str(expiry_days)]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    try:
        spec = json.loads(result.stdout)
    except Exception:
        spec = {"output": result.stdout}
    if verbose:
        print(f"   名称: {spec.get('name')}")
        print(f"   计划: {spec.get('schedule')}")
        print(f"   模式: {spec.get('mode')} | 过期: {spec.get('expiry_days')}天")
        print(f"   提示词: {str(spec.get('prompt', ''))[:60]}...")
    return spec


# ─────────────────────────────────────────────
# 完整工作流：全量集成运行
# ─────────────────────────────────────────────
def run_full_integration():
    """运行完整的CC Harness Skills集成工作流"""
    print("=" * 65)
    print("🚀 CC Harness Skills 深度集成工作流")
    print(f"   时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)

    results = {}

    # 1. 内存整合
    results["dream_memory"] = run_dream_memory()

    # 2. 记忆提取
    results["memory_manifest"] = run_memory_extractor()

    # 3. 验证门控
    results["verification"] = run_verification_gate()

    # 4. 群体协调 — 针对当前待办任务
    results["swarm_board"] = run_swarm_coordinator(
        goal="完成《三国演义外传》P1/P2/P3修改并导出最终版本",
        workers=["research", "synthesis", "implementation", "verification"],
        fmt="markdown"
    )

    # 5. 上下文压缩
    results["compressor"] = run_context_compressor()

    # 6. kairos-lite — 注册三个定时任务规范
    jobs = [
        {
            "name": "daily-memory-consolidation",
            "prompt": "运行dream-memory整合内存目录，更新MEMORY.md索引",
            "schedule": "0 9 * * *",
            "expiry_days": 30,
        },
        {
            "name": "novel-progress-check",
            "prompt": "检查《三国演义外传》P1/P2/P3修改进度，统计完成章节数",
            "schedule": "0 */6 * * *",
            "expiry_days": 14,
        },
        {
            "name": "agent-cluster-health",
            "prompt": "检查agent-cluster守护进程存活状态和失败任务数量",
            "schedule": "*/30 * * * *",
            "expiry_days": 7,
        },
    ]
    results["kairos_jobs"] = []
    for job in jobs:
        spec = run_kairos_lite(**job)
        results["kairos_jobs"].append(spec)

    # 保存集成报告
    report_path = REPO_ROOT / "cc_harness_integration_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        # swarm markdown不可序列化，转为字符串
        safe = {k: (v if not isinstance(v, dict) or "markdown" not in v
                    else {"markdown_lines": len(v["markdown"].splitlines())})
                for k, v in results.items()}
        json.dump(safe, f, ensure_ascii=False, indent=2, default=str)

    print("\n" + "=" * 65)
    print("✅ 集成工作流完成")
    print(f"   报告已保存: {report_path.name}")
    print("=" * 65)
    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="CC Harness Skills 深度集成")
    parser.add_argument("--skill", choices=[
        "dream-memory", "memory-extractor", "verification-gate",
        "swarm-coordinator", "structured-context-compressor", "kairos-lite", "all"
    ], default="all", help="运行指定技能或全部")
    parser.add_argument("--goal", default="完成《三国演义外传》P1/P2/P3修改并导出最终版本")
    args = parser.parse_args()

    if args.skill == "all":
        run_full_integration()
    elif args.skill == "dream-memory":
        run_dream_memory()
    elif args.skill == "memory-extractor":
        run_memory_extractor()
    elif args.skill == "verification-gate":
        run_verification_gate()
    elif args.skill == "swarm-coordinator":
        run_swarm_coordinator(args.goal)
    elif args.skill == "structured-context-compressor":
        run_context_compressor()
    elif args.skill == "kairos-lite":
        run_kairos_lite("demo-job", "示例任务提示词", "0 9 * * *")
