#!/usr/bin/env python3
"""
Batch flip existing reports: translate ZH→EN, make ZH stubs.
Uses deep-translator (Google Translate, free).
Install: pip install deep-translator
"""
import re, sys, os
from pathlib import Path
from datetime import date

REPO_ROOT = Path(__file__).resolve().parent.parent
ZH_DIR = REPO_ROOT / "zh" / "trending"
EN_DIR = REPO_ROOT / "en" / "trending"

# ── Translation ────────────────────────────────────────────────────

def translate_text(text: str) -> str:
    """Translate Chinese to English using Google Translate."""
    try:
        from deep_translator import GoogleTranslator
        # Split into chunks of 4000 chars to avoid API limits
        chunks = []
        while len(text) > 4000:
            # split at paragraph boundary
            split_at = text.rfind('\n', 0, 4000)
            if split_at == -1:
                split_at = 4000
            chunks.append(text[:split_at])
            text = text[split_at:]
        chunks.append(text)

        translated = []
        for chunk in chunks:
            result = GoogleTranslator(source='zh-CN', target='en').translate(chunk)
            translated.append(result)
        return ''.join(translated)
    except ImportError:
        print("[FATAL] deep-translator not installed. Run: pip install deep-translator", file=sys.stderr)
        sys.exit(1)


def extract_sections(content: str) -> dict:
    """Extract named sections from markdown content."""
    sections = {}
    current_section = "preamble"
    current_lines = []

    for line in content.split('\n'):
        m = re.match(r'^##\s+(.*)', line)
        if m:
            if current_lines:
                sections[current_section] = '\n'.join(current_lines).strip()
            current_section = m.group(1).strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        sections[current_section] = '\n'.join(current_lines).strip()

    return sections


# ── Main ───────────────────────────────────────────────────────────

def process_file(zh_path: Path):
    """Translate one ZH report to English, write both files."""
    fname = zh_path.name
    en_path = EN_DIR / fname

    content = zh_path.read_text(encoding='utf-8')
    sections = extract_sections(content)

    # Extract frontmatter
    fm_match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if not fm_match:
        print(f"[SKIP] {fname}: no frontmatter")
        return
    frontmatter_raw = fm_match.group(0)
    frontmatter_body = fm_match.group(1)

    # Translate title
    title_match = re.search(r'^#\s+(.*)', content, re.MULTILINE)
    title_zh = title_match.group(1) if title_match else fname
    title_en = title_zh  # keep as-is, project names don't translate

    # Build English report
    en_parts = [frontmatter_raw]
    en_parts.append(f"# {title_en} — Source Code Analysis\n")

    # Translate each section
    for section_name, section_text in sections.items():
        if not section_text.strip():
            continue
        if section_name == "preamble":
            en_parts.append(section_text + "\n")
            continue

        en_parts.append(f"## {section_name}\n")
        if section_name in ("💡 一句话判词", "🔍 项目简介",
                           "Overview", "Verdict",
                           "📊 元信息", "Meta",
                           "🚀 快速上手", "Quick Start",
                           "🗺️ 知识图谱（Mermaid）", "Architecture Graph (Mermaid)",
                           "🔐 安全审计", "Security Audit",
                           "⚡ 核心功能", "Core Features"):
            # Translate these sections
            print(f"  Translating: {section_name} ({len(section_text)} chars)...")
            translated = translate_text(section_text)
            en_parts.append(translated + "\n")
        else:
            # Keep code blocks, mermaid, etc. as-is
            en_parts.append(section_text + "\n")

    en_content = '\n'.join(en_parts)

    # Write English report
    os.makedirs(EN_DIR, exist_ok=True)
    en_path.write_text(en_content, encoding='utf-8')
    print(f"[EN] Wrote {len(en_content)} chars → {en_path}")

    # Build tags string for stub
    tag_match = re.findall(r'tags:\s*\[(.*?)\]', frontmatter_body)
    if tag_match:
        raw_tags = tag_match[0].replace('"','').replace("'","")
        tags_display = ', '.join(f'`{t.strip()}`' for t in raw_tags.split(','))
    else:
        tags_display = '`github-trending`'

    # Write Chinese stub
    zh_stub = f"""{frontmatter_raw}
# {title_zh} — 源码深度分析

**标签:** {tags_display}

## 概述

对 **{title_zh}** 的源码深度分析。

---

*完整英文分析报告请见 [English version](../../en/trending/{fname}).*
"""
    zh_path.write_text(zh_stub, encoding='utf-8')
    print(f"[ZH] Stub → {zh_path}")


def main():
    if not ZH_DIR.exists():
        print(f"[FATAL] {ZH_DIR} not found")
        sys.exit(1)

    zh_files = sorted(ZH_DIR.glob("*.md"))
    print(f"Found {len(zh_files)} ZH reports to flip\n")

    for i, zh_path in enumerate(zh_files):
        print(f"[{i+1}/{len(zh_files)}] {zh_path.name}")
        try:
            process_file(zh_path)
        except Exception as e:
            print(f"  [ERROR] {e}")
        print()

    print(f"\n✅ Done. {len(zh_files)} files flipped.")
    print("Run: cd {0} && python3 src/update-index.py && bash src/publish.sh".format(REPO_ROOT))


if __name__ == "__main__":
    main()
