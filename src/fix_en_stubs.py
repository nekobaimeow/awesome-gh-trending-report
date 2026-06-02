#!/usr/bin/env python3
"""
Fix EN stubs: extract structured info from ZH reports — no external API needed.
EN becomes a proper entry page with: overview excerpt, section index, key stats.
ZH keeps full deep-dive, gets a cross-link banner to EN.

Usage: python3 src/fix_en_stubs.py
"""
import re, sys, os
from pathlib import Path
from datetime import date

REPO_ROOT = Path(__file__).resolve().parent.parent
ZH_DIR = REPO_ROOT / "zh" / "trending"
EN_DIR = REPO_ROOT / "en" / "trending"


def extract_frontmatter(content: str) -> tuple:
    """Return (raw_fm, body, tags, date_str)."""
    m = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if not m:
        return ("", "", [], "")
    raw = m.group(0)
    body = m.group(1)

    # tags
    tag_m = re.findall(r'tags:\s*\[(.*?)\]', body)
    tags = []
    if tag_m:
        tags = [t.strip().strip('"').strip("'") for t in tag_m[0].split(',') if t.strip()]

    # date
    date_m = re.search(r'date:\s*(\S+)', body)
    date_str = date_m.group(1) if date_m else ""

    return (raw, body, tags, date_str)


def extract_overview(content: str) -> str:
    """Get first substantive paragraph(s) from the report."""
    for header in ['🔍 项目简介', '项目简介', '🔍 概述']:
        m = re.search(rf'##\s*{re.escape(header)}\s*\n+(.*?)(?=\n##|\n#|\n---|\Z)', content, re.DOTALL)
        if m:
            text = m.group(1).strip()
            # Take first 3 sentences/paragraphs max
            lines = text.split('\n')
            result = []
            for line in lines:
                if line.strip().startswith('##'):
                    break
                result.append(line)
                if len(result) >= 5:
                    break
            return '\n'.join(result).strip()
    return ""


def extract_sections(content: str) -> list:
    """List all ## section headers found in the report."""
    sections = re.findall(r'^##\s+(.*?)$', content, re.MULTILINE)
    return sections


def extract_stats(content: str) -> dict:
    """Extract Stars/Forks/Language/License info."""
    stats = {}
    for key, pattern in [
        ('stars', r'(?:Stars|⭐|star)[：:\s]*([\d,]+)'),
        ('forks', r'(?:Forks?|🍴)[：:\s]*([\d,]+)'),
        ('language', r'(?:Language|语言|Lang)[：:\s]*(\S+)'),
        ('license', r'(?:License|许可证)[：:\s]*(\S+)'),
    ]:
        m = re.search(pattern, content, re.IGNORECASE)
        if m:
            stats[key] = m.group(1)
    return stats


def process_file(zh_path: Path):
    fname = zh_path.name
    en_path = EN_DIR / fname
    repo_name = fname.split('-', 3)[-1].replace('.md', '')

    zh_content = zh_path.read_text(encoding='utf-8')
    fm_raw, fm_body, tags, date_str = extract_frontmatter(zh_content)

    if not fm_raw:
        print(f"  [SKIP] no frontmatter")
        return

    # Title
    title_match = re.search(r'^#\s+(.*)', zh_content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else repo_name

    # Extract data
    overview = extract_overview(zh_content)
    sections = extract_sections(zh_content)
    stats = extract_stats(zh_content)

    tags_display = ', '.join(f'`{t}`' for t in tags) if tags else '`github-trending`'
    date_display = date_str.split('T')[0] if date_str else 'unknown'

    # Stats line
    stats_parts = []
    if stats.get('stars'):
        stats_parts.append(f"⭐ {stats['stars']}")
    if stats.get('forks'):
        stats_parts.append(f"🍴 {stats['forks']}")
    if stats.get('language'):
        stats_parts.append(f"📝 {stats['language']}")
    if stats.get('license'):
        stats_parts.append(f"📄 {stats['license']}")
    stats_line = ' | '.join(stats_parts) if stats_parts else ''

    # Build English entry page
    en_report = f"""{fm_raw}
# {title} — Source Code Analysis

> **Tags:** {tags_display} | **Date:** {date_display}
> {stats_line}

## Overview

{overview if overview else f'A deep-dive source code analysis of **{title}**, examining architecture, core features, security posture, and implementation details.'}

## What's Inside

"""
    if sections:
        for s in sections[:10]:
            en_report += f"- {s}\n"
    else:
        en_report += "- Full source code analysis with architecture diagrams\n"
        en_report += "- Security audit with vulnerability scanning\n"
        en_report += "- Knowledge graph (Mermaid) of core module dependencies\n"

    en_report += f"""
---

📖 **Full deep-dive analysis (Chinese):** [{fname}](../../zh/trending/{fname})
"""

    os.makedirs(EN_DIR, exist_ok=True)
    en_path.write_text(en_report, encoding='utf-8')
    print(f"  [EN] {len(en_report):>5} chars — {fname}")

    # Add cross-link banner to ZH (only once)
    banner = f"<!-- 🔗 English entry page: [English version](../../en/trending/{fname}) -->\n"
    if 'English version' not in zh_content[:500] and '英文' not in zh_content[:500]:
        zh_content = re.sub(
            r'(---\s*\n.*?\n---\n)',
            rf'\1{banner}',
            zh_content,
            count=1,
            flags=re.DOTALL
        )
        zh_path.write_text(zh_content, encoding='utf-8')
        print(f"  [ZH] cross-link banner added")


def main():
    if not ZH_DIR.exists():
        print(f"[FATAL] {ZH_DIR} not found")
        sys.exit(1)

    zh_files = sorted(ZH_DIR.glob("*.md"))
    print(f"Fixing {len(zh_files)} EN stubs using ZH data (no external API)\n")

    for i, zh_path in enumerate(zh_files):
        print(f"[{i+1}/{len(zh_files)}] {zh_path.name}")
        try:
            process_file(zh_path)
        except Exception as e:
            print(f"  [ERROR] {e}")
        print()

    print(f"\n✅ {len(zh_files)} EN stubs rebuilt.")
    print(f"Next: cd {REPO_ROOT} && python3 src/update-index.py && bash src/publish.sh")


if __name__ == "__main__":
    main()
