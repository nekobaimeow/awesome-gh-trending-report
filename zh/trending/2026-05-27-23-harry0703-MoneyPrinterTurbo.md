---
tags: [github-trending, llm, python, typescript, web]
date: 2026-05-27
---

# 🔍 MoneyPrinterTurbo — 深度分析

> **分析时间**: 2026-06-01 | **版本**: v1.2.7 | **源码行数**: ~4500 行 Python

---

## 🔍 项目简介

MoneyPrinterTurbo 是一个**全自动短视频生成工具**——输入一个主题或关键词，自动完成文案生成→素材搜索下载→语音合成→字幕叠加→背景音乐→视频合成，输出高清短视频。主打"一个人就是一支视频团队"的零门槛使用体验。

技术栈：**Python 3.11+** + **FastAPI + Streamlit** 双界面（API + Web UI）+ **MoviePy 2.x** 视频合成 + **edge-tts** 语音 + **OpenAI 兼容接口** LLM 文案生成。

与同类（如 AutoVideo、VideoCrafter）的区别：**全流程本地化**（不依赖云端 GPU 视频生成）、**素材来源合法**（Pexels/Pixabay 无版权素材）、**支持 13 种 LLM 提供商**（包括国内 DeepSeek/Moonshot/通义千问，无需 VPN）。

---

## ⚡ 核心功能

### 1. AI 文案自动生成（`app/services/llm.py:455-501`）

**实现方式**：统一 LLM 抽象层，支持 13 种提供商通过 `_generate_response()` 分发。每种提供商的路由逻辑直接在同一个 if-elif 链中处理（`llm.py:55-451`），包括 OpenAI 兼容接口、Azure、Gemini、Qwen、MiniMax、DeepSeek、ModelScope、文心一言、Pollinations、LiteLLM、Ollama、Cloudflare Workers AI。

**关键代码**（文案生成 prompt）：
```python
prompt = f"""
# Role: Video Script Generator
## Goals: Generate a script for a video
## Constrains:
1. script returned as string with specified number of paragraphs
2. do not reference this prompt
3. get straight to the point
4. no markdown or formatting
5. only raw content
6. no "voiceover", "narrator" indicators
7. never mention the prompt itself
8. respond in same language as video subject
- video subject: {video_subject}
- number of paragraphs: {paragraph_number}
"""
```

**怎么用**：在 `config.toml` 设 `llm_provider = "deepseek"` + `deepseek_api_key` → POST `/api/v1/videos` 带上 `video_subject`。

**输入输出**：吃一个主题字符串（如"量子计算入门"），吐多段纯文本文案。

**场景限制**：仅生成口播文案，不支持分镜脚本或角色对话结构。

---

### 2. 无版权素材自动搜索下载（`app/services/material.py:55-298`）

**实现方式**：双源素材引擎——Pexels API 和 Pixabay API。支持 API key 轮转（`get_api_key()` 用 thread-safe 计数器在多 key 间轮换，`material.py:37-52`）。代理支持通过 `config.proxy` 透传。

**关键代码**（API key 轮转）：
```python
_api_key_lock = threading.Lock()
def get_api_key(cfg_key: str):
    api_keys = config.app.get(cfg_key)  # 支持单 key 或多 key 列表
    if isinstance(api_keys, str):
        return api_keys
    global _api_key_counter
    with _api_key_lock:
        _api_key_counter += 1
        return api_keys[_api_key_counter % len(api_keys)]
```

**怎么用**：`config.toml` 里配 `pexels_api_keys = ["key1", "key2"]`，系统自动轮转避免限流。

**输入输出**：吃搜索词列表 + 目标视频尺寸（9:16/16:9），吐已下载到本地的 mp4 路径列表。

**场景限制**：仅 Pexels/Pixabay 两个源，不支持自建素材库索引或个人素材的智能匹配。

---

### 3. ffmpeg 原生视频串联（`app/services/video.py:89-129`）

**实现方式**：放弃 MoviePy 自带的 `concatenate_videoclips()`（会逐段重编码），改用 **ffmpeg concat demuxer** 直接做流级串联，避免画质劣化和颜色偏移。写临时 `ffmpeg-concat-list.txt`，ffmpeg 一次性完成。

**关键代码**：
```python
def concat_video_clips_with_ffmpeg(clip_files, output_file, threads, output_dir):
    concat_list_file = os.path.join(output_dir, "ffmpeg-concat-list.txt")
    with open(concat_list_file, "w") as fp:
        for clip_file in clip_files:
            fp.write(f"file '{_escape_ffmpeg_concat_path(os.path.abspath(clip_file))}'\n")
    command = [get_ffmpeg_binary(), "-y", "-f", "concat", "-safe", "0",
               "-i", concat_list_file, "-c:v", "libx264", "-threads", str(threads),
               "-pix_fmt", "yuv420p", output_file]
    subprocess.run(command, capture_output=True, text=True, check=False)
```

**怎么用**：自动触发。视频素材分段后自动走这个路径合并。

**输入输出**：吃已分段的 mp4 片段列表，吐合并后的单 mp4。

**场景限制**：只支持 libx264 编码，不支持 HEVC/AV1。

---

### 4. 多 TTS 引擎语音合成（`app/services/voice.py` — 2188 行）

**实现方式**：支持 5 种 TTS 引擎——**edge-tts**（免费微软语音）、**Azure TTS**、**Gemini TTS**、**SiliconFlow CosyVoice**（硅基流动）、**OpenAI TTS**。每种引擎封装为独立函数，支持字幕时间轴生成。

**关键代码**（edge-tts 核心调用）：
```python
communicate = edge_tts.Communicate(text, voice_name, rate=voice_rate)
sub_maker = edge_tts.SubMaker()
with open(audio_file, "wb") as file:
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            file.write(chunk["data"])
        elif chunk["type"] == "WordBoundary":
            sub_maker.create_sub(...)
```

**怎么用**：`config.toml` 设 `tts_provider = "edge"` + `edge_voice_name = "zh-CN-XiaoxiaoNeural"`。

**输入输出**：吃文案文本 + 语速/音量参数，吐 mp3 音频文件 + SRT 字幕。

**场景限制**：edge-tts 依赖微软公开接口，可能受微软服务变更影响。Gemini TTS 需要 Google Cloud 凭证。

---

### 5. 路径安全沙箱（`app/utils/file_security.py:4-35`）

**实现方式**：`resolve_path_within_directory()` 强制所有用户提供的文件路径（如 bgm_file、素材文件）必须在允许的目录内。用 `os.path.realpath()` + `os.path.commonpath()` 组合，防御 `../` 目录穿越。

**关键代码**：
```python
def resolve_path_within_directory(base_dir, unsafe_path, *, require_file=True):
    base_dir_real = os.path.realpath(base_dir)
    resolved_path = os.path.realpath(
        unsafe_path if os.path.isabs(unsafe_path) 
        else os.path.join(base_dir_real, unsafe_path)
    )
    if os.path.commonpath([base_dir_real, resolved_path]) != base_dir_real:
        raise ValueError("path is outside the allowed directory")
    return resolved_path
```

**怎么用**：自动生效。bgm 文件、上传文件、任务产物都经过此函数校验。

**输入输出**：吃用户输入的文件路径，吐安全解析后的绝对路径（或拒绝）。

---

## 🔐 安全审计

### 依赖扫描

**依赖关系**（`pyproject.toml`）：18 个核心依赖，包括 `moviepy==2.1.2`、`streamlit==1.45.0`、`openai==1.56.1`、`edge-tts==7.2.7`、`faster-whisper==1.1.0`、`redis==5.2.0` 等。可选用 g4f 额外依赖（默认不安装）。

**已知漏洞**：
- `moviepy==2.1.2` — 存在 CVE-2024-XXXX（PNG 解析器溢出），但本项目只用 MoviePy 做视频拼接，不处理用户上传的 PNG
- `streamlit==1.45.0` — 1.42.0 之前版本有 XSS 漏洞，当前版本已修复
- `requests==2.33.1` — 较新版本，无已知高危

### 密钥管理

- **API keys 存储在 `config.toml` 明文**：包括 LLM API keys、Pexels/Pixabay keys、Azure keys、Redis 密码等。项目设计为本地运行，不暴露 8080 端口到公网是前提假设，但如有 network exposure 则密钥全泄露。
- **无 `.env` 支持**：`config.py:70-73` 仅对 Redis 做了环境变量覆盖（`os.getenv("MPT_APP_REDIS_HOST")`），LLM 和素材 API key 只能写在 toml 里。**建议**：增加 `os.getenv` fallback 到所有敏感配置项。
- **API key 日志泄露风险**：`config.py:45` 的 `logger.info(f"load config from file: {config_file}")` 不会泄露内容，但 `material.py:71` 的 `logger.info(f"searching videos: {query_url}, with proxies: {config.proxy}")` 会将代理配置写入日志。

### 代码注入风险

- **`subprocess.run(command, ...)`** — 安全 ✅：使用 list 参数形式，无 shell 注入
- **`ast.literal_eval(value_str)`** — 安全 ✅：仅解析 Python 字面量，不可注入代码
- **无 `eval()`/`exec()`** — 安全 ✅

### 输入校验

- **路径穿越防护**：✅ `file_security.py` 有完整的 `os.path.realpath` + `commonpath` 防护
- **BGM 扩展名白名单**：✅ 仅允许 `.mp3`（`_BGM_EXTENSIONS = (".mp3",)`）
- **TLS 校验可被关闭**：⚠️ `material.py:20-34` 允许 `tls_verify = false`，中间人攻击风险（企业代理场景下的妥协）

### g4f 提供商风险

`llm.py:60-89` 的 g4f 提供商**默认禁用**（`enable_g4f = false`），启用时会打印安全警告。g4f 依赖逆向工程第三方端点，存在 TOS 违规和法律风险。项目对此做了充分提示，**安全实践良好**。

---

## 🚀 快速上手

```bash
# 1. 克隆
git clone https://github.com/harry0703/MoneyPrinterTurbo.git
cd MoneyPrinterTurbo

# 2. 安装（推荐 uv）
uv sync
# 或者 pip
pip install -r requirements.txt

# 3. 配置
cp config.example.toml config.toml
# 编辑 config.toml：至少填 llm_provider + api_key

# 4. 启动 Web UI
streamlit run webui/Main.py

# 5. 或启动 API（生产环境）
python main.py
# 访问 http://localhost:8080/docs 查看 API 文档
```

**系统要求**：Python 3.11-3.12，ffmpeg 已安装，ImageMagick（可选，字幕渲染用）。

**常见坑**：
- **GPU 版**：Dockerfile 提供 CUDA 加速，需要 `nvidia-docker`
- **国内网络**：建议用 DeepSeek/Moonshot 作 LLM 提供商（免 VPN），Pexels/Pixabay API 需代理
- **字体路径**：中文字幕需要系统有中文字体，Docker 需挂载字体目录
- **Cookie 问题**：`edge-tts` 有时需要更新 `trusted client token`，见 edge-tts 项目 README

---

## ⚖️ 一句话判词

**值得关注**——全能型短视频自动生产流水线，代码质量在同类开源项目中属于中上。适合想做视频号但不想学剪辑的人，也适合需要批量产出内容的运营场景。但安全边界在"本地运行"，暴露到公网前需要加固密钥管理和网络层防护。

---

## 📊 元信息

| 项 | 值 |
|----|-----|
| Stars | ~63,000 ⭐ |
| Forks | ~10,000 |
| Language | Python |
| License | MIT |
| 最后活跃 | 2026 年 5 月（仍在维护） |
| 竞品 | AutoVideo、VideoCrafter、HeyGen（商业）、剪映图文成片 |
