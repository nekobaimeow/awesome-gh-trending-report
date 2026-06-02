---
tags: [ai-agents, cli-tool, github-trending, llm, typescript]
date: 2026-06-01
---

# a5c-ai/babysitter 源码分析报告

## 🔍 项目简介

`a5c-ai/babysitter` 不是一个单独的“聊天机器人”，而是一套给 AI 编程代理加“监管层”的基础设施：它用 TypeScript/Node.js 写了一个可落盘的 SDK/CLI（`packages/sdk`）、一组面向 Codex/Cursor/Gemini/Copilot/Pi 的 shell hook/插件（`plugins/*`），再加一个基于 Next.js 的本地观察面板（`packages/observer-dashboard`）。它解决的问题不是“怎么调用大模型”，而是“怎么把长流程 agent 工作拆成可回放、可审批、可中断恢复、可审计的确定性任务”。目标用户是已经在用 AI coding harness 的工程团队、自动化工作流作者、以及需要人机审批点的代理系统维护者。技术栈主体是 Node.js 20+、TypeScript、Next.js、MCP、shell hook、Git。和 LangGraph / CrewAI 这类偏“智能体框架”的竞品相比，Babysitter 更强调对外部 agent CLI 的编排、事件日志和断点管控，而不是在进程内拼 prompt graph。

## ⚡ 核心功能

### 1. 运行创建与不可变事件日志

**实现方式**

Babysitter 在创建 run 时，不是直接内存起状态，而是先把 `RUN_CREATED` 事件写进 `runDir/journal/`，并在随后触发运行时 hook。关键逻辑在 `packages/sdk/src/runtime/createRun.ts:45-94`：

```ts
const eventPayload: Record<string, unknown> = {
  runId,
  processId: metadata.processId,
  entrypoint: metadata.entrypoint,
};
await appendEvent({
  runDir,
  eventType: "RUN_CREATED",
  event: eventPayload,
});
await callRuntimeHook("on-run-start", { runId, processId: metadata.processId, entry: entryString, inputs: options.inputs }, ...)
```

真正落盘时，`packages/sdk/src/storage/journal.ts:27-49` 会给每条事件生成自增序号、ULID 和 SHA-256 校验和，再调用 `packages/sdk/src/storage/atomic.ts:15-47` 走临时文件 + `rename` 的原子写：

```ts
const contents = JSON.stringify(eventPayload, null, 2) + "\n";
const checksum = crypto.createHash("sha256").update(contents).digest("hex");
const payloadWithChecksum = JSON.stringify({ ...eventPayload, checksum }, null, 2) + "\n";
await writeFileAtomic(targetPath, payloadWithChecksum);
```

**怎么用**

```bash
cd /home/trade/ctf_workspace/gh_trending/a5c-ai-babysitter
npm install
npm run build:sdk

node packages/sdk/dist/cli/main.js run:create \
  --process-id demo \
  --entry /tmp/demo-process.js#process \
  --prompt "echo once" \
  --json
```

`/tmp/demo-process.js` 可以是最小示例：

```js
exports.process = async (inputs) => ({ ok: true, inputs });
```

**输入输出**

输入是 `processId`、process 入口文件、可选 `prompt/inputs/runId`；输出是一个新的 `runId`、`runDir`，以及落盘后的 `run.json`、`inputs.json`、`journal/*.json`。

**适用场景和限制**

适合需要“每一步都有审计记录”的长流程代理。限制是：它只创建运行，不会自动完成任务；后续必须继续 `run:iterate` 或通过 harness/plugin 驱动迭代。


### 2. 单步编排、回放与 effect 提交

**实现方式**

每次调度不是“一口气跑到底”，而是执行一轮 `orchestrateIteration()`，根据结果落 `RUN_COMPLETED`、`RUN_FAILED` 或返回 `waiting`。核心在 `packages/sdk/src/runtime/orchestrateIteration.ts:38-169`：

```ts
const output = await withProcessContext(engine.internalContext, () =>
  processFn(inputs, engine.context, options.context)
);
const outputRef = await writeRunOutput(options.runDir, output);
await appendEvent({ runDir: options.runDir, eventType: "RUN_COMPLETED", event: { outputRef } });
...
const waiting = asWaitingResult(error);
if (waiting) {
  return { status: "waiting", nextActions: annotateWaitingActions(waiting.nextActions), ... };
}
```

回放一致性由 `packages/sdk/src/runtime/replay/effectIndex.ts:107-218` 负责：它会校验 journal 序号/ULID 顺序、拒绝重复 `effectId`/`invocationKey`、并根据 `EFFECT_RESOLVED` 恢复任务状态：

```ts
if (event.seq !== shouldMatch) {
  throw new RunFailedError(`Journal sequence gap detected at ${event.filename} ...`);
}
if (this.byEffectId.has(effectId)) {
  throw new RunFailedError(`Duplicate effectId detected: ${effectId}`);
}
record.status = payload.status === "ok" ? "resolved_ok" : "resolved_error";
```

外部任务结果提交走 `packages/sdk/src/runtime/commitEffectResult.ts:16-85`，会先校验 payload、检查 effect 仍然是 `requested` 状态，再追加 `EFFECT_RESOLVED`：

```ts
if (record.status !== "requested") {
  throw new RunFailedError(`Effect ${options.effectId} is already resolved`);
}
ensureInvocationKeyMatches(options, record);
...
await appendEvent({
  runDir: options.runDir,
  eventType: "EFFECT_RESOLVED",
  event: { effectId: options.effectId, status: options.result.status, resultRef, ... }
});
```

**怎么用**

```bash
node packages/sdk/dist/cli/main.js run:iterate .a5c/runs/<runId> --json
node packages/sdk/dist/cli/main.js task:list .a5c/runs/<runId> --pending --json
node packages/sdk/dist/cli/main.js task:post .a5c/runs/<runId> <effectId> \
  --status ok \
  --value-inline '{"answer":"done"}' \
  --json
```

**输入输出**

`run:iterate` 输入是 `runDir`，输出是 `completed` / `failed` / `waiting`。`task:post` 输入是 `effectId` 和结果 payload，输出是 `resultRef` 等落盘信息。

**适用场景和限制**

适合把 agent 工作拆成“执行一轮 -> 等外部 effect -> 再执行一轮”的可恢复循环。限制是它天然偏串行控制面：真正的任务执行、人工审批或外部系统回调，必须由别的 actor 负责。


### 3. 任务、断点与并行原语

**实现方式**

Babysitter 暴露给 process 作者的上下文 API 在 `packages/sdk/src/runtime/types.ts:104-129`，明确提供了 `ctx.task()`、`ctx.breakpoint()` 和 `ctx.parallel`：

```ts
export interface ProcessContext {
  task<TArgs, TResult>(task: DefinedTask<TArgs, TResult>, args: TArgs, options?: TaskInvokeOptions): Promise<TResult>;
  breakpoint<T = unknown>(payload: T, options?: { label?: string } & BreakpointRoutingOptions): Promise<BreakpointResult>;
  parallel: ParallelHelpers;
}
```

`ctx.task()` 的底层实现 `packages/sdk/src/runtime/intrinsics/task.ts:51-154` 会给调用生成 `invocationKey`，若未见过则序列化任务定义并落一条 `EFFECT_REQUESTED`：

```ts
const invocation = hashInvocationKey({ processId: options.context.processId, stepId, taskId: task.id });
...
const { taskRef: taskDefRef, inputsRef } = await serializeAndWriteTaskDefinition(...);
await appendEvent({ runDir: options.context.runDir, eventType: "EFFECT_REQUESTED", event: eventPayload });
```

`ctx.breakpoint()` 实际上就是特殊 task，定义在 `packages/sdk/src/runtime/intrinsics/breakpoint.ts:18-70`；如果 run 标记为 non-interactive，它会直接自动批准：

```ts
if (ctx.nonInteractive) {
  void appendEvent({ runDir: context.runDir, eventType: "PROCESS_LOG", event: { ... } });
  return Promise.resolve({ approved: true, response: "Auto-approved (non-interactive mode)" });
}
return runTaskIntrinsic({ task: breakpointTask, ... });
```

并行语义在 `packages/sdk/src/runtime/intrinsics/parallel.ts:19-40`：它不是 `Promise.all` 那种一报错就炸，而是把多个 pending effect 聚合成一个 `ParallelPendingError`：

```ts
for (const thunk of thunks) {
  try {
    const value = await thunk();
    results.push(value);
  } catch (error) {
    const actions = collectPendingActions(error);
    if (actions.length) {
      pending.push(...actions);
      continue;
    }
    throw error;
  }
}
if (pending.length) {
  throw new ParallelPendingError(buildParallelBatch(pending));
}
```

测试文件 `packages/sdk/src/testing/__tests__/parallelHarness.test.ts:76-82` 直接展示了写法：

```ts
export async function process(inputs, ctx) {
  const [alpha, beta] = await ctx.parallel.all([
    async () => ctx.task(branchTask, { branch: "alpha", value: inputs.base }),
    async () => ctx.task(branchTask, { branch: "beta", value: inputs.base + 1 }),
  ]);
  return { alpha, beta };
}
```

**怎么用**

```ts
export async function process(inputs, ctx) {
  const result = await ctx.task(myTask, { request: inputs.prompt });
  const gate = await ctx.breakpoint({ summary: result }, { label: "human-review" });
  const branches = await ctx.parallel.map(["a", "b"], (name) =>
    ctx.task(myTask, { request: `branch:${name}` })
  );
  return { gate, branches };
}
```

**输入输出**

`ctx.task()` 吃 `DefinedTask + args`，吐任务结果或 pending effect；`ctx.breakpoint()` 吃任意 payload，吐 `{ approved, response }`；`ctx.parallel.*` 吃 thunk 数组/数据数组，吐结果数组或批量 pending action。

**适用场景和限制**

适合把流程精确拆成“外部 agent 任务”“人工审批”“并发子任务”。限制是 `parallel.all()` 必须传 thunk，不能直接传 Promise；另外 non-interactive 模式会自动通过 breakpoint，不适合强审查场景。


### 4. 两阶段 `harness:create-run`：先写流程，再跑编排

**实现方式**

`harness:create-run` 不是简单包装 `run:create`，而是把工作拆成 Phase 1（让 agent 先生成 babysitter process 文件）和 Phase 2（真正创建 run、绑定会话、迭代执行）。入口在 `packages/sdk/src/cli/commands/harnessCreateRun.ts:93-141`：

```ts
let processPath = providedProcessPath;
if (!processPath) {
  processPath = await runProcessDefinitionPhase({ ... });
}
...
return await runOrchestrationPhase({
  processPath,
  prompt,
  workspace,
  model,
  runsDir,
  ...
});
```

Phase 1 的核心工具定义在 `packages/sdk/src/cli/commands/harnessPhase1.ts:1707-1768`，其中 `babysitter_write_process_definition` 会把 agent 产出的 JS 文件写入输出目录，并校验文件名：

```ts
const customTools: unknown[] = [
  {
    name: "babysitter_write_process_definition",
    ...
    execute: async (_toolCallId, params) => {
      if (!/\\.m?js$/.test(filename)) throw new BabysitterRuntimeError(...);
      if (/[/\\\\]/.test(filename) || filename.includes("..")) throw new BabysitterRuntimeError(...);
      ...
    },
  },
];
```

Phase 2 在 `packages/sdk/src/cli/commands/harnessPhase2.ts:979-1142` 里把 orchestrator 需要的内部工具注册给 harness：`AskUserQuestion`、`babysitter_run_create`、`babysitter_bind_session`、`babysitter_run_iterate`。

```ts
const customTools: unknown[] = [
  { name: "AskUserQuestion", ... },
  { name: "babysitter_run_create", ... },
  { name: "babysitter_bind_session", ... },
  { name: "babysitter_run_iterate", ... },
];
```

**怎么用**

```bash
node packages/sdk/dist/cli/main.js harness:create-run \
  --prompt "为当前仓库生成一个 babysitter 流程并执行" \
  --workspace "$PWD" \
  --harness internal \
  --json
```

**输入输出**

输入是自然语言 prompt、workspace、harness/model；输出先是一个生成好的 process 文件路径，再是 `runId/runDir` 和多轮 orchestration 的进度/结果。

**适用场景和限制**

适合“先让 agent 把流程代码写出来，再由 Babysitter 严格执行”的场景。限制是它依赖所选 harness 的能力，且生成的 process 质量本身仍取决于底层模型。


### 5. 多 harness hook 接入与上下文压缩

**实现方式**

支持哪些宿主，不是写死在 README，而是代码里显式列了能力矩阵。`packages/sdk/src/harness/discovery.ts:50-110` 定义了 Codex、Cursor、Gemini CLI、GitHub Copilot、Pi、OMP 等 harness 及其 capability：

```ts
export const KNOWN_HARNESSES: readonly HarnessSpec[] = [
  { name: "codex", cli: "codex", callerEnvVars: ["CODEX_THREAD_ID", "CODEX_SESSION_ID", "CODEX_PLUGIN_ROOT"], capabilities: [...] },
  { name: "cursor", cli: "cursor", callerEnvVars: ["CURSOR_PROJECT_DIR", "CURSOR_VERSION"], capabilities: [...] },
  { name: "gemini-cli", cli: "gemini", callerEnvVars: ["GEMINI_SESSION_ID", "GEMINI_PROJECT_DIR", "GEMINI_CWD"], capabilities: [...] },
  ...
];
```

通用 hook 分发入口在 `packages/sdk/src/cli/commands/hookRun.ts:47-153,179-268`。它做了两件很“工程化”的事：

1. `user-prompt-submit` 时对超长 prompt 做密度压缩：

```ts
const tokenCount = estimateTokens(prompt);
if (tokenCount > layer.threshold) {
  payload.prompt = densityFilterText(prompt, 1 - layer.keepRatio);
}
```

2. `pre-tool-use` 时把简单命令重写成 `babysitter compress-output ...`：

```ts
const rewritten = `babysitter compress-output ${command}`;
const response = {
  hookSpecificOutput: {
    hookEventName: "PreToolUse",
    permissionDecision: "allow",
    updatedInput,
  },
};
```

Cursor 的 stop hook 适配器 `packages/sdk/src/harness/cursor.ts:559-618` 会在 run 未完成时输出 `followup_message` 驱动自动续跑：

```ts
followupMessage = `Babysitter iteration ${nextIteration} | Continue orchestration: call 'babysitter run:iterate .a5c/runs/${runId} --json'.\\n\\n${prompt}`;
const output = { followup_message: followupMessage };
process.stdout.write(JSON.stringify(output, null, 2) + "\\n");
```

真正落到宿主的桥接脚本在 `plugins/*/hooks`。例如 Cursor 插件 `plugins/babysitter-cursor/hooks/stop-hook.sh:52-63`：

```bash
RESULT=$(babysitter hook:run \
  --hook-type stop \
  --harness cursor \
  --plugin-root "$PLUGIN_ROOT" \
  --state-dir "${BABYSITTER_STATE_DIR}" \
  --json < "$INPUT_FILE")
```

Gemini 插件 `plugins/babysitter-gemini/hooks/after-agent.sh:82-99` 同样把宿主 hook 输入交给 SDK：

```bash
RESULT=$(babysitter hook:run \
  --hook-type stop \
  --harness gemini-cli \
  --plugin-root "$EXTENSION_PATH" \
  --state-dir ".a5c/state" \
  --json < "$INPUT_FILE")
```

**怎么用**

```bash
cat hook-input.json | node packages/sdk/dist/cli/main.js hook:run \
  --hook-type stop \
  --harness cursor \
  --json
```

**输入输出**

输入通常是宿主 hook 通过 stdin 传来的 JSON；输出可能是：

- `{}`：允许退出
- `{"followup_message":"..."}`：要求宿主继续下一轮
- `{"hookSpecificOutput":{...}}`：更新 tool 输入或权限决策

**适用场景和限制**

适合把 Babysitter 嵌进现有 agent CLI，而不是重造一个新 agent。限制是不同 harness 的 hook 协议不统一，shell wrapper 还依赖本地 `babysitter` CLI 或 `npx` 能成功拉起 SDK。


### 6. Process Library：克隆、绑定与自动引导

**实现方式**

Babysitter 内置了“流程库”概念，默认仓库就是自己：`packages/sdk/src/processLibrary/active.ts:8-12` 定义了默认 repo 和子目录：

```ts
const DEFAULT_PROCESS_LIBRARY_REPO = "https://github.com/a5c-ai/babysitter.git";
const DEFAULT_PROCESS_LIBRARY_SUBPATH = "library";
const DEFAULT_PROCESS_LIBRARY_REFERENCE_SUBPATH = "library/reference";
```

克隆/更新逻辑分别在 `packages/sdk/src/processLibrary/active.ts:277-332`：

```ts
const cloneArgs = ["clone", "--depth", "1"];
if (options.ref) {
  cloneArgs.push("--branch", options.ref);
}
cloneArgs.push(options.repo, dir);
await runGit(cloneArgs);
...
await runGit(["pull", "--ff-only"], dir);
```

绑定和自动引导在 `packages/sdk/src/processLibrary/active.ts:334-445`：它会把默认、run 级、session 级绑定写进 `~/.a5c/active/process-library.json`，并在缺失时自动 clone/update 再 bind。

```ts
if (options.runId) {
  state.runBindings[options.runId] = binding;
}
if (cloneExists) {
  await updateProcessLibrary({ dir: defaultSpec.cloneDir, ... });
} else {
  await cloneProcessLibrary({ repo: defaultSpec.repo, dir: defaultSpec.cloneDir, ... });
}
```

**怎么用**

```bash
node packages/sdk/dist/cli/main.js process-library:clone --json
node packages/sdk/dist/cli/main.js process-library:use --dir "$HOME/.a5c/process-library/babysitter-repo/library" --json
node packages/sdk/dist/cli/main.js process-library:active --json
```

**输入输出**

输入是 repo URL、clone 目录、`runId/sessionId/ref`；输出是 clone 位置、revision、binding scope，以及 active state 文件路径。

**适用场景和限制**

适合团队共享流程模板、skills、reference material。限制是强依赖 Git 和约定目录布局；如果你只想本地一次性跑单个 process，这一层会显得偏重。


### 7. Observer Dashboard：实时看板、SSE 推送、断点批准

**实现方式**

Observer Dashboard 不是静态 UI，它会把 run 目录当数据库。配置写在 `packages/observer-dashboard/src/lib/config-loader.ts:44-80` 的 `~/.a5c/observer.json`，默认 source 甚至会回退到“当前目录的父目录”（`121-149`），方便一口气扫同级多个项目。

扫描逻辑在 `packages/observer-dashboard/src/lib/source-discovery.ts:12-72,95-190`：它递归找 `.a5c/runs` 并按 `runId` 去重。

```ts
const runsPath = path.join(dir, ".a5c", "runs");
...
for (const source of config.sources) {
  const runsDirs = await discoverRunsInSource(source);
  ...
}
```

摘要接口 `packages/observer-dashboard/src/app/api/digest/route.ts:8-45` 会返回所有缓存的 run 摘要：

```ts
await ensureInitialized();
await discoverAndCacheAll();
const runs = getAllCachedDigests();
return NextResponse.json({ runs }, {
  headers: { "Cache-Control": "no-cache, no-store" },
});
```

实时更新接口 `packages/observer-dashboard/src/app/api/stream/route.ts:19-124` 用 SSE 推送 `connected`、`update`、`new-run` 事件：

```ts
const stream = new ReadableStream({
  start(controller) {
    controller.enqueue(encoder.encode(`data: ${JSON.stringify({ type: "connected", ... })}\\n\\n`));
    ...
    serverEvents.on("run-changed", runChangedListener);
    serverEvents.on("new-run", newRunListener);
  },
});
```

断点批准不是只改内存，而是直接写任务结果文件并追加 `EFFECT_RESOLVED` 日志，见 `packages/observer-dashboard/src/app/actions/approve-breakpoint.ts:81-139`：

```ts
const resultPayload = {
  status: "ok",
  value: {
    answer: answer.trim(),
    approvedAt: now,
    approvedBy: "observer-dashboard",
  },
  startedAt: now,
  finishedAt: now,
};
await fs.writeFile(resultPath, JSON.stringify(resultPayload, null, 2), "utf-8");
await appendJournalEntry(runDir, effectId, now);
```

**怎么用**

```bash
npm run dev --workspace=@a5c-ai/babysitter-observer-dashboard
# 浏览器打开 http://127.0.0.1:4800
```

或用它自带 CLI：

```bash
npm run build:cli --workspace=@a5c-ai/babysitter-observer-dashboard
node packages/observer-dashboard/dist/cli.js --watch-dir "$PWD" --port 4800 --dev
```

**输入输出**

输入是一个或多个 watch source（本质上是宿主机目录）；输出是 HTTP JSON（digest/config）、SSE 事件流，以及对 `tasks/<effectId>/result.json` 和 `journal/*.json` 的落盘修改。

**适用场景和限制**

适合本机或内网里观察多个 babysitter run、人工批准 breakpoint。限制很明确：这是“本地可信工具”思路，不是对公网暴露的多租户服务；而且批准逻辑自己写 journal，不走 SDK 的锁保护，见安全审计。


### 8. MCP Server：把 Babysitter 暴露给外部 Agent/工具

**实现方式**

MCP 服务器在 `packages/sdk/src/mcp/server.ts:10-19` 里创建，并注册 run/task/session/discovery 工具：

```ts
export function createBabysitterMcpServer(): McpServer {
  const server = new McpServer({ name: "babysitter", version: pkg.version });
  registerRunTools(server);
  registerTaskTools(server);
  registerSessionTools(server);
  registerDiscoveryTools(server);
  return server;
}
```

`packages/sdk/src/mcp/tools/runs.ts:89-225` 提供 `run_create/run_status/run_iterate/run_events`。例如 `run_create` 直接调用 `createRun()`，`run_iterate` 直接调 `orchestrateIteration()`：

```ts
const result = await createRun({
  runsDir,
  process: { processId: args.processId, importPath: absoluteImportPath, exportName },
  prompt: args.prompt,
  inputs,
});
...
const result = await orchestrateIteration({ runDir });
```

`packages/sdk/src/mcp/tools/tasks.ts:87-166` 提供 `task_post`，内部直接走 `commitEffectResult()`：

```ts
const committed = await commitEffectResult({
  runDir,
  effectId: args.effectId,
  result: args.status === "ok"
    ? { status: "ok", value, startedAt: nowIso, finishedAt: nowIso }
    : { status: "error", error: errorPayload, startedAt: nowIso, finishedAt: nowIso },
});
```

`packages/sdk/src/mcp/tools/sessions.ts:16-236` 则补齐 `session_init/session_associate/session_resume/session_state`，让宿主能恢复跨会话编排状态。

**怎么用**

```bash
node packages/sdk/dist/cli/main.js mcp:serve
```

在 MCP 客户端里可调用：

```json
{
  "tool": "run_create",
  "arguments": {
    "processId": "demo",
    "entrypoint": "/tmp/demo-process.js#process",
    "prompt": "hello"
  }
}
```

**输入输出**

输入是 MCP tool invocation；输出是结构化 JSON，例如 `runId/runDir/state/pendingEffects/resultRef/stateFile` 等。

**适用场景和限制**

适合把 Babysitter 作为其他 agent 平台的“任务控制平面”。限制是参数很多地方仍然用 JSON 字符串传值（如 `inputs`、`value`），客户端适配成本不算低。

## 🔐 安全审计

### 1. 依赖扫描

我实际执行了以下命令：

```bash
cd /home/trade/ctf_workspace/gh_trending/a5c-ai-babysitter && npm audit --package-lock-only --json
cd /home/trade/ctf_workspace/gh_trending/a5c-ai-babysitter/video && npm audit --package-lock-only --json
cd /home/trade/ctf_workspace/gh_trending/a5c-ai-babysitter/plugins/babysitter-codex && npm audit --package-lock-only --json
cd /home/trade/ctf_workspace/gh_trending/a5c-ai-babysitter/plugins/babysitter-pi && npm audit --package-lock-only --json
cd /home/trade/ctf_workspace/gh_trending/a5c-ai-babysitter/plugins/babysitter-omp && npm audit --package-lock-only --json
```

结果如下：

- 根工作区：`31` 个漏洞，`1 critical / 13 high / 17 moderate`
- `video/`：`12` 个漏洞，`2 high / 9 moderate / 1 low`
- `plugins/babysitter-codex/`：`0` 个漏洞
- `plugins/babysitter-pi/`：`11` 个漏洞，`1 critical / 4 high / 6 moderate`
- `plugins/babysitter-omp/`：`11` 个漏洞，`1 critical / 5 high / 5 moderate`

高危条目和代码归因：

- **Critical: `protobufjs`**。根因链路可以在 `packages/sdk/package.json:27-34` 和 `package-lock.json:3339-3357,2308-2317` 看到：SDK 直接依赖 `@mariozechner/pi-coding-agent`，其传递依赖 `@mariozechner/pi-ai` 又拉入 `@google/genai`，而后者依赖 `protobufjs`。

```json
// packages/sdk/package.json
"dependencies": {
  "@mariozechner/pi-coding-agent": "*",
  "@modelcontextprotocol/sdk": "^1.12.1"
}

// package-lock.json
"node_modules/@mariozechner/pi-ai": {
  "dependencies": {
    "@google/genai": "^1.40.0"
  }
}
"node_modules/@google/genai": {
  "dependencies": {
    "protobufjs": "^7.5.4"
  }
}
```

- **High: `next` / `eslint-config-next`**。`packages/observer-dashboard/package.json:75,94` 固定了 `next: 14.2.35` 和 `eslint-config-next: ^14.2.0`，审计报告给出了多条 Next.js 高危项（DoS、请求反序列化、rewrite/request smuggling 相关）。这意味着观察面板如果长期对外开放，不应忽略框架层补丁。

```json
"dependencies": {
  "next": "14.2.35"
},
"devDependencies": {
  "eslint-config-next": "^14.2.0"
}
```

- **High: `basic-ftp`**。根工作区的锁文件 `package-lock.json:11170-11179,14713-14726` 显示它来自 `pac-proxy-agent -> get-uri -> basic-ftp`，审计命中 FTP command injection / DoS。

```json
"node_modules/get-uri": {
  "dependencies": {
    "basic-ftp": "^5.0.2"
  }
}
"node_modules/pac-proxy-agent": {
  "dependencies": {
    "get-uri": "^6.0.1"
  }
}
```

- `plugins/babysitter-pi` 和 `plugins/babysitter-omp` 的严重漏洞，主要不是插件自己写了很多逻辑，而是它们都只直接依赖 SDK（`plugins/babysitter-pi/package.json:21-23`、`plugins/babysitter-omp/package.json:21-23`），所以把 SDK 的传递依赖风险整包带过去了。

结论：供应链风险在这个仓库里不是“边角料问题”，而是已经进入核心 SDK 路径；至少要优先处理 `protobufjs`、Next.js、`basic-ftp`、`fast-uri`、`fast-xml-parser` 这几条。

### 2. 密钥泄露扫描

我实际执行了两类扫描：

```bash
cd /home/trade/ctf_workspace/gh_trending/a5c-ai-babysitter
rg -n --hidden --glob '!**/node_modules/**' --glob '!**/package-lock.json' --glob '!**/pnpm-lock.yaml' \
  '(ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9]{20,}|AIza[0-9A-Za-z\\-_]{35}|AKIA[0-9A-Z]{16}|xox[baprs]-[A-Za-z0-9-]{10,})'
```

以及对 `TOKEN/SECRET/PASSWORD/API_KEY` 关键字的广义扫描。

结果：

- **未发现可用的真实明文凭据**。
- 命中的强模式基本都是文档里的占位示例，例如 `library/specializations/desktop-development/skills/electron-auto-updater-setup/README.md:334-340`：

```bash
GH_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

- 另外一些命中是显式要求用户通过环境变量传值，而不是仓库硬编码，比如 `DOCKER.md:41-88`、`docker-compose.yml:11-35`、`docs/release-pipeline.md:8-18`。

从代码角度看，项目对 secret 泄露做了几层防护：

- `packages/sdk/src/config/defaults.ts:165-170` 默认 `allowSecretLogs: false`
- `packages/sdk/src/tasks/kinds/index.ts:363-395` 会基于 key 名红线词自动剔除环境变量
- `packages/sdk/src/cli/main.ts:930-939,1910-1936` 只有在 `--json --verbose` 且显式设置 `BABYSITTER_ALLOW_SECRET_LOGS=true` 时才会输出 task/result payload

```ts
function allowSecretLogs(parsed: ParsedArgs): boolean {
  if (!parsed.json || !parsed.verbose) return false;
  const raw = process.env.BABYSITTER_ALLOW_SECRET_LOGS;
  ...
}
...
task: secretLogsAllowed ? taskDef : null,
result: secretLogsAllowed ? inlineResult : null,
```

这部分的结论是：仓库里没有直接泄露真实 key，但它包含大量“如何传 key”的模板；在 fork/复制这些模板时，仍要注意二次提交风险。

### 3. 认证、授权与 CSRF 逻辑

这里最重要的发现不是“认证写得不好”，而是**观察面板几乎没有应用层认证**。

- `packages/observer-dashboard/src/app/api/config/route.ts:8-137` 直接暴露配置读写接口，没有任何身份检查。
- `packages/observer-dashboard/src/app/api/digest/route.ts:8-45` 直接返回所有 run 摘要。
- `packages/observer-dashboard/src/app/api/stream/route.ts:11-124` 直接开放 SSE 流。
- `packages/observer-dashboard/src/app/actions/approve-breakpoint.ts:81-145` 允许提交 breakpoint 批准结果，但没有用户身份、角色、权限判断。

我还检查了 `packages/observer-dashboard/src` 下是否存在 `middleware.ts`、auth 模块或常见库（`next-auth`、`csrf`、`cookie-session` 等）；源码里没有看到对应实现。换句话说，这个 dashboard 的安全边界是“本机/可信内网”，不是“互联网服务”。

需要特别区分的一点是：SDK 里有大量 `session` 代码，但那是**编排状态会话**，不是登录态。比如 `packages/sdk/src/session/write.ts:40-73` 只是把 run 关联状态用 YAML frontmatter 原子写入文件：

```ts
await fs.writeFile(tempPath, content, 'utf8');
await fs.rename(tempPath, filePath);
```

这能减少状态损坏，但不能替代用户认证/授权。

审计结论：

- 如果 `observer-dashboard` 只监听 `127.0.0.1`，问题可接受。
- 如果把它直接暴露到公网或共享内网，`config`、`digest`、`stream`、`approve-breakpoint` 都应被反向代理鉴权或接入应用层 auth。
- 源码里没有看到额外的 CSRF token / Origin 校验逻辑；是否完全依赖 Next.js 默认行为，要看最终部署方式，但项目自身没有再加一层。

### 4. 输入校验、数据暴露面与完整性风险

正向设计：

- `packages/observer-dashboard/src/app/actions/approve-breakpoint.ts:87-100` 对 `runId/effectId` 做了空值检查和正则限制，能防住最直接的路径穿越。

```ts
const idPattern = /^[a-zA-Z0-9_\\-]+$/;
if (!idPattern.test(runId) || !idPattern.test(effectId)) {
  return { success: false, error: "Invalid characters in runId or effectId" };
}
```

- `packages/observer-dashboard/src/app/api/config/route.ts:25-111` 对 `sources/depth/pollInterval/theme/retentionDays/hiddenProjects` 做了明确类型和范围校验。
- `packages/sdk/src/mcp/tools/runs.ts:91-101`、`tasks.ts:89-107`、`sessions.ts:18-36` 都通过 `zod` / schema 先约束 MCP 输入。

但仍有几个实质性风险：

- **任意目录观测面**：`packages/observer-dashboard/src/app/api/config/route.ts:33-47,99-115` 只要求 `sources[i].path` 是非空字符串；`packages/observer-dashboard/src/lib/config-loader.ts:44-80` 会把它写入 `~/.a5c/observer.json`；`packages/observer-dashboard/src/lib/source-discovery.ts:16-71,95-190` 随后会递归扫描这些路径。如果攻击者能访问这个配置接口，就能把 dashboard 指向宿主机上别的目录树。

- **默认暴露范围偏大**：`packages/observer-dashboard/src/lib/config-loader.ts:142-149` 在没有显式配置时，默认观测 `process.cwd()` 的父目录。这对本地体验很好，但也意味着“一不小心就把同级仓库都扫进来了”。

- **未鉴权的数据接口**：`packages/observer-dashboard/src/app/api/digest/route.ts` 和 `packages/observer-dashboard/src/app/api/stream/route.ts` 会暴露 runId、时间戳、项目名、runDir 等运行元数据；如果 source 指到共享目录，这些信息本身就可能敏感。

- **完整性并发风险**：`packages/observer-dashboard/src/app/actions/approve-breakpoint.ts:19-69,119-139` 自己扫描 journal 目录算下一个序号并直接 `fs.writeFile()`，但它没有复用 SDK 的 `withRunLock + commitEffectResult()` 路径（对比 `packages/sdk/src/runtime/commitEffectResult.ts:16-85`）。这意味着在“人工批准”和“CLI/别的 actor 同时提交 effect”时，存在 journal 序号竞争、重复 resolve 或状态不一致的可能。这个更偏一致性/完整性问题，但在审计里值得单列。

总体判断：

- **高风险**：未鉴权 observer API 如果暴露到不可信网络。
- **中风险**：配置接口可扩大文件系统扫描面。
- **中风险**：dashboard 旁路写 journal，存在并发一致性隐患。
- **低风险/正向**：CLI 对 secret log 默认关闭，task env 有 redaction。

## 🚀 快速上手

系统与依赖要求：

- Node.js `>=20`，`packages/observer-dashboard/package.json:31-33` 明确要求
- `npm`
- `git`（`process-library:*` 命令需要）
- 如果要接入特定宿主，还需要对应 CLI，如 `codex` / `cursor` / `gemini`

最小可执行步骤：

```bash
cd /home/trade/ctf_workspace/gh_trending/a5c-ai-babysitter

# 安装工作区依赖
npm install

# 构建 SDK CLI
npm run build:sdk

# 查看 CLI 功能
node packages/sdk/dist/cli/main.js --help
node packages/sdk/dist/cli/main.js harness:discover --json

# 启动观察面板
npm run dev --workspace=@a5c-ai/babysitter-observer-dashboard
# 打开 http://127.0.0.1:4800
```

如果只想验证 observer CLI：

```bash
npm run build:cli --workspace=@a5c-ai/babysitter-observer-dashboard
node packages/observer-dashboard/dist/cli.js --watch-dir "$PWD" --port 4800 --dev
```

如果要手工创建一个最小 run：

```bash
cat >/tmp/demo-process.js <<'EOF'
exports.process = async (inputs) => ({ ok: true, inputs });
EOF

node packages/sdk/dist/cli/main.js run:create \
  --process-id demo \
  --entry /tmp/demo-process.js#process \
  --prompt "hello" \
  --json
```

常见坑：

- 根工作区只声明了 `packages/*`（`package.json:5-7`），`plugins/*` 不在 workspace 里；要单独测试某个插件，通常要进入对应目录再 `npm install`。
- `observer-dashboard` 默认会扫当前目录的父目录（`packages/observer-dashboard/src/lib/config-loader.ts:142-149`）；不想扫太多项目时，显式传 `--watch-dir` 或配置 `sources`。
- `process-library:*` 命令需要本机有 `git`，并且 `~/.a5c` 可写。
- `packages/sdk/package.json:5` 标成了 `UNLICENSED`，但仓库根有 `LICENSE.md`（MIT）；如果你要做企业依赖合规，最好先确认发布包元数据。

## ⚖️ 一句话判词

值得关注，但前提是你的问题真的是“多 harness、可审计、可断点恢复的 agent 编排”；如果你只需要一个轻量级单轮 AI 工具，这个项目会明显过重。

## 📊 元信息

- Stars：`1135`（截至 `2026-06-01`，GitHub API：`https://api.github.com/repos/a5c-ai/babysitter`）
- Forks：`71`（截至 `2026-06-01`，GitHub API）
- Language：`JavaScript`（GitHub API 主语言；但核心源码实际以 `packages/sdk/src/**/*.ts`、`packages/observer-dashboard/src/**/*.ts` 的 TypeScript 为主）
- License：仓库根 `LICENSE.md` 为 `MIT`，但 `packages/sdk/package.json:5` 标记为 `UNLICENSED`，存在包级元数据不一致
