#!/usr/bin/env python3
"""Auto-update README.md and README_zh.md indexes from report files.

Scans en/ and zh/ directories, parses YAML frontmatter tags, generates
markdown tables + tag cloud, and replaces placeholders in both README files.

Usage:
    python3 src/update-index.py          # run from repo root
"""

import os
import re
import yaml
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter

REPO_ROOT = Path(__file__).resolve().parent.parent

SECTIONS = {
    "daily":    ("en/daily",    "zh/daily"),
    "weekly":   ("en/weekly",   "zh/weekly"),
    "trending": ("en/trending", "zh/trending"),
    "infra":    ("en/infra",    "zh/infra"),
}

EN_LABELS = {
    "daily":    "📅 Daily Digests",
    "weekly":   "📊 Weekly Synthesis",
    "trending": "🔥 GitHub Trending Deep-Dives",
    "infra":    "🖥 Infrastructure",
}

ZH_LABELS = {
    "daily":    "📅 每日摘要",
    "weekly":   "📊 每周合成",
    "trending": "🔥 GitHub Trending 深度分析",
    "infra":    "🖥 基础设施",
}

EN_EMPTY = {
    "daily":    "*No daily digests yet.*",
    "weekly":   "*No weekly syntheses yet.*",
    "trending": "*No trending analyses yet.*",
    "infra":    "*No infrastructure reports yet.*",
}

ZH_EMPTY = {
    "daily":    "*暂无每日摘要。*",
    "weekly":   "*暂无每周合成。*",
    "trending": "*暂无 Trending 分析。*",
    "infra":    "*暂无基础设施报告。*",
}


def parse_frontmatter(filepath: Path) -> dict:
    """Extract YAML frontmatter from a markdown file. Returns {} if none."""
    text = filepath.read_text(encoding="utf-8")
    m = re.match(r'^---\s*\n(.*?)\n---', text, re.DOTALL)
    if not m:
        return {}
    try:
        return yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return {}


def scan_files(dir_path: Path) -> list[Path]:
    """Return .md files sorted reverse-chronologically (newest first)."""
    if not dir_path.exists():
        return []
    files = sorted(
        dir_path.rglob("*.md"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return files[:30]


def build_table(files: list[Path], section: str) -> str:
    """Build a markdown table from file paths, extracting date/tags from frontmatter."""
    if not files:
        return EN_EMPTY.get(section, "*No reports yet.*")

    lines = []
    if section == "weekly":
        lines.append("| Week | Report | Tags |")
        lines.append("|------|--------|------|")
    else:
        lines.append("| Date | Report | Tags |")
        lines.append("|------|--------|------|")

    for f in files:
        rel = f.relative_to(REPO_ROOT)
        name = f.stem
        fm = parse_frontmatter(f)
        tags = fm.get("tags", [])
        tag_str = ", ".join(f"`{t}`" for t in tags) if tags else "—"
        display_date = fm.get("date", name.replace("-", " ").replace("_", " "))
        lines.append(f"| {display_date} | [{name}]({rel}) | {tag_str} |")

    return "\n".join(lines)


def build_tag_cloud(all_tags: Counter, lang: str) -> str:
    """Build a tag cloud section."""
    if not all_tags:
        if lang == "zh":
            return "*暂无标签。*"
        return "*No tags yet.*"

    # Sort by frequency desc, then alphabetically
    sorted_tags = sorted(all_tags.items(), key=lambda x: (-x[1], x[0]))
    badges = []
    for tag, count in sorted_tags:
        badges.append(f"`{tag}` ({count})")
    return " · ".join(badges)


def update_readme(template_path: Path, tables: dict[str, str],
                  tag_cloud: str, last_updated: str):
    """Replace placeholders in template."""
    content = template_path.read_text(encoding="utf-8")

    for section, table in tables.items():
        placeholder = f"<!-- {section.upper()}_TABLE -->"
        content = content.replace(placeholder, table)

    content = content.replace("<!-- TAG_CLOUD -->", tag_cloud)
    content = content.replace("<!-- LAST_UPDATED -->", last_updated)
    template_path.write_text(content, encoding="utf-8")


def main():
    en_tables = {}
    zh_tables = {}
    en_tags = Counter()
    zh_tags = Counter()

    for section, (en_dir, zh_dir) in SECTIONS.items():
        en_path = REPO_ROOT / en_dir
        zh_path = REPO_ROOT / zh_dir

        en_files = scan_files(en_path)
        zh_files = scan_files(zh_path)

        en_tables[section] = build_table(en_files, section)
        zh_tables[section] = build_table(zh_files, section)

        # Collect tags
        for f in en_files:
            fm = parse_frontmatter(f)
            for t in fm.get("tags", []):
                en_tags[t] += 1
        for f in zh_files:
            fm = parse_frontmatter(f)
            for t in fm.get("tags", []):
                zh_tags[t] += 1

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    en_cloud = build_tag_cloud(en_tags, "en")
    zh_cloud = build_tag_cloud(zh_tags, "zh")

    update_readme(REPO_ROOT / "README.md", en_tables, en_cloud, now)
    update_readme(REPO_ROOT / "README_zh.md", zh_tables, zh_cloud, now)

    print(f"✅ Indexes updated at {now}")
    print(f"   Tags (EN): {len(en_tags)} unique, {sum(en_tags.values())} total")
    print(f"   Tags (ZH): {len(zh_tags)} unique, {sum(zh_tags.values())} total")


if __name__ == "__main__":
    main()
