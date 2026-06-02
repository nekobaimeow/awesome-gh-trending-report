# FIND EVIL! — SANS AI 事件响应黑客松

> **原文：** https://findevil.devpost.com/
> **翻译日期：** 2026-06-02

---

## 📋 基本信息

| 项目 | 详情 |
|------|------|
| **主办方** | SANS Institute |
| **形式** | 在线、公开 |
| **奖金池** | **$22,000** |
| **参赛人数** | 3,858 人 |
| **团队规模** | 最多 5 人（可单人） |
| **赛程** | 2026.4.15 — 2026.6.15 (EDT 11:45pm) |
| **评审期** | 2026.6.19 — 2026.7.3 |
| **公布结果** | 2026.7.8 左右 |
| **标签** | 网络安全、机器学习/AI、新手友好 |

**参赛资格：** 年满居住国法定成年年龄，全球大多数国家/地区可参加（排除巴西、魁北克、俄罗斯、克里米亚、古巴、伊朗、朝鲜等）

---

## 🎯 口号

> **AI threats strike in minutes. Build the defender that responds in seconds.**
> **AI 威胁在几分钟内发动攻击。构建能在几秒内响应的防御者。**

---

## ⚡ 速度问题

AI 驱动的攻击者可以在 **不到 8 分钟** 内从初始访问到完全域控制。

- CrowdStrike 观察到的最快突破时间：**7 分钟**
- Horizon3 的自主 agent：**60 秒完成全权限提升**
- MIT 2024 年研究：AI 驱动的攻击工作流比人类操作员快 **47 倍**

与此同时，一个人类事件响应者还在打开他的工具箱。

**这个差距是网络安全中最危险的问题。Find Evil! 挑战你来弥合它。**

---

## 🎖️ 任务

在 **SANS SIFT Workstation** 上构建自主 AI agent——一个集成了 200+ 事件响应工具的平台，经过 18 年社区开发，年下载量 6 万+。

**Protocol SIFT** 是连接 AI agent 到这些工具的概念验证框架，通过 **Model Context Protocol (MCP)** 实现。

Protocol SIFT 能用，但它幻觉比我们期望的多。**（这正是本次黑客松存在的理由。）** 与攻击方三四个人秘密行动不同，我们把整个从业者社区同时投入到这个问题上。

**你的工作：教 AI agent 像高级分析师一样思考——如何排序方法、识别不对劲的地方、以及出错时自我纠错。**

---

## 👥 谁应该参加

你不需要是事件响应专家。SIFT Workstation 负责领域工具。你需要的是好奇心和构建能力。

- **IR/安全专业人员：** 你已经手动"找 evil"多年了。构建你在凌晨 3 点处理活跃事件时想要的那个 AI 伙伴。
- **AI/ML 工程师：** 将你的技能应用到一个速度决定攻击者是否获胜的领域。真实案例数据，真实工具，没有玩具数据集。
- **学生和早期职业构建者：** 不需要 IR 背景。SIFT Workstation 是你进入科技领域最热门交叉点的入口。
- **开源贡献者：** 每个提交都将作为社区工具继续存在。构建数千名响应者会使用的东西。

---

## 🏗️ 支持的架构方案

四种方法任选，平台没有你的架构如何执行证据完整性和真正自我纠错重要：

### 1. Direct Agent Extension（直接 Agent 扩展）
**Claude Code / OpenClaw** — 扩展 Protocol SIFT 现有的 agent 循环。更好的 prompt 工程、更智能的工具排序、自我纠错例程、准确性验证。这是大多数参与者的入门路径，也是通往可用提交的最快路径。OpenClaw 的可扩展架构也天然适合在工具链中直接构建自定义 MCP 工具包装器。

### 2. Custom MCP Server（自定义 MCP 服务器）
构建专用 MCP 服务器，**暴露结构化函数而非通用 shell 命令**。不是给 AI 一个 `execute_shell_cmd`，而是暴露类型化函数如 `get_amcache()`、`extract_mft_timeline()`、`analyze_prefetch()`。agent 物理上无法运行破坏性命令，因为服务器根本没有这些工具。MCP 服务器原生处理原始工具输出，可在返回 LLM 前解析，防止上下文窗口因大量文本溢出。**（评审中最稳固的架构，也是工作量最大的。）**

### 3. Multi-Agent Frameworks（多 Agent 框架）
**AutoGen / CrewAI / LangGraph** — 将分析分解为专门的、相互通信的 agent。一个 agent 审查内存工件，另一个解析磁盘时间线，第三个综合发现。没有单一模型在其上下文窗口中持有所有原始数据，防止复杂案例上的上下文退化。Agent 间通信以结构化方式记录（时间戳 + token 用量）。**警告：** 没有谨慎终止条件的 agent 循环可能陷入无限对话螺旋。必须内置最大迭代上限和优雅降级。

### 4. Alternative Agentic IDEs（替代 AI IDE）
**Cursor / Cline / Aider** — AI 原生开发环境，有自己的规则系统。优秀的 UI/UX 和内置 diff 查看，但为软件开发设计，非事件响应。这些工具依赖 prompt 遵守来保护证据，而非架构强制执行。如果使用替代 IDE，你的准确率报告必须记录当模型忽略只读规则时会发生什么。

> 如果其他 agentic 框架能做到，我们不会取消资格。但 **Claude Code、OpenClaw 和上述四种方案是主要目标**。为这些构建。

---

## 💡 入门创意（非处方）

两个月足够构建真正的东西，但最难的总是第一个小时。以下是起点，最好的提交会超出这些方向：

### 1. 自我纠错分诊 Agent
构建一个对磁盘镜像运行初始分诊的 agent，评估自身输出的逻辑一致性，识别分析中的空白，并自主以调整后的参数重新运行。**成功指标：** 比 Protocol SIFT 当前基线更少的幻觉发现。

### 2. 多源关联引擎
给定同一系统的磁盘镜像和内存捕获，构建一个交叉引用两个来源发现并标记差异的 agent。如果磁盘时间线说一件事而内存说另一件事，agent 应该能捕捉到。

### 3. MCP 连接的实时分诊
构建一个将 Protocol SIFT 连接到远程端点或 SIEM 的 MCP 服务器，然后创建一个 agent 工作流，拉取实时数据，对照 SIFT 工具库分析，生成实时分诊报告。

### 4. 分析师训练循环
构建一个不仅分析案例数据、还在每一步解释其推理的 agent——选择了哪个工具、为什么、预期发现什么、实际发现了什么。旨在通过使 agent 的决策过程透明来培训初级分析师。

### 5. 准确性基准框架
创建一个测试框架，对已知 ground truth 的数据运行 Protocol SIFT，然后对准确性、误报率和幻觉频率打分。社区需要这个基准来衡量进展。

### 6. 专用 MCP 服务器
将 SIFT 的 200+ 工具封装为结构化、类型安全的函数，通过自定义 MCP 服务器暴露。agent 物理上无法运行破坏性命令，因为服务器不暴露它们。**成功指标：** 零证据破坏风险，同时产生与基线 Protocol SIFT agent 相同或更好的分析输出。**（这是能让从业者放心认可结果的架构。）**

### 7. 持久学习循环
构建一个自我纠错执行循环，在任务上迭代直到满足可验证的成功标准。agent 将失败记录到进度文件，从自身跨迭代的执行轨迹中学习，无需人类干预即可纠偏。必须包含硬性 `--max-iterations` 上限以防止失控执行。**成功指标：** 同一数据上第一次迭代和最后一次迭代之间准确性的可证明改进，保留完整执行轨迹。

> 获奖提交几乎肯定是没有人预料到的东西。

---

## 📦 提交要求

**共 8 项，缺一不可，少任何一项直接淘汰。**

### 1. 代码仓库
GitHub（公开）。开源许可证（MIT 或 Apache 2.0）。

### 2. 演示视频（最多 5 分钟）
终端实时执行的屏幕录制，带音频解说。展示 agent 对真实案例数据工作，包括至少一个自我纠错序列。上传到 YouTube/Vimeo/Youku 并设为公开。

### 3. 架构图
组件如何连接：agent、SIFT 工具、MCP 服务器、数据源、输出管道。必须标明使用的架构模式，记录安全边界在哪里执行。Prompt 级防护和架构级防护必须清晰区分。评委需要一眼理解你的系统和信任边界。

### 4. 书面项目描述
Devpost 项目故事格式：做什么、如何构建、挑战、学到了什么、下一步。具体说明设计决策、权衡，以及你的提交针对哪些自主执行品质。

### 5. 数据集文档
agent 测试的数据是什么、数据来源、发现了什么。可复现性从这里开始。

### 6. 准确率报告
发现准确性的自我评估。误报、遗漏工件、幻觉声明。**必须包含证据完整性方案：** 你的架构如何防止原始数据被修改？如果使用 prompt 级限制而非架构强制执行，记录当模型忽略限制时会发生什么。你测试过证据破坏吗？（如果发现失败模式，记录下来——那是信号，不是弱点。）

### 7. 试用说明
在线部署 URL 或评委在可下载的 SIFT 工作站上本地运行 agent 的分步说明。如果本地设置需要特定工具或依赖，在 README 中明确记录。

### 8. Agent 执行日志
结构化日志，显示完整的 agent 通信和工具执行序列。多 agent 提交：agent 间消息日志带时间戳。单 agent 提交：工具执行日志带时间戳和 token 用量。持久循环提交：迭代跨迭代轨迹，展示 agent 的方法如何变化。**评委必须能将任何发现追溯到产生它的具体工具执行。**

**所有提交材料必须为英文，或提供英文翻译。**

---

## 🏆 奖金

| 奖项 | 奖金 | 额外奖励 |
|------|------|----------|
| 🥇 **SLAYED EVIL** | **$10,000** | SANS Summit 通行证 + 酒店（每人）+ SANS OnDemand 课程（每人）+ SANS 网络直播展示 |
| 🥈 **HUNTED EVIL** | **$7,500** | SANS Summit 通行证 + 酒店（每人）+ SANS OnDemand 课程（每人）+ SANS 网络直播展示 |
| 🥉 **FOUND EVIL** | **$4,500** | SANS OnDemand 课程（每人） |

**总计：$22,000**

---

## ⚖️ 评审标准（等权重，第一阶段为通过/不通过筛选）

| # | 标准 | 说明 |
|---|------|------|
| 1 | **自主执行质量**（平局决胜） | Agent 是否能推理下一步、处理失败、实时自我纠错？ |
| 2 | **IR 准确性** | 发现是否正确？幻觉是否被捕捉和标记？确认发现与推断是否有区分？ |
| 3 | **分析广度和深度** | Agent 能处理多少案例数据？少数类型的深度胜过许多类型的浅层覆盖。 |
| 4 | **约束实现** | 防护是架构级还是 prompt 级？评委评估安全边界在哪里执行以及是否测试过绕过。 |
| 5 | **审计追踪质量** | 评委能否将任何发现追溯到产生它的具体工具执行？ |
| 6 | **可用性和文档** | 另一个从业者能否部署并在此基础上构建？ |

---

## 👨‍⚖️ 评委团（部分）

| 评委 | 职位 |
|------|------|
| **Rob T. Lee** | CAIO, SANS Institute |
| Ahmed AbuGharbia | Founder, cyberdojo.ai |
| Brad Edwards | Domain Consultant SecOps, Palo Alto Networks |
| Yevhen Pervushyn | Founder, Red Asgard (Adversarial AI) |
| Adam Nasreldin | Senior IR Consultant, **Google Mandiant** |
| Georgios Kapoglis | Staff Detection & Response Engineer, **Roblox** |
| Sneha Parmar | Director EDR, **Deutsche Bank** |
| Saurabh Naik | Head of Red Team, **Lockheed Martin** |
| Brett Cumming | CISO, **Skechers** |
| Steve Cobb | CISO, SecurityScorecard |
| Ovie Carroll | Director, **DOJ Cybercrime Lab** |
| John Wilson | CISO & President of Forensics, HaystackID |
| Jason Garman | Principal Security Specialist, **AWS** |
| Amanda Rankhorn | FBI Special Agent (Retired) |

> 共 35+ 位评委，涵盖 Google Mandiant、AWS、Lockheed Martin、Deutsche Bank、Roblox、FBI、渣打银行等顶级机构。

---

## 🔑 知识产权

- 提交必须是参赛者原创作品，参赛者独立拥有
- 代码仓库必须开源（MIT 或 Apache 2.0）
- 可使用开源软件/硬件，但必须在此基础上增强和构建
- 不得使用来自主办方资金或优惠支持开发的项目

---

## 🚀 快速开始

1. 在 Devpost 注册（[findevil.devpost.com](https://findevil.devpost.com)）
2. 加入 **Protocol SIFT Slack** — 问题解答、组队、导师交流
3. 从 [sans.org/tools/sift-workstation](https://sans.org/tools/sift-workstation) 下载 SIFT Workstation
4. 安装 Protocol SIFT：
   ```bash
   curl -fsSL https://raw.githubusercontent.com/teamdfir/protocol-sift/main/install.sh | bash
   ```
5. 查看入门资源：示例案例数据（硬盘镜像、内存镜像）、示例提交
6. 选择问题开始构建

---

## ⏰ 关键时间线

| 节点 | 时间 (EDT) |
|------|-----------|
| 提交截止 | **2026.6.15 11:45 PM** |
| 评审期 | 2026.6.19 — 7.3 |
| 公布结果 | 2026.7.8 左右 |

---

*本文档翻译自 [findevil.devpost.com](https://findevil.devpost.com/)，仅供参考，以原文为准。*
