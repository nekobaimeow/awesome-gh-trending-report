---
tags: [ai-agents, github-trending, llm, python]
date: 2026-06-01
---
# GordenSun/GordenPPTSkill 源码分析报告 — Source Code Analysis

> **Tags:** `ai-agents`, `github-trending`, `llm`, `python` | **Date:** 2026-06-01
> ⭐ 1273 | 🍴 118 | 📝 Python | 📄 `

## Overview

这是一个面向 AI Agent 的 PPT 生成/编辑技能包，本体由 19 套内置 `.pptx` 模板、模板元数据 `detail.json`、以及一组离线 Python 脚本组成。它解决的不是“从零画幻灯片”，而是“在不破坏原始版式/配色/字号的前提下，按模板快速裁页、替换文本、生成新的 `.pptx`”。目标用户主要是需要批量做中文工作汇报、述职竞聘、开题答辩、教学课件的人，以及调用该 Skill 的 Agent。技术栈是 Python 3 + `python-pptx` + JSON 元数据，预览环节依赖 LibreOffice / `pdftoppm`。和 Canva / Gamma / Marp 这类重绘式方案不同，它的核心路线是“直接改现成 PPTX 模板里的指定 run，并保留设计师原版排版”。

## What's Inside

- 🔍 项目简介
- ⚡ 核心功能
- 🔐 安全审计
- 🚀 快速上手
- ⚖️ 一句话判词
- 📊 元信息

---

📖 **Full deep-dive analysis (Chinese):** [2026-06-01-19-GordenSun-GordenPPTSkill.md](../../zh/trending/2026-06-01-19-GordenSun-GordenPPTSkill.md)
