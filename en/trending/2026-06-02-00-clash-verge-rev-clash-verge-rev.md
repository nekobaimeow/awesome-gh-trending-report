---
tags: [github-trending, rust, typescript]
date: 2026-06-02
---
# clash-verge-rev/clash-verge-rev 源码分析 — Source Code Analysis

> **Tags:** `github-trending`, `rust`, `typescript` | **Date:** 2026-06-02
> 📝 `TypeScript` | 📄 `GPL-3.0`

## Overview

`clash-verge-rev` 是一个基于 Tauri 2 的跨平台桌面代理客户端，核心目标是把 Mihomo/Clash 内核的订阅管理、运行时配置增强、系统代理/TUN、连接监控、流媒体解锁测试和备份恢复整合到一个原生 GUI 里。目标用户是需要长期管理多订阅、多平台代理策略的桌面用户。技术栈上，前端是 React 19 + TypeScript + Vite + MUI（`package.json:5-35,36-80`），后端是 Rust + Tauri 2（`src-tauri/src/lib.rs:35-72`），并通过 `tauri-plugin-mihomo`、warp、本地 sidecar/service 完成与 Mihomo 内核和系统代理的交互。和 Clash for Windows 这类 Electron 客户端相比，它更偏 Tauri/Rust，本地能力更重，系统集成更深。

## What's Inside

- 🔍 项目简介
- ⚡ 核心功能
- 🗺️ 知识图谱（Mermaid）
- 🔐 安全审计
- 🚀 快速上手
- ⚖️ 一句话判词
- 📊 元信息

---

📖 **Full deep-dive analysis (Chinese):** [2026-06-02-00-clash-verge-rev-clash-verge-rev.md](../../zh/trending/2026-06-02-00-clash-verge-rev-clash-verge-rev.md)
