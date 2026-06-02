---
tags: [github-trending, security, typescript, web]
date: 2026-06-01
---
# excalidraw/excalidraw 源码分析报告 — Source Code Analysis

> **Tags:** `github-trending`, `security`, `typescript`, `web` | **Date:** 2026-06-01
> 📝 `TypeScript` | 📄 `MIT`

## Overview

`excalidraw/excalidraw` 是一个用 TypeScript/React 实现的手绘风白板项目，同时包含可嵌入的编辑器库 `packages/excalidraw` 和官方演示/云能力外壳 `excalidraw-app`。它解决的是“快速画出结构图、流程图、线框图，同时还能分享、协作、导出、复用素材”的问题，目标用户既包括直接在网页上画图的终端用户，也包括想把白板能力嵌入自家产品的前端团队。技术栈核心是 React 19、TypeScript、Vite、Jotai、Firebase、Socket.IO 和浏览器 Web Crypto。竞品可以类比 tldraw、draw.io，但 Excalidraw 的差异在于手绘风、本地优先、开放 JSON 格式和把协作加密逻辑也做进了前端实现。

## What's Inside

- 🔍 项目简介
- ⚡ 核心功能
- 🔐 安全审计
- 🚀 快速上手
- ⚖️ 一句话判词
- 📊 元信息

---

📖 **Full deep-dive analysis (Chinese):** [2026-06-01-17-excalidraw-excalidraw.md](../../zh/trending/2026-06-01-17-excalidraw-excalidraw.md)
