---
tags: [data-engineering, devops, github-trending, web]
date: 2026-06-01
---

## 🔍 项目简介

`ripienaar/free-for-dev` 不是传统意义上的 Web 应用，而是一个“内容仓库 + 静态站点外壳”的项目：它把面向开发者、开源作者、DevOps/Infra 工程师的免费 SaaS/PaaS/IaaS 资源整理在单一 `README.md` 中，再由 `index.html` 里的 Docsify 在浏览器端动态渲染成网站。它解决的问题很直接：把“哪些开发服务有长期免费层”这类分散信息集中起来，方便评估和选型。技术栈非常轻：原生 HTML、Docsify、Docsify 搜索插件、`docsify-darklight-theme`、Google Analytics，自定义域名通过 `CNAME` 发布到 `free-for.dev`。和一般的 `awesome-*` 列表相比，它更聚焦“可直接拿来用的免费在线服务”，且没有自建后端或构建链路。

## ⚡ 核心功能

### 1. Docsify 驱动的零构建静态站点外壳

- 功能名称：浏览器端把仓库内容渲染成单页文档站。
- 实现方式：`index.html` 只保留一个 `#app` 容器和 Docsify 配置，真正渲染逻辑交给外部脚本。

```html
<div id="app">Loading...</div>

<script>
  window.$docsify = {
    name: "Free for Developers",
    repo: "ripienaar/free-for-dev",
    search: ["/"]
  }
</script>

<script src="//cdn.jsdelivr.net/npm/docsify/lib/docsify.min.js"></script>
```

来源：`index.html:51-69`

- 怎么用：

```bash
cd /home/trade/ctf_workspace/gh_trending/ripienaar-free-for-dev
python3 -m http.server 8016
```

然后浏览器访问 `http://127.0.0.1:8016`。
- 输入输出：输入是浏览器对静态文件的请求，以及根目录下的 Markdown 内容；输出是浏览器中的可导航文档页面。
- 适用场景和限制：适合维护只读知识库、目录站、文档站。限制是强依赖 JavaScript 和外部 CDN，且没有服务端渲染能力。


### 2. 单文件 Markdown 数据源与分节目录导航

- 功能名称：用一个 `README.md` 既存内容，又承担信息架构。
- 实现方式：`README.md` 顶部维护总目录，正文按二级标题分段；每个条目统一采用“名称 + 链接 + 免费层说明”的列表格式，Docsify 负责把这些 Markdown 锚点渲染为页面导航。

```md
# Table of Contents

  * [Major Cloud Providers' Always-Free Limits](#major-cloud-providers)
  * [Cloud management solutions](#cloud-management-solutions)
```

来源：`README.md:15-18`

```md
## Source Code Repos

  * [Bitbucket](https://bitbucket.org/) - Unlimited public and private Git repos for up to 5 users with Pipelines for CI/CD
  * [Codeberg](https://codeberg.org/) - Unlimited public and private Git repos for free and open-source projects
```

来源：`README.md:205-208`

- 怎么用：新增条目时直接按同样格式编辑 `README.md`。

```md
  * [Example Service](https://example.com) - Free tier: 1 project, 5GB storage, public pricing page.
```

- 输入输出：输入是结构化 Markdown 文本；输出是分类清晰、可锚点跳转的资源目录。
- 适用场景和限制：适合协作维护“长清单”型内容。限制是没有 schema 校验，格式一致性完全依赖人工审阅。


### 3. 客户端全文搜索

- 功能名称：对整个目录站做前端侧关键字检索。
- 实现方式：`window.$docsify` 打开 `search: ["/"]`，再加载 `search.min.js` 插件，让 Docsify 对根路由文档建立索引。

```html
window.$docsify = {
  name: "Free for Developers",
  repo: "ripienaar/free-for-dev",
  search: ["/"]
}

<script src="//cdn.jsdelivr.net/npm/docsify/lib/plugins/search.min.js"></script>
```

来源：`index.html:53-69`

- 怎么用：

```bash
cd /home/trade/ctf_workspace/gh_trending/ripienaar-free-for-dev
python3 -m http.server 8016
```

打开页面后，在 Docsify 自动生成的搜索框中输入 `terraform`、`auth`、`postgres` 等关键字。
- 输入输出：输入是字符串查询；输出是匹配到的章节标题和条目片段。
- 适用场景和限制：适合在几千行 Markdown 中快速定位供应商。限制是只有关键词匹配，没有结构化过滤、排序权重调优或多文档索引配置。


### 4. 明暗主题切换与最小化视觉配置

- 功能名称：提供站点级别的 light/dark 主题切换。
- 实现方式：`index.html` 引入 `docsify-darklight-theme` 的 CSS/JS，并在配置里声明默认主题、字体和字号。

```html
<link rel="stylesheet" href="//cdn.jsdelivr.net/npm/docsify-darklight-theme@latest/dist/style.min.css">

darklightTheme: {
  siteFont : "Source Sans Pro, Helvetica Neue",
  defaultTheme : "light",
  codeFontFamily : "Roboto Mono, Monaco, courier, monospace",
  bodyFontSize: "15px"
}
```

来源：`index.html:31-32,58-63,69`

- 怎么用：

```bash
cd /home/trade/ctf_workspace/gh_trending/ripienaar-free-for-dev
python3 -m http.server 8016
```

打开页面后使用插件提供的主题切换按钮。
- 输入输出：输入是用户的主题切换操作或默认配置；输出是整页 CSS 主题变化。
- 适用场景和限制：适合无需自己写大量 CSS 就获得基本可读性的文档站。限制是视觉控制权很弱，本仓库只改了默认字体、字号和一个 `blockquote` 背景色。


### 5. 贡献提交流程与内容质量门槛

- 功能名称：通过仓库规范约束新增条目的格式和资格。
- 实现方式：`CONTRIBUTING.md` 说明新增和更新规则，`.github/PULL_REQUEST_TEMPLATE.md` 提供勾选式模板，要求贡献者确认“是 SaaS、不是试用、有公开定价、未重复”等条件。

```md
## New Submission

Open a Pull Request and fill in the PR template. New submissions that
do not follow the PR template guidance and tick all the boxes...
```

来源：`CONTRIBUTING.md:25-31`

```md
 * [ ] This is Software as a Service not self hosted
 * [ ] It has a free tier not just a free trial
 * [ ] Pricing information is clearly visible without signup or phone calls
 * [ ] The submission is not already present in the list
```

来源：`.github/PULL_REQUEST_TEMPLATE.md:35-45`

- 怎么用：提交新服务时，PR 描述里按模板打勾并补齐条目。

```md
## Requirements
 * [x] This is Software as a Service not self hosted
 * [x] It has a free tier not just a free trial
 * [x] Pricing information is clearly visible without signup or phone calls
```

- 输入输出：输入是贡献者的条目描述和勾选信息；输出是可供维护者审阅的标准化 PR。
- 适用场景和限制：适合用最小流程维持长列表质量。限制是它完全靠人工执行，没有 CI 自动校验，也没有防止模板绕过的机器人。


### 6. 面向分享的元信息和无 JavaScript 兜底

- 功能名称：让页面在搜索引擎、社交平台和禁用 JS 的环境里至少“能被发现、能退回源仓库”。
- 实现方式：`index.html` 写了完整的 `description`、Open Graph、Twitter Card 元数据；同时用 `<noscript>` 给出 GitHub 源地址。

```html
<meta property="og:url" content="https://free-for.dev">
<meta property="og:title" content="Free for Developers">
<meta property="og:image" content="https://raw.githubusercontent.com/ripienaar/free-for-dev/master/logo.webp">

<noscript>This page requires JavaScript to work, please enable it or read
  <a href="https://github.com/ripienaar/free-for-dev">here</a>.
</noscript>
```

来源：`index.html:17-28,49`

- 怎么用：

```bash
curl -s http://127.0.0.1:8016 | rg -n "(og:|twitter:|noscript)"
```

- 输入输出：输入是爬虫抓取或用户在禁用 JavaScript 的浏览器中访问页面；输出是社交卡片元信息，或者一个指向 GitHub 仓库的降级入口。
- 适用场景和限制：适合把静态文档站直接对外分享。限制是无 JS 时无法阅读正文，只能跳回 GitHub。

## 🔐 安全审计

- 依赖扫描：
  - 我在仓库根目录实际执行了 `npm audit --json`，结果直接报错 `ENOLOCK`，因为仓库没有 `package.json` 和 `package-lock.json`，说明它本身没有可被 npm 原生审计的一方依赖树。
  - 但 `index.html` 明确运行时依赖外部 CDN 包：`docsify` 与 `docsify-darklight-theme`，分别见 `index.html:31-32,67-69`。而且它们没有被锁版本：`docsify` 直接省略版本号，`docsify-darklight-theme` 甚至显式写成 `@latest`，这意味着今天和明天加载的代码可能不同。
  - 我在临时目录按“页面当前会拉取的包名”执行了：

```bash
npm init -y
npm install docsify@4.13.1 docsify-darklight-theme@3.2.0 --package-lock-only
npm audit --json
```

  - 实测结果：`9` 个漏洞，其中 `3` 个高危、`6` 个中危。
  - 高危项：
    - `marked` 经 `docsify` 引入，存在 ReDoS 问题，`npm audit` 给出 3 条 advisories，其中 2 条高危；对应仓库风险来源是 `index.html:67` 未锁定版本加载 `docsify.min.js`。
    - `braces` 经 `docsify-darklight-theme -> micromatch` 链引入，存在资源消耗问题；对应本地引用是 `index.html:32,69`。
    - `micromatch` 经主题链路引入，存在 ReDoS 风险；对应本地引用同样是 `index.html:32,69`。
  - 结论：这个仓库虽然“代码很少”，但前端运行时供应链风险并不低，核心问题是外部脚本未锁版本、无本地锁文件、无 SRI。

- 密钥泄露扫描：
  - 我实际执行了基于 `rg` 的模式扫描，覆盖 `api key / token / secret / private key` 等常见模式。
  - 唯一命中的真正“像凭证”的内容是 `index.html:38,44` 的 Google Analytics Measurement ID `G-DLYKZXPL9J`。这不是私密 API Key，而是公开埋点标识。
  - 其余大量 `token/auth/password` 命中来自 `README.md` 中收录的第三方服务介绍，例如 `README.md:625-653` 的“Authentication, Authorization, and User Management”分类；这些是内容文本，不是仓库自己的认证实现，也不是泄露。
  - 未发现私钥、云访问密钥、GitHub Token、Slack Token 等硬编码秘密。

- 认证授权逻辑：
  - 仓库内没有后端、没有登录表单、没有 session 管理、没有 cookie 处理，也没有 auth middleware。对源码文件做 `rg` 检查后，除 `README.md` 文本内容外，没有发现本地认证/授权实现。
  - `README.md:625-653` 确实列出了大量 Auth 服务，但这只是目录内容，不是本项目在实现登录。
  - 因为这是纯静态站点，所以“认证绕过”“会话固定”“CSRF Token 缺失”这类传统 Web 风险在仓库内基本不存在；反过来说，它也没有任何访问控制能力。

- 输入校验和数据暴露面：
  - `index.html` 中没有 `<form>`、`<input>`、`fetch()`、`XMLHttpRequest`、`eval()`、`localStorage` 或自定义 `innerHTML` 注入逻辑；本地源代码几乎不处理用户输入。实际的搜索输入处理由外部 Docsify 搜索插件承担。
  - `index.html` 没有 `Content-Security-Policy`，也没有任何 `integrity=` 子资源完整性校验；第三方资源直接来自 `cdn.jsdelivr.net` 和 `www.googletagmanager.com`，见 `index.html:31-32,38,67-69`。这是本项目最现实的数据暴露面和供应链风险点。
  - `CNAME:1` 暴露了正式站点域名 `free-for.dev`，`index.html:15,22,28` 暴露了 logo 的 GitHub Raw 地址；这些都属于公开发布信息，不是敏感数据。
  - 综合判断：服务端攻击面很小，供应链和外链依赖风险明显高于输入校验风险。

## 🚀 快速上手

系统要求：

- 任意现代浏览器，且必须启用 JavaScript。
- 一台能启动静态文件服务器的机器；我本地验证使用的是 Linux + `Python 3.12`。
- 如果要复现依赖审计，还需要 `Node.js 24.15.0` 和 `npm 11.12.1`。
- 访问 `cdn.jsdelivr.net` 和 `www.googletagmanager.com` 的外网能力，否则页面会缺脚本或样式。

直接运行：

```bash
cd /home/trade/ctf_workspace/gh_trending/ripienaar-free-for-dev
python3 -m http.server 8016
```

验证服务是否起来：

```bash
curl -I http://127.0.0.1:8016
```

如果你想复现我做的依赖审计：

```bash
tmpdir="$(mktemp -d)"
cd "$tmpdir"
npm init -y
npm install docsify@4.13.1 docsify-darklight-theme@3.2.0 --package-lock-only
npm audit
```

常见坑：

- 不要直接双击 `index.html` 用 `file://` 打开；Docsify 这类文档站通常需要 HTTP 环境读取 Markdown。
- 关闭 JavaScript 后，正文不会渲染，只会看到 `noscript` 里的 GitHub 回退链接，见 `index.html:49`。
- 这个项目没有本地依赖清单，所以 `npm audit` 在仓库根目录会直接失败；真正的风险来自页面运行时抓取的 CDN 包。
- 页面依赖外部 CDN，离线环境或受限网络下会出现“只有空壳、没有正文/搜索/主题”的情况。

## ⚖️ 一句话判词

值得关注的是它长期维护的“免费开发服务目录”和极简静态发布方式，不值得把它当成复杂工程样板；最适合做技术选型参考站，或者当作“Docsify + 单文件 Markdown 目录站”的最小实现范本。

## 📊 元信息

- 仓库：`https://github.com/ripienaar/free-for-dev`
- Stars：`122,850`（GitHub API，截至 `2026-06-01`；GitHub 页面四舍五入显示约 `123k`）
- Forks：`12,900`（GitHub API，截至 `2026-06-01`；GitHub 页面显示约 `12.9k`）
- Language：`HTML`（GitHub API 主语言判定；实际内容主体另包含超大体量 Markdown）
- License：未声明。GitHub API 返回 `license: null`，仓库根目录也没有 `LICENSE` 文件。
