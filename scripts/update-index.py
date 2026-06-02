#!/usr/bin/env python3
"""Auto-update README.md and README_zh.md indexes from report files.

Scans en/ and zh/ directories, generates markdown tables, and replaces
the <!-- *_TABLE --> placeholders in both README files.

Usage:
    python3 scripts/update-index.py          # run from repo root
"""

import os
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

SECTIONS = {
    "daily": ("en/daily", "zh/daily"),
    "weekly": ("en/weekly", "zh/weekly"),
    "trending": ("en/trending", "zh/trending"),
    "infra": ("en/infra", "zh/infra"),
}

EN_LABELS = {
    "daily": "📅 Daily Digests",
    "weekly": "📊 Weekly Synthesis",
    "trending": "🔥 GitHub Trending Deep-Dives",
    "infra": "🖥 Infrastructure",
}

ZH_LABELS = {
    "daily": "📅 每日摘要",
    "weekly": "📊 每周合成",
    "trending": "🔥 GitHub Trending 深度分析",
    "infra": "🖥 基础设施",
}

EN_EMPTY = {
    "daily": "No daily digests yet. Reports appear after the morning cron runs.",
    "weekly": "No weekly syntheses yet. Published every Friday.",
    "trending": "No trending analyses yet. The hourly deep-dive will populate this.",
    "infra": "No infrastructure reports yet.",
}

ZH_EMPTY = {
    "daily": "暂无每日摘要。早间 cron 运行后报告将出现。",
    "weekly": "暂无每周合成。每周五发布。",
    "trending": "暂无 Trending 分析。每小时深度分析将填充此处。",
    "infra": "暂无基础设施报告。",
}


def scan_files(dir_path: Path) -> list[Path]:
    """Return .md files sorted reverse-chronologically (newest first)."""
    if not dir_path.exists():
        return []
    files = sorted(
        dir_path.rglob("*.md"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return files[:30]  # keep index compact


def build_table(files: list[Path], base_dir: Path, lang: str) -> str:
    """Build a markdown table from file paths."""
    if not files:
        return {
            "en": EN_EMPTY,
            "zh": ZH_EMPTY,
        }[lang].get(base_dir.parent.name, "*No reports yet.*")

    # Determine which section this is
    section = base_dir.parent.name  # e.g. "daily", "trending"

    # Build relative links
    lines = []
    if section in ("daily", "trending", "infra"):
        lines.append("| Date | Report |")
        lines.append("|------|--------|")
    else:  # weekly
        lines.append("| Week | Report |")
        lines.append("|------|--------|")

    for f in files:
        rel = f.relative_to(REPO_ROOT)
        name = f.stem
        # Extract date from filename for display
        display_date = name.replace("-", " ").replace("_", " ")
        lines.append(f"| {display_date} | [{name}]({rel}) |")

    return "\n".join(lines)


def update_readme(template_path: Path, tables: dict[str, str], last_updated: str):
    """Replace <!-- *_TABLE --> and <!-- LAST_UPDATED --> in template."""
    content = template_path.read_text(encoding="utf-8")

    for section, table in tables.items():
        placeholder = f"<!-- {section.upper()}_TABLE -->"
        content = content.replace(placeholder, table)

    content = content.replace("<!-- LAST_UPDATED -->", last_updated)
    template_path.write_text(content, encoding="utf-8")


def main():
    # Generate tables for each section in each language
    en_tables = {}
    zh_tables = {}

    for section, (en_dir, zh_dir) in SECTIONS.items():
        en_path = REPO_ROOT / en_dir
        zh_path = REPO_ROOT / zh_dir

        en_files = scan_files(en_path)
        zh_files = scan_files(zh_path)

        en_tables[section] = build_table(en_files, en_path, "en")
        zh_tables[section] = build_table(zh_files, zh_path, "zh")

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Update English README
    update_readme(REPO_ROOT / "README.md", en_tables, now)

    # Update Chinese README
    update_readme(REPO_ROOT / "README_zh.md", zh_tables, now)

    print(f"✅ Indexes updated at {now}")


if __name__ == "__main__":
    main()
