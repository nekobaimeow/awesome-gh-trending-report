---
tags: [cli-tool, github-trending, llm, python, typescript]
date: 2026-06-01
---
# KylinMountain/TradingAgents-AShare 源码分析 — Source Code Analysis

> **Tags:** `cli-tool`, `github-trending`, `llm`, `python`, `typescript` | **Date:** 2026-06-01
> 📝 Graph | 📄 GitHub

## Overview

`KylinMountain/TradingAgents-AShare` 是一个面向 A 股场景的多智能体投研系统：后端用 `FastAPI` 暴露分析、报告、持仓、调度、认证等接口，核心推理由 `LangGraph + LangChain` 驱动的 15 个 Agent 协作完成，行情/新闻/资金面主要依赖 `AkShare / BaoStock / yfinance`，前端则是 `React + Vite + Zustand`。它解决的不是“单次问答”，而是“把股票分析做成可持续运营的服务”：支持登录、持仓导入、定时任务、看板、报告落库。和上游 `TauricResearch/TradingAgents` 相比，这个仓库已经明显产品化，重点是 A 股数据接入、Web 端体验和任务调度链路，而不是通用 CLI 框架。

## What's Inside

- 🔍 项目简介
- ⚡ 核心功能
- 🗺️ 知识图谱（Mermaid）
- 🔐 安全审计
- 🚀 快速上手
- ⚖️ 一句话判词
- 📊 元信息

---

📖 **Full deep-dive analysis (Chinese):** [2026-06-01-23-KylinMountain-TradingAgents-AShare.md](../../zh/trending/2026-06-01-23-KylinMountain-TradingAgents-AShare.md)
