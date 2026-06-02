---
tags: [ai-agents, github-trending, llm, python]
date: 2026-06-01
---

# GordenSun/GordenPPTSkill 源码分析报告

## 🔍 项目简介

这是一个面向 AI Agent 的 PPT 生成/编辑技能包，本体由 19 套内置 `.pptx` 模板、模板元数据 `detail.json`、以及一组离线 Python 脚本组成。它解决的不是“从零画幻灯片”，而是“在不破坏原始版式/配色/字号的前提下，按模板快速裁页、替换文本、生成新的 `.pptx`”。目标用户主要是需要批量做中文工作汇报、述职竞聘、开题答辩、教学课件的人，以及调用该 Skill 的 Agent。技术栈是 Python 3 + `python-pptx` + JSON 元数据，预览环节依赖 LibreOffice / `pdftoppm`。和 Canva / Gamma / Marp 这类重绘式方案不同，它的核心路线是“直接改现成 PPTX 模板里的指定 run，并保留设计师原版排版”。

## ⚡ 核心功能

### 1. 模板元数据建模：把 PPT 模板变成可编程资产

- 功能名称：模板页面、文本槽位、章节角色、图表位的结构化描述
- 实现方式：每套模板都带一份 `detail.json`。例如 `templates/minimal-business-summary/detail.json:23-37` 定义编辑规则、页面角色和可编辑槽位；`templates/data-viz-deck/detail.json:35-79` 进一步标记了原生图表所在页和 `shape_id`。

```json
"editing_rules": [
  "保留所有形状的位置/大小/字号/字体/颜色，只替换 run 文本。",
  "字数控制在 max_chars 以内，否则会被截断或换行变形。"
],
"page_roles": {
  "cover": [1],
  "agenda": [2],
  "section_divider": [3, 7, 10, 13],
  "content": [4, 5, 6, 8, 9, 11, 12, 14, 15],
  "ending": [16]
}
```

```json
"data_charts": [
  {
    "slide_number": 8,
    "chart_shape_ids": [120, 121],
    "guidance": "柱图 + 堆叠柱图，可用 chart_data 替换数据"
  }
]
```

- 怎么用：

```bash
python3 - <<'PY'
import json
d = json.load(open('templates/minimal-business-summary/detail.json', encoding='utf-8'))
print([(p['slide_number'], p['role']) for p in d['pages'][:5]])
PY
```

- 输入输出：输入是模板目录里的 `detail.json`；输出是一个足够细的模板描述对象，包含 `page_roles`、`text_slots`、`max_chars`、`level`、`data_charts` 等字段，供上层 Agent 选页、写 `edits.json`、做审计。
- 适用场景和限制：适合“先选模板，再程序化填充内容”的流水线。限制是这些元数据主要靠人工维护；虽然 `data_charts` 已经把图表位标出来了，但当前仓库里的 `scripts/build_pptx.py` 没有实际处理 `chart_data` 的代码分支，所以“图表数据改写”目前更像元数据预留，不算已落地能力。


### 2. 按 `selected_slides` 裁页并重排，输出新的 PPTX

- 功能名称：基于原模板页号的选页、删除、重排
- 实现方式：`scripts/build_pptx.py:179-196` 的 `prune_slides()` 直接操作 `prs.slides._sldIdLst`，先校验页号，再按新顺序重建 slide id 列表。它保留了原 XML element 实例，因此不会破坏页内的关系引用。

```python
def prune_slides(prs, selected_1indexed: list[int]) -> None:
    sldIdLst = prs.slides._sldIdLst
    sld_ids = list(sldIdLst)
    keep_idx0 = [i - 1 for i in selected_1indexed]
    ...
    for sld in list(sldIdLst):
        sldIdLst.remove(sld)
    for sld in new_order:
        sldIdLst.append(sld)
```

- 怎么用：

```bash
python3 scripts/build_pptx.py \
  templates/minimal-business-summary/template.pptx \
  edits.json \
  out/final.pptx \
  --detail templates/minimal-business-summary/detail.json \
  --strict
```

`edits.json` 里只要写：

```json
{
  "selected_slides": [1, 2, 3, 5, 7, 9, 10, 12, 13, 14, 16],
  "edits": []
}
```

- 输入输出：输入是 `template.pptx + edits.json`；输出是一个只保留目标页面的新 `.pptx` 文件。
- 适用场景和限制：适合从大模板里拼一份更短的演示稿。限制是所有页号都必须基于“原模板编号”，不是裁剪后的新编号；脚本会在 `scripts/build_pptx.py:183-186`、`212-215` 对越界页号直接报错。


### 3. 精确到 `shape/paragraph/run` 的换字，并尽量保住原格式

- 功能名称：按 `slot_id` 或显式 `address` 替换文本，不改位置/字号/颜色
- 实现方式：`scripts/build_pptx.py:58-74` 先把 `detail.json` 建成 `(slide_number, slot_id) -> slot` 索引；`scripts/build_pptx.py:139-173` 的 `apply_edit_to_shape()` 则区分“改单个 run”和“整段替换保留 run0 格式”两种模式。

```python
for page in detail.get("pages", []):
    slide_number = page["slide_number"]
    for slot in page.get("text_slots", []):
        slot.setdefault("expected_text", slot.get("current_text"))
        index[(slide_number, slot["slot_id"])] = slot
```

```python
if ri is None:
    runs[0].text = new_text
    for r in runs[1:]:
        r.text = ""
    return True, f"replaced paragraph ..."

runs[ri].text = new_text
return True, f"replaced run: {current!r} -> {new_text!r}"
```

- 怎么用：

```json
{
  "selected_slides": [1, 2, 3],
  "edits": [
    {"slide": 1, "slot_id": "cover_title_en", "new_text": "Annual Review"},
    {"slide": 1, "slot_id": "cover_title_cn", "new_text": "2026年度复盘"},
    {"slide": 2, "slot_id": "agenda_title_en", "new_text": "Agenda"}
  ]
}
```

或者直接显式寻址：

```json
{
  "slide": 1,
  "address": {"shape_id": 46, "paragraph": 1, "run": 0},
  "expected_text": "工作计划模板",
  "new_text": "2026年度复盘"
}
```

- 输入输出：输入是 `edits.json` 中的 `slide + slot_id/address + new_text`；输出是模板中对应文本 run 被替换后的 `.pptx`。
- 适用场景和限制：这是仓库最核心的落地功能，尤其适合“换文案但不能毁模板”的场景。我本地实跑了 `minimal-business-summary` 模板，成功生成了 3 页、8 处编辑的 `out.pptx`。限制是它只处理文本，不改图形、不调布局、不重算图表；`--strict` 下只要 `expected_text` 不匹配或 `shape_id` 找不到就会拒绝保存。


### 4. 真实几何容量计算 + 构建期出框检测

- 功能名称：按文本框尺寸和字号估算可容字符数，并在生成时拦截超长文案
- 实现方式：`scripts/compute_capacity.py:177-189` 用 `width_cm / height_cm / font_size_pt` 算 `chars_per_line`、`max_lines`、`max_chars`；`scripts/build_pptx.py:94-119` 与 `273-292` 则在真正替换文字时做 overflow lint。

```python
def capacity_for(width_cm: float, height_cm: float, size_pt: float,
                 wrap: bool) -> tuple[int, int, int]:
    usable_w_pt = max(0.0, (width_cm - H_MARGIN_CM)) * PT_PER_CM
    usable_h_pt = max(0.0, (height_cm - V_MARGIN_CM)) * PT_PER_CM
    cpl = max(1, math.floor(usable_w_pt / size_pt))
    max_lines = max(1, math.floor(usable_h_pt / (size_pt * LINE_HEIGHT))) if wrap else 1
    cap = max(1, math.floor(cpl * max_lines * TOLERANCE))
    return cpl, max_lines, cap
```

```python
if total_vw <= cap:
    return True, ""
...
if not args.no_lint and p["meta"]:
    fits, omsg = check_overflow(p["new_text"], p["meta"])
    if omsg and not fits:
        overflow_issues.append(line)
```

- 怎么用：

```bash
python3 scripts/compute_capacity.py \
  templates/minimal-business-summary/detail.json \
  templates/minimal-business-summary/template.pptx \
  -o /tmp/detail.out.json

python3 scripts/build_pptx.py \
  templates/minimal-business-summary/template.pptx \
  edits.json \
  out/final.pptx \
  --detail templates/minimal-business-summary/detail.json \
  --strict
```

- 输入输出：`compute_capacity.py` 输入 `detail.json + template.pptx`，输出补充了 `box_cm`、`font_size_pt`、`chars_per_line`、`max_lines`、`max_chars`、`level` 的新 JSON；`build_pptx.py` 则把这些容量字段作为 lint 基础，输出带告警或直接失败的构建结果。
- 适用场景和限制：适合把“字数别太多”变成机器可执行的约束，而不是靠肉眼拍脑袋。我本地实跑后得到 `16 pages, 138 slots, 14 size tiers`。限制是组合框、自动增长文本框等不可靠几何对象会被标成 `capacity_unknown`（见 `scripts/compute_capacity.py:224-232`），这类槽位 lint 会跳过；`autofit` 也只会给软提示，不会真的改字号。


### 5. 把 PPTX 渲染成逐页 PNG 预览

- 功能名称：幻灯片预览图生成
- 实现方式：`scripts/render_slides.py:19-56` 先调用 `soffice --convert-to pdf` 把 PPTX 转成 PDF，再用 `pdftoppm -png` 拆成每页 PNG。

```python
subprocess.run(
    ["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(td_path), str(pptx)],
    check=True,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.PIPE,
)
...
subprocess.run(
    ["pdftoppm", "-png", "-r", str(dpi), str(pdf), str(out_dir / "slide")],
    check=True,
)
```

- 怎么用：

```bash
python3 scripts/render_slides.py out/final.pptx out/renders --dpi 144
```

- 输入输出：输入是任意 `.pptx` 和输出目录；输出是 `slide-1.png`、`slide-2.png` 这类预览图。
- 适用场景和限制：适合发给用户预览、做 QA、自检有无溢出。限制是强依赖系统二进制；我在当前分析环境实际执行时，因 `soffice` 不在 `PATH` 直接失败，所以这个脚本不是“纯 Python 开箱即用”。


### 6. 版本检查、增量更新与文件完整性清单

- 功能名称：Skill 自更新与文件哈希清单
- 实现方式：`scripts/check_update.py:39-45` / `47-76` 从 `updates.json` 指向的远端抓取版本信息；`scripts/apply_update.py:79-129` 和 `132-220` 根据版本差异只拉增量文件；`scripts/build_manifest.py:64-87` 重新计算所有文件的 SHA-256 并写回 `manifest.json`。

```python
url = source.rstrip("/") + "/updates.json"
with urllib.request.urlopen(url, timeout=30) as resp:
    return json.loads(resp.read().decode("utf-8"))
```

```python
for f in sorted(added | modified):
    dest = root / f
    dest.parent.mkdir(parents=True, exist_ok=True)
    data = fetch_bytes(source, f"files/{f}")
    dest.write_bytes(data)
```

```python
entry = {
    "sha256": sha,
    "size": p.stat().st_size,
    "version_added": prev.get("version_added", version),
    "last_modified": version if prev.get("sha256") != sha else prev.get("last_modified", version),
}
```

- 怎么用：

```bash
python3 scripts/check_update.py
python3 scripts/apply_update.py --dry-run
python3 scripts/build_manifest.py --skill-root .
```

- 输入输出：更新检查输入是本地 `VERSION` / `updates.json` 和远端 `updates.json`，输出是“是否有新版本、哪些文件会变”；应用更新则直接写本地文件；`build_manifest.py` 输入整个仓库目录，输出 `manifest.json`。
- 适用场景和限制：适合把 Skill 当作一个可分发的离线资产包维护。我本地实跑 `check_update.py`，结果为 `OK   Up to date (local=1.0.14, remote=1.0.14)`；`build_manifest.py` 也成功重建了 `manifest.json`。限制是它依赖远端仓库和网络，而且更新链路的路径校验做得不够严，这一点在安全审计里单独说。

## 🔐 安全审计

### 1. 依赖扫描

仓库里没有 `requirements.txt`、`pyproject.toml`、`package.json` 之类锁定依赖文件；我先根据 `scripts/*.py` 的真实 import 做了依赖识别，确认唯一直接第三方 Python 依赖是 `python-pptx`，其运行时依赖为 `lxml`、`Pillow`、`typing-extensions`、`XlsxWriter`。

实际执行的审计方式是：按当前环境真实安装版本重建最小依赖集后运行 `pip-audit`。

```bash
python3 -m pip show python-pptx lxml Pillow typing-extensions XlsxWriter

tmp=$(mktemp)
cat > "$tmp" <<'EOF'
python-pptx==1.0.2
lxml==6.1.0
Pillow==12.2.0
typing-extensions==4.15.0
XlsxWriter==3.2.9
EOF
python3 -m pip_audit -r "$tmp"
```

结果：`No known vulnerabilities found`。

- 已知漏洞总数：0
- 高危漏洞数：0
- 备注：这只能覆盖 Python 依赖；`render_slides.py` 依赖的 `soffice` / `pdftoppm` 是系统包，不在 `pip-audit` 覆盖范围内。

### 2. 密钥泄露扫描

我实际执行了以下模式扫描：

```bash
rg -n --glob '!/.git/**' -S '(AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{36}|sk-[A-Za-z0-9]{20,}|api[_-]?key|secret|token|password|passwd)' .
```

结果：0 条命中。

结论：项目源码和模板元数据里没有看到明显的 API Key、GitHub Token、OpenAI Key、明文密码一类硬编码凭据。`updates.json:4` 只有公开仓库地址 `git+https://github.com/GordenSun/GordenPPTSkill.git#main`，不属于秘密信息。

### 3. 认证 / 授权 / 会话 / CSRF

我实际执行了搜索：

```bash
rg -n --glob '!/.git/**' -S '(auth|authorization|session|csrf|middleware|login|jwt|cookie)' scripts SKILL.md references manifest.json updates.json templates
```

结果：0 条命中。

结论很直接：这不是一个 Web 服务，没有认证中间件、会话管理、Cookie、JWT、CSRF 防护这类逻辑。安全边界主要在“本地文件写入能力”和“远端更新链路信任”。换句话说，任何能执行这些脚本的人，天然就拥有对目标路径的本地读写能力。

### 4. 输入校验与数据暴露面

正向点：

- `scripts/build_pptx.py:183-186`、`212-215` 会校验 `selected_slides` 是否越界。
- `scripts/build_pptx.py:227-234` 会校验 `slot_id` 是否能在 `detail.json` 中解析出来。
- `scripts/build_pptx.py:155-170` 的 `expected_text + --strict` 能阻止模板漂移导致的误替换。
- `scripts/build_pptx.py:273-292` 会对文本出框给出告警，`--strict` 下直接拒绝保存。
- `scripts/compute_capacity.py:224-232` 会把几何不可信的槽位标成 `capacity_unknown`，避免误算。

主要风险点：

1. 高风险：更新脚本存在路径穿越 / 任意覆盖窗口  
`scripts/apply_update.py:102-123` 在 HTTP 更新模式里直接把远端文件名拼成 `dest = root / f`，随后 `dest.parent.mkdir(...)`、`dest.write_bytes(data)`；删除也直接 `dest.unlink()`。  
`scripts/apply_update.py:194-215` 的 git 更新模式也一样，`dst = root / f` 后直接复制/删除。  
这里没有做 `resolve()` 后的根目录包含性校验。如果远端 `updates.json` 或更新源被污染，理论上可以用诸如 `../../somewhere` 的路径写出仓库外。

2. 中风险：更新链路强信任远端，无签名校验  
`updates.json:4` 把更新源固定为 GitHub 仓库；`scripts/check_update.py:39-45`、`47-76` 会自动读取远端 `updates.json`；`scripts/apply_update.py:132-220` 在 git 模式下直接浅克隆并复制文件。  
HTTP 模式至少会尝试读取远端 `manifest.json` 做 SHA-256 对比（`scripts/apply_update.py:96-115`），但 git 模式没有等价的完整性校验。仓库被接管或供应链被污染时，本地会无条件信任远端内容。

3. 低到中风险：预览链路会把任意 PPTX 交给大型本地解析器  
`scripts/render_slides.py:23-54` 会调用 `soffice` 和 `pdftoppm` 处理传入的 `.pptx`。代码本身没有命令注入问题，因为它用的是参数列表，不是 shell 拼接；但如果拿这个脚本处理完全不可信的 Office 文件，风险会转移到 LibreOffice / Poppler 这些原生程序本身。

总体判断：这仓库的“运行时攻击面”不大，因为它不是联网服务；真正需要盯的是更新链路的供应链信任和路径校验，而不是传统 Web 安全问题。

## 🚀 快速上手

系统和依赖要求：

- Python 3.10+（代码里用了 `Path | None`、`list[int]` 等语法）
- Python 包：`python-pptx`
- 可选系统包：LibreOffice（提供 `soffice`）、Poppler（提供 `pdftoppm`）
- 可选工具：`git`；未来若模板重新启用 LFS，则 `git-lfs` 也可能需要

最小安装：

```bash
git clone https://github.com/GordenSun/GordenPPTSkill.git
cd GordenSun-GordenPPTSkill

python3 -m venv .venv
source .venv/bin/activate
pip install python-pptx
```

先检查更新：

```bash
python3 scripts/check_update.py
```

最小生成示例：

```bash
cat > edits.json <<'EOF'
{
  "template_slug": "minimal-business-summary",
  "selected_slides": [1, 2, 3],
  "edits": [
    {"slide": 1, "slot_id": "cover_title_en", "new_text": "Annual Review"},
    {"slide": 1, "slot_id": "cover_title_cn", "new_text": "2026年度复盘"},
    {"slide": 2, "slot_id": "agenda_title_cn", "new_text": "目录"},
    {"slide": 2, "slot_id": "agenda_title_en", "new_text": "Agenda"},
    {"slide": 2, "slot_id": "agenda_ch1_cn", "new_text": "重点工作"},
    {"slide": 2, "slot_id": "agenda_ch1_en", "new_text": "Highlights"},
    {"slide": 3, "slot_id": "div1_cn", "new_text": "重点工作"},
    {"slide": 3, "slot_id": "div1_en", "new_text": "Highlights"}
  ]
}
EOF

python3 scripts/build_pptx.py \
  templates/minimal-business-summary/template.pptx \
  edits.json \
  out.pptx \
  --detail templates/minimal-business-summary/detail.json \
  --strict
```

如果要渲染预览图：

```bash
python3 scripts/render_slides.py out.pptx renders --dpi 144
```

常见坑：

- 仓库没提供 `requirements.txt`，你需要自己装 `python-pptx`。
- `render_slides.py` 不是纯 Python；没有 `soffice` / `pdftoppm` 就跑不起来。
- `--strict` 很有用，但如果模板文件和 `detail.json` 已经不一致，会因为 `expected_text mismatch` 直接失败。
- `detail.json` 里的 `max_chars` 是硬约束思路，不是装饰字段；文案太长时应该缩句子，不是缩字号。
- `LICENSE` 只覆盖代码；`templates/` 的使用还要看 `NOTICE.md`，其中明确写了非商业使用限制。
- `data-viz-deck` 等模板虽然已经在 `detail.json` 标了很多 `data_charts`，但当前构建脚本并没有真实的图表数据写回实现，别把它当成现成功能。

## ⚖️ 一句话判词

值得关注，前提是你的目标是“拿现成 PPTX 模板做高保真自动填充”，而不是“用代码重新设计一套幻灯片”；它非常适合汇报类、答辩类、课件类场景，但对图表数据写回、供应链更新安全、以及商业使用合规性都要额外留神。

## 📊 元信息

- 仓库：`GordenSun/GordenPPTSkill`
- Stars：1273
- Forks：118
- Language：Python
- License：代码部分是 MIT（见 `LICENSE:1-28`），但模板资源受 `NOTICE.md` 的非商业限制；GitHub API 当前返回的是 `NOASSERTION`
- 版本：本地仓库 `VERSION` 为 `1.0.14`
- 数据时间：Stars / Forks / Language 来自 2026-06-01 对 GitHub API 的实际查询
