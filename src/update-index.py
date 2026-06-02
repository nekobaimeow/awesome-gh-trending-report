#!/usr/bin/env python3
"""Auto-update README.md and README_zh.md for awesome-gh-trending-report.

Scans en/trending/ and zh/trending/ directories, parses YAML frontmatter
(date + tags), and generates three sections in both READMEs:

1. Today's Grabs   — reports from today
2. This Week's Grabs — reports from this ISO week
3. By Tag           — all reports grouped by tag, continuously updated

Usage:
    python3 src/update-index.py          # run from repo root
"""

import re
import yaml
from datetime import date, datetime, timezone
from pathlib import Path
from collections import defaultdict

REPO_ROOT = Path(__file__).resolve().parent.parent

EN_TRENDING = REPO_ROOT / "en" / "trending"
ZH_TRENDING = REPO_ROOT / "zh" / "trending"


# ── Frontmatter parsing ────────────────────────────────────────────

def parse_frontmatter(filepath: Path) -> dict:
    """Extract YAML frontmatter. Returns {} if none or parse error."""
    text = filepath.read_text(encoding="utf-8")
    m = re.match(r'^---\s*\n(.*?)\n---', text, re.DOTALL)
    if not m:
        return {}
    try:
        return yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return {}


def get_date(fm: dict, fallback_path: Path) -> date:
    """Extract date from frontmatter, or fall back to file mtime."""
    raw = fm.get("date")
    if raw:
        try:
            if isinstance(raw, date):
                return raw
            return date.fromisoformat(str(raw)[:10])
        except (ValueError, TypeError):
            pass
    # Fallback: file modification time (UTC)
    mtime = fallback_path.stat().st_mtime
    return datetime.fromtimestamp(mtime, tz=timezone.utc).date()


# ── File scanning ──────────────────────────────────────────────────

def scan_trending(base_dir: Path) -> list[tuple[Path, dict, date]]:
    """Return list of (path, frontmatter, parsed_date) sorted newest first."""
    if not base_dir.exists():
        return []
    results = []
    for f in sorted(base_dir.rglob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True):
        fm = parse_frontmatter(f)
        d = get_date(fm, f)
        results.append((f, fm, d))
    return results


# ── Table builders ─────────────────────────────────────────────────

def build_today_table(files: list[tuple[Path, dict, date]], lang: str) -> str:
    """Build a markdown table of today's reports."""
    today = date.today()
    todays = [(p, fm, d) for p, fm, d in files if d == today]
    if not todays:
        return {
            "en": "*No projects grabbed today yet.*",
            "zh": "*今天还没有抓取项目。*",
        }[lang]

    lines = _table_header(lang)
    for p, fm, d in todays:
        rel = p.relative_to(REPO_ROOT)
        lines.append(_table_row(p, fm, rel))
    return "\n".join(lines)


def build_week_table(files: list[tuple[Path, dict, date]], lang: str) -> str:
    """Build a markdown table of this week's reports."""
    today = date.today()
    # ISO week: Monday=1, Sunday=7
    monday = today - date.resolution * today.weekday()
    sunday = monday + date.resolution * 6

    weeks = [(p, fm, d) for p, fm, d in files if monday <= d <= sunday]
    if not weeks:
        return {
            "en": "*No projects grabbed this week yet.*",
            "zh": "*本周还没有抓取项目。*",
        }[lang]

    lines = _table_header(lang)
    for p, fm, d in weeks:
        rel = p.relative_to(REPO_ROOT)
        lines.append(_table_row(p, fm, rel))
    return "\n".join(lines)


def _table_header(lang: str) -> list[str]:
    if lang == "zh":
        return [
            "| 日期 | 项目 | 标签 |",
            "|------|------|------|",
        ]
    return [
        "| Date | Project | Tags |",
        "|------|---------|------|",
    ]


def _table_row(path: Path, fm: dict, rel: Path) -> str:
    tags = fm.get("tags", [])
    tag_str = ", ".join(f"`{t}`" for t in tags) if tags else "—"
    display_date = fm.get("date", path.stem[:10])
    name = path.stem
    return f"| {display_date} | [{name}]({rel}) | {tag_str} |"


# ── Tag sections ───────────────────────────────────────────────────

def build_tag_index(all_tags: set[str], lang: str) -> str:
    """Build a tag quick-jump index line."""
    if not all_tags:
        return {
            "en": "*No tags yet.*",
            "zh": "*暂无标签。*",
        }[lang]
    sorted_tags = sorted(all_tags)
    badges = [f"[`{t}`](#{t})" for t in sorted_tags]
    label = "Jump to:" if lang == "en" else "快速跳转："
    return f"{label} " + " · ".join(badges)


def build_tag_sections(files: list[tuple[Path, dict, date]], lang: str) -> str:
    """Build grouped sections: one per tag, listing relevant reports."""
    if not files:
        return {
            "en": "*No reports yet.*",
            "zh": "*暂无报告。*",
        }[lang]

    # Group files by tag
    tag_groups: dict[str, list[tuple[Path, dict, date]]] = defaultdict(list)
    for p, fm, d in files:
        for tag in fm.get("tags", []):
            tag_groups[tag].append((p, fm, d))

    if not tag_groups:
        return {
            "en": "*No tagged reports yet.*",
            "zh": "*暂无带标签的报告。*",
        }[lang]

    sections = []
    for tag in sorted(tag_groups.keys()):
        items = tag_groups[tag]
        # Deduplicate by path
        seen = set()
        unique = []
        for p, fm, d in items:
            if p not in seen:
                seen.add(p)
                unique.append((p, fm, d))

        section = [f"### {tag}\n"]
        for p, fm, d in unique:
            rel = p.relative_to(REPO_ROOT)
            d_str = fm.get("date", p.stem[:10])
            tags = fm.get("tags", [])
            tag_str = ", ".join(f"`{t}`" for t in tags) if tags else ""
            section.append(f"- **[{p.stem}]({rel})** ({d_str}) — {tag_str}")
        sections.append("\n".join(section))

    return "\n\n".join(sections)


# ── README update ──────────────────────────────────────────────────

def update_readme(template_path: Path, today_table: str, week_table: str,
                  tag_index: str, tag_sections: str, last_updated: str):
    """Replace placeholders in template."""
    content = template_path.read_text(encoding="utf-8")

    content = content.replace("<!-- TODAY_TABLE -->", today_table)
    content = content.replace("<!-- WEEK_TABLE -->", week_table)
    content = content.replace("<!-- TAG_INDEX -->", tag_index)
    content = content.replace("<!-- TAG_SECTIONS -->", tag_sections)
    content = content.replace("<!-- LAST_UPDATED -->", last_updated)

    template_path.write_text(content, encoding="utf-8")


# ── Main ───────────────────────────────────────────────────────────

def main():
    en_files = scan_trending(EN_TRENDING)
    zh_files = scan_trending(ZH_TRENDING)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # English
    en_today = build_today_table(en_files, "en")
    en_week = build_week_table(en_files, "en")
    en_all_tags = set()
    for _, fm, _ in en_files:
        en_all_tags.update(fm.get("tags", []))
    en_tag_idx = build_tag_index(en_all_tags, "en")
    en_tag_sec = build_tag_sections(en_files, "en")
    update_readme(REPO_ROOT / "README.md", en_today, en_week,
                  en_tag_idx, en_tag_sec, now)

    # Chinese
    zh_today = build_today_table(zh_files, "zh")
    zh_week = build_week_table(zh_files, "zh")
    zh_all_tags = set()
    for _, fm, _ in zh_files:
        zh_all_tags.update(fm.get("tags", []))
    zh_tag_idx = build_tag_index(zh_all_tags, "zh")
    zh_tag_sec = build_tag_sections(zh_files, "zh")
    update_readme(REPO_ROOT / "README_zh.md", zh_today, zh_week,
                  zh_tag_idx, zh_tag_sec, now)

    print(f"✅ Indexes updated at {now}")
    print(f"   EN: {len(en_files)} reports, {len(en_all_tags)} tags")
    print(f"   ZH: {len(zh_files)} reports, {len(zh_all_tags)} tags")


if __name__ == "__main__":
    main()
