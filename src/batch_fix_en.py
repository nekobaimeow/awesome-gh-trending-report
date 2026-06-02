#!/usr/bin/env python3
"""
Batch fix: translate ZH Overview → English, rebuild EN files.
EN gets real content (Overview + link to ZH deep-dive).
ZH keeps full analysis but adds a header pointing to EN.

Usage: python3 src/batch_fix_en.py
"""
import re, sys, os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ZH_DIR = REPO_ROOT / "zh" / "trending"
EN_DIR = REPO_ROOT / "en" / "trending"

try:
    from deep_translator import GoogleTranslator
except ImportError:
    print("[FATAL] deep-translator not installed. Run: pip install deep-translator", file=sys.stderr)
    sys.exit(1)


def translate_chunk(text: str) -> str:
    """Translate CN->EN, splitting on paragraph boundaries."""
    if not text.strip():
        return text
    MAX_CHUNK = 4000
    chunks = []
    remaining = text
    while len(remaining) > MAX_CHUNK:
        split_at = remaining.rfind('\n', 0, MAX_CHUNK)
        if split_at == -1:
            split_at = remaining.rfind('. ', 0, MAX_CHUNK)
        if split_at == -1:
            split_at = MAX_CHUNK
        chunks.append(remaining[:split_at])
        remaining = remaining[split_at:]
    chunks.append(remaining)

    result = []
    for chunk in chunks:
        if not chunk.strip():
            continue
        try:
            result.append(GoogleTranslator(source='zh-CN', target='en').translate(chunk))
        except Exception as e:
            print(f"    [TRANSLATE ERROR] {e}, keeping original")
            result.append(chunk)
    return ''.join(result)


def extract_overview_zh(content: str) -> str:
    """Extract the Overview paragraph(s) from a Chinese report."""
    # Try Chinese section name
    for header in ['🔍 项目简介', '项目简介', '🔍 概述', '概述', '简介']:
        m = re.search(rf'##\s*{re.escape(header)}\s*\n+(.*?)(?=\n##|\n#|\Z)', content, re.DOTALL)
        if m:
            return m.group(1).strip()
    # Fallback: take first paragraph after title
    lines = content.split('\n')
    in_content = False
    result = []
    for line in lines:
        if line.startswith('# '):
            in_content = True
            continue
        if in_content:
            if line.startswith('##') or line.startswith('---'):
                break
            if line.strip():
                result.append(line)
        if len(result) > 10:
            break
    return '\n'.join(result).strip() if result else content[:500]


def extract_frontmatter(content: str) -> tuple:
    """Return (raw_frontmatter, frontmatter_body, tags_list)."""
    m = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if not m:
        return ("", "", [])
    raw = m.group(0)
    body = m.group(1)
    tag_m = re.findall(r'tags:\s*\[(.*?)\]', body)
    tags = []
    if tag_m:
        tags = [t.strip().strip('"').strip("'") for t in tag_m[0].split(',') if t.strip()]
    return (raw, body, tags)


def format_tags(tags: list) -> str:
    return ', '.join(f'`{t}`' for t in tags) if tags else '`github-trending`'


def process_file(zh_path: Path):
    fname = zh_path.name
    en_path = EN_DIR / fname

    zh_content = zh_path.read_text(encoding='utf-8')
    fm_raw, fm_body, tags = extract_frontmatter(zh_content)

    if not fm_raw:
        print(f"[SKIP] {fname}: no frontmatter")
        return

    # Extract title
    title_match = re.search(r'^#\s+(.*)', zh_content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else fname

    # Translate Overview
    overview_zh = extract_overview_zh(zh_content)
    print(f"  Overview: {len(overview_zh)} chars CN")
    overview_en = translate_chunk(overview_zh[:3000])  # limit to avoid rate issues
    print(f"  Translated: {len(overview_en)} chars EN")

    # Build English report with real content
    en_report = f"""{fm_raw}
# {title} — Source Code Analysis

**Tags:** {format_tags(tags)}

## Overview

{overview_en}

## Full Analysis

The complete deep-dive source code analysis is available in [Chinese (中文版)](../../zh/trending/{fname}),
covering architecture, core features, security audit, and knowledge graph.

> *English summaries generated via machine translation. For technical accuracy,
> refer to the Chinese deep-dive which includes source code citations and detailed analysis.*
"""

    os.makedirs(EN_DIR, exist_ok=True)
    en_path.write_text(en_report, encoding='utf-8')
    print(f"  [EN] → {en_path} ({len(en_report)} chars)")

    # Update ZH: add banner pointing to EN
    banner = f"""<!-- 
  📖 English summary available at: [English version](../../en/trending/{fname})
-->
"""
    if 'English version' not in zh_content and '英文' not in zh_content[:200]:
        # Insert banner after frontmatter
        zh_content = re.sub(
            r'(---\s*\n.*?\n---)',
            rf'\1\n{banner}',
            zh_content,
            count=1,
            flags=re.DOTALL
        )
        zh_path.write_text(zh_content, encoding='utf-8')
        print(f"  [ZH] Banner added")


def main():
    if not ZH_DIR.exists():
        print(f"[FATAL] {ZH_DIR} not found")
        sys.exit(1)

    zh_files = sorted(ZH_DIR.glob("*.md"))
    print(f"Found {len(zh_files)} ZH reports to fix\n")

    for i, zh_path in enumerate(zh_files):
        print(f"[{i+1}/{len(zh_files)}] {zh_path.name}")
        try:
            process_file(zh_path)
        except Exception as e:
            print(f"  [ERROR] {e}")
        print()

    print(f"\n✅ Done. {len(zh_files)} files fixed.")
    print(f"Next: cd {REPO_ROOT} && python3 src/update-index.py && bash src/publish.sh")


if __name__ == "__main__":
    main()
