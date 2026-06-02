---
tags: [ai-agents, github-trending, llm, rust, typescript]
date: 2026-06-02
---
# dmtrKovalenko/fff 源码分析 — Source Code Analysis

> **Tags:** `ai-agents`, `github-trending`, `llm`, `rust`, `typescript` | **Date:** 2026-06-02
> ⭐ 7119 | 🍴 298 | 📝 的。 | 📄 MIT

## Overview

`dmtrKovalenko/fff` 是一个“常驻型”文件搜索工具包：核心是 Rust 写的索引与搜索引擎，外面包了 Neovim 插件、MCP 服务器、Node/Bun SDK。它解决的问题不是“单次 grep”，而是编辑器或 AI agent 在同一仓库里连续做几十次到几百次搜索时，反复 fork `rg`/`fzf` 太慢、上下文不连贯的问题。目标用户是 Neovim 用户、AI coding agent、需要嵌入式文件搜索能力的 Node/Rust 工具作者。技术栈是 Rust 工作区（`fff-core`/`fff-mcp`/`fff-nvim`/`fff-query-parser`/`fff-c`）+ Lua + TypeScript。和 `ripgrep`/`fzf`/Telescope 一类工具相比，它的差异点是“长期驻留索引 + frecency 排序 + git 感知 + 给 AI 的 MCP/SDK 封装”。

## What's Inside

- 🔍 项目简介
- ⚡ 核心功能
- 🗺️ 知识图谱（Mermaid）
- 🔐 安全审计
- 🚀 快速上手
- ⚖️ 一句话判词
- 📊 元信息

---

📖 **Full deep-dive analysis (Chinese):** [2026-06-02-04-dmtrKovalenko-fff.md](../../zh/trending/2026-06-02-04-dmtrKovalenko-fff.md)
