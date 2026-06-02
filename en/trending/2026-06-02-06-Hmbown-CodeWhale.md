---
tags: [cli-tool, github-trending, llm, rust, typescript]
date: 2026-06-02
---
# Hmbown/CodeWhale 源码分析 — Source Code Analysis

> **Tags:** `cli-tool`, `github-trending`, `llm`, `rust`, `typescript` | **Date:** 2026-06-02
> 📝 ":"en"}' | 📄 `MIT`

## Overview

CodeWhale 是一个以 Rust workspace 为核心的终端编码 agent monorepo：`codewhale` 负责 CLI 调度，`codewhale-tui` 承担交互式 TUI 与工具执行，`app-server` 提供 HTTP/stdio 传输层，`web/` 是基于 Next.js + Cloudflare Workers 的社区站，`integrations/feishu-bridge/` 则把本地 runtime 暴露给飞书/ Lark 手机聊天入口。它解决的不是“让模型回答问题”，而是“让模型在本地工作区里带着工具、状态、审批策略和外部入口完成编码任务”。目标用户是需要开源、可自托管、可脚本化的 DeepSeek/MiMo 编码代理用户；和只包一层聊天 CLI 的竞品相比，这个仓库把工具面、状态库、HTTP transport、社区自动化和移动桥接都做进了同一套源码里。

## What's Inside

- 🔍 项目简介
- ⚡ 核心功能
- 🗺️ 知识图谱（Mermaid）
- 🔐 安全审计
- 🚀 快速上手
- ⚖️ 一句话判词
- 📊 元信息

---

📖 **Full deep-dive analysis (Chinese):** [2026-06-02-06-Hmbown-CodeWhale.md](../../zh/trending/2026-06-02-06-Hmbown-CodeWhale.md)
