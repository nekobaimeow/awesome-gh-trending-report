---
tags: [github-trending, python, web]
date: 2026-06-01
---
<!-- 
  📖 English summary available at: [English version](../../en/trending/2026-06-01-13-TheAlgorithms-Python.md)
-->


## 🔍 项目简介

`TheAlgorithms/Python` 是一个社区共建的 Python 算法与数据结构实现仓库，我本地实际看到的快照包含约 1385 个 `.py` 文件、50 个顶层目录，覆盖排序、图算法、压缩、字符串、机器学习、密码学、网络脚本等大量主题。它解决的不是“上线一个应用”，而是“给学习者、刷题者、面试准备者、贡献者提供可读、可运行、可改写的参考实现”；目标用户主要是想看算法源码的人，而不是追求生产性能的人。技术栈以 Python 为核心，`pyproject.toml` 明确声明 `requires-python = ">=3.14"`，并拉入 `numpy`、`pandas`、`scikit-learn`、`matplotlib`、`httpx`、`sympy`、`xgboost` 等依赖。和标准库或成熟算法库相比，它的差异不在性能，而在覆盖面大、实现拆得细、每个文件都尽量能单独运行；但这也意味着代码质量和可维护性不完全一致，局部模块甚至有当前快照下无法直接运行的情况。

## ⚡ 核心功能

### 1. 归并排序

- 功能名称：对可比较序列做分治排序。
- 实现方式：核心在 `sorts/merge_sort.py`，先递归拆分，再在内部 `merge()` 里逐个比较并拼回结果。

```python
# sorts/merge_sort.py
def merge_sort(collection: list) -> list:
    def merge(left: list, right: list) -> list:
        result = []
        while left and right:
            result.append(left.pop(0) if left[0] <= right[0] else right.pop(0))
        result.extend(left)
        result.extend(right)
        return result

    if len(collection) <= 1:
        return collection
    mid_index = len(collection) // 2
    return merge(merge_sort(collection[:mid_index]), merge_sort(collection[mid_index:]))
```

- 怎么用：

```bash
cd /home/trade/ctf_workspace/gh_trending/TheAlgorithms-Python
python - <<'PY'
from sorts.merge_sort import merge_sort
print(merge_sort([9, 1, 5, 3]))
PY
```

- 输入输出：输入是 `list` 类型、元素之间可比较；输出是新的升序列表，例如 `[9, 1, 5, 3] -> [1, 3, 5, 9]`。
- 适用场景和限制：适合教学、解释分治法、写 doctest。限制也很明显：源码虽然注释写的是 `O(n log n)`，但 `merge()` 用了 `left.pop(0)` / `right.pop(0)`，在 Python `list` 上这是线性移动，真实常数和性能都不适合生产；命令行入口还只按整数解析，`sorts/merge_sort.py` 末尾只是一个非常薄的交互壳。

### 2. 加权图最短路（Dijkstra）

- 功能名称：计算加权图上两点之间的最短路径代价。
- 实现方式：`graphs/dijkstra.py` 用 `heapq` 维护最小堆，用 `visited` 去重，弹出当前最小代价节点后把邻居重新压回堆。

```python
# graphs/dijkstra.py
heap = [(0, start)]
visited = set()
while heap:
    (cost, u) = heapq.heappop(heap)
    if u in visited:
        continue
    visited.add(u)
    if u == end:
        return cost
    for v, c in graph[u]:
        if v in visited:
            continue
        heapq.heappush(heap, (cost + c, v))
```

- 怎么用：

```bash
cd /home/trade/ctf_workspace/gh_trending/TheAlgorithms-Python
python graphs/dijkstra.py
```

- 输入输出：输入是邻接表形式的图，如 `{"A": [["B", 2], ["C", 5]], ...}`，再给起点和终点；输出是整数代价，找不到时返回 `-1`。仓库自带样例里 `dijkstra(G, "E", "C")` 输出 `6`。
- 适用场景和限制：适合解释“最短路 + 最小堆”的基本套路，也适合把别的题目图建模后直接塞进去。限制是它只返回总代价，不返回路径本身；默认假设边权非负；而且当前文件在模块顶层就执行了 3 组样例并 `print()`，所以把它当库导入时会有副作用输出，不够“库友好”。

### 3. 基于 Trie 的自动补全

- 功能名称：按前缀返回候选单词。
- 实现方式：`strings/autocomplete_using_trie.py` 先把字符逐层插入嵌套字典，再通过 `_elements()` 深度遍历前缀子树，把所有后缀拼回来。

```python
# strings/autocomplete_using_trie.py
class Trie:
    def insert_word(self, text: str) -> None:
        trie = self._trie
        for char in text:
            if char not in trie:
                trie[char] = {}
            trie = trie[char]
        trie[END] = True

    def find_word(self, prefix: str) -> tuple | list:
        trie = self._trie
        for char in prefix:
            if char in trie:
                trie = trie[char]
            else:
                return []
        return self._elements(trie)
```

```python
# strings/autocomplete_using_trie.py
def autocomplete_using_trie(string: str) -> tuple:
    suffixes = trie.find_word(string)
    return tuple(string + word for word in suffixes)
```

- 怎么用：

```bash
cd /home/trade/ctf_workspace/gh_trending/TheAlgorithms-Python
python - <<'PY'
from strings.autocomplete_using_trie import autocomplete_using_trie
print(autocomplete_using_trie("de"))
PY
```

- 输入输出：输入是前缀字符串，例如 `"de"`；输出是补全结果元组，当前内置词表下会得到 `('depart ', 'detergent ', 'deer ', 'deal ')`。
- 适用场景和限制：适合讲前缀树这种“空间换时间”的结构，或者做很轻量的命令补全演示。限制非常源码级：这个文件默认只预装了 `("depart", "detergent", "daring", "dog", "deer", "deal")` 六个词，而且 `END = "#"` 的终止标记最后被实现成一个空格，所以返回结果自带尾随空格，这不是一个生产级 autocomplete API。

### 4. LZ77 压缩与解压

- 功能名称：把字符串压成 `(offset, length, indicator)` token 序列，再还原回原文。
- 实现方式：`data_compression/lz77.py` 里定义了 `Token` 和 `LZ77Compressor`；`compress()` 维护滑动窗口，调用 `_find_encoding_token()` 找最长匹配，`decompress()` 再按 token 逐步回放。

```python
# data_compression/lz77.py
class LZ77Compressor:
    def compress(self, text: str) -> list[Token]:
        output = []
        search_buffer = ""
        while text:
            token = self._find_encoding_token(text, search_buffer)
            search_buffer += text[: token.length + 1]
            if len(search_buffer) > self.search_buffer_size:
                search_buffer = search_buffer[-self.search_buffer_size :]
            text = text[token.length + 1 :]
            output.append(token)
        return output

    def decompress(self, tokens: list[Token]) -> str:
        output = ""
        for token in tokens:
            for _ in range(token.length):
                output += output[-token.offset]
            output += token.indicator
        return output
```

- 怎么用：

```bash
cd /home/trade/ctf_workspace/gh_trending/TheAlgorithms-Python
python - <<'PY'
from data_compression.lz77 import LZ77Compressor
lz = LZ77Compressor()
compressed = lz.compress("ababcbababaa")
print(compressed)
print(lz.decompress(compressed))
PY
```

- 输入输出：输入是普通字符串；压缩输出是 `Token` 列表，比如 `[(0, 0, a), (0, 0, b), (2, 2, c), ...]`，解压输出又回到原字符串。
- 适用场景和限制：适合教学、理解无损压缩、做小型字符串实验。限制是它只处理字符串而不是通用字节流/文件容器，没有比特级编码；`_match_length_from_index()` 用递归找最长匹配，大输入下栈深和性能都不是生产方案。

### 5. K-Means 聚类

- 功能名称：对二维或多维数值数据做 K-Means 聚类，并可记录异质性曲线、画 3D 图。
- 实现方式：`machine_learning/k_means_clust.py` 先随机抽样初始质心，用 `pairwise_distances()` 算样本到质心距离，再 `argmin` 分配类别，最后对每个簇做均值回算新质心。

```python
# machine_learning/k_means_clust.py
def assign_clusters(data, centroids):
    distances_from_centroids = centroid_pairwise_dist(data, centroids)
    cluster_assignment = np.argmin(distances_from_centroids, axis=1)
    return cluster_assignment

def revise_centroids(data, k, cluster_assignment):
    new_centroids = []
    for i in range(k):
        member_data_points = data[cluster_assignment == i]
        centroid = member_data_points.mean(axis=0)
        new_centroids.append(centroid)
    return np.array(new_centroids)
```

```python
# machine_learning/k_means_clust.py
for itr in range(maxiter):
    cluster_assignment = assign_clusters(data, centroids)
    centroids = revise_centroids(data, k, cluster_assignment)
    if prev_cluster_assignment is not None and (prev_cluster_assignment == cluster_assignment).all():
        break
    if record_heterogeneity is not None:
        score = compute_heterogeneity(data, k, centroids, cluster_assignment)
        record_heterogeneity.append(score)
```

- 怎么用：

```bash
cd /home/trade/ctf_workspace/gh_trending/TheAlgorithms-Python
uv sync --all-groups
uv run python - <<'PY'
import numpy as np
from machine_learning.k_means_clust import get_initial_centroids, kmeans

X = np.array([[0., 0.], [0., 1.], [9., 9.], [9., 8.]])
init = get_initial_centroids(X, 2, seed=0)
centroids, labels = kmeans(X, 2, init, maxiter=20)
print(centroids)
print(labels)
PY
```

- 输入输出：输入是 `numpy` 二维数组 `data`、簇数 `k`、初始质心 `initial_centroids`；输出是 `centroids` 和 `cluster_assignment` 两个数组，可选再得到 `heterogeneity` 历史曲线。
- 适用场景和限制：适合教学、讲 Lloyd 迭代流程、快速看小样本聚类效果。限制很源码化：依赖 `numpy` / `scikit-learn` / `matplotlib`，基础 Python 环境直接导入会缺包；`revise_centroids()` 对空簇没有显式处理，`member_data_points.mean(axis=0)` 可能产出 `NaN`；`plot_kmeans()` 固定画 3D 点云，不是通用可视化层。

### 6. 基于 TCP Socket 的文件传输

- 功能名称：在本机名和固定端口上做一个极简文件发送/接收。
- 实现方式：`file_transfer/send_file.py` 在 `12312` 端口监听，把文件按 1024 字节块发送；`file_transfer/receive_file.py` 连接后循环 `recv()` 并写入本地文件。

```python
# file_transfer/send_file.py
port = 12312
sock = socket.socket()
host = socket.gethostname()
sock.bind((host, port))
sock.listen(5)

conn, addr = sock.accept()
with open(filename, "rb") as in_file:
    data = in_file.read(1024)
    while data:
        conn.send(data)
        data = in_file.read(1024)
```

```python
# file_transfer/receive_file.py
sock.connect((host, port))
sock.send(b"Hello server!")
with open("Received_file", "wb") as out_file:
    while True:
        data = sock.recv(1024)
        if not data:
            break
        out_file.write(data)
```

- 怎么用：

```bash
cd /home/trade/ctf_workspace/gh_trending/TheAlgorithms-Python

# 终端 A
python file_transfer/send_file.py

# 终端 B
python file_transfer/receive_file.py
```

- 输入输出：发送端输入是待发送文件名，默认 `mytext.txt`；接收端输出是当前目录下的 `Received_file`。
- 适用场景和限制：适合讲 socket 基本收发流程、调试本地网络通信。限制非常大：固定端口、固定输出文件名、无断点续传、无校验和、默认靠 `socket.gethostname()` 同机通信，而且完全没有认证、授权或加密。

## 🔐 安全审计

### 1. 依赖漏洞扫描

我先按 `uv.lock` 实际导出依赖，再跑了 `pip-audit`：

```bash
cd /home/trade/ctf_workspace/gh_trending/TheAlgorithms-Python
uv export --format requirements.txt --all-groups --no-hashes --output-file /tmp/thealgorithms-python-reqs.txt
pip-audit -r /tmp/thealgorithms-python-reqs.txt
```

结果：共发现 **19 个已知漏洞**，分布在 **6 个包** 上。

- `fonttools 4.58.0`：1 个
- `idna 3.10`：1 个
- `keras 3.9.2`：8 个
- `pygments 2.19.1`：1 个
- `requests 2.32.3`：2 个
- `urllib3 2.4.0`：6 个

高危/严重条目里，最值得盯的是这几项：

- `fonttools 4.58.0 -> CVE-2025-66034`：NVD 评分 **9.8 CRITICAL**。NVD 描述是处理恶意 `.designspace` 文件时存在任意文件写入，最终可走到 RCE。这个包是依赖树里真实存在的，来自科学计算/绘图库依赖链，而不是 README 里随口提到。
- `urllib3 2.4.0 -> CVE-2026-21441`：NVD 评分 **7.5 HIGH**，CNA 给到 **8.9 HIGH**。问题是流式读取重定向响应时可能先把压缩炸弹整包解开，导致高 CPU/高内存消耗。
- `keras 3.9.2 -> CVE-2026-1669`：NVD 评分 **7.5 HIGH**。恶意 `.keras` 模型可触发任意本地文件读取；同一个 `keras 3.9.2` 还同时命中了多条 safe mode 绕过、任意代码执行、SSRF 和文件覆盖类漏洞（例如 `PYSEC-2025-76`、`PYSEC-2025-123`、`CVE-2025-12058`、`CVE-2026-1462`）。

结合源码看，这些漏洞更像“开发/学习环境风险”而不是“仓库本身是线上服务”；但由于项目确实在 `pyproject.toml` 里声明了 `keras`、`matplotlib`、`httpx` 等重依赖，任何按当前锁文件同步环境的人都会把这些版本装下来，所以不能忽略。

### 2. 密钥泄露扫描

我对仓库做了关键字和常见 token 形态扫描：

```bash
rg -n -i "(api[_-]?key|secret|token|password|passwd|client_secret|authorization|bearer |private[_-]?key|access[_-]?key)" .
rg -n "BEGIN (RSA|OPENSSH|EC|DSA|PGP|PRIVATE)" .
rg -n -i "(AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{20,}|xox[baprs]-[A-Za-z0-9-]{10,}|AIza[0-9A-Za-z\\-_]{35})" .
```

结论：**没有扫到真实高熵密钥、私钥块或常见云平台 token**，但扫到了几处示例位和一个硬编码演示值。

- `web_programming/recaptcha_verification.py`：`secret_key = "secretKey"`，这是硬编码示例值，不是真实密钥，但如果有人照抄进生产代码会有明显问题。
- `web_programming/current_weather.py`：`OPENWEATHERMAP_API_KEY = ""`、`WEATHERSTACK_API_KEY = ""`，是空占位。
- `web_programming/giphy.py`：`giphy_api_key = "YOUR API KEY"`，也是占位。
- `web_programming/fetch_github_info.py`：没有硬编码 token，而是 `USER_TOKEN = os.environ.get("USER_TOKEN", "")` 后再进 `Authorization` 头，这是相对正确的做法。

换句话说，这个仓库**没有“现成泄露”**，但 `web_programming/` 目录里不少文件是“把你该填的密钥位置留出来”，使用者需要自己把安全边界补齐。

### 3. 认证与授权逻辑

我又搜了认证/会话相关关键字：

```bash
rg -n -i "\\b(auth|authenticate|authorization|session|csrf|login|jwt|oauth)\\b" .
```

结论很明确：**这个仓库不是一个有统一认证体系的应用**，而是一堆独立脚本和算法文件，所以没有看到全局 auth middleware、session store、RBAC、JWT 校验链这类东西。真正有认证语义的代码主要只有三处：

- `web_programming/recaptcha_verification.py`：文档字符串里的 HTML 表单包含 `{% csrf_token %}`，函数体里实际调用 Django 的 `authenticate()` / `login()`，逻辑是“先过 Google Recaptcha，再尝试登录”。这是全仓库最接近真实登录流程的文件。
- `web_programming/fetch_github_info.py`：走的是 GitHub personal access token，token 放环境变量，调用时进 `Authorization` 头。
- `file_transfer/send_file.py` + `file_transfer/receive_file.py`：这两份 socket 脚本完全没有 authn/authz 概念，谁连上端口谁就能收文件。

如果按“安全产品”标准看，这里的认证授权是明显不完整的；但从项目定位看，这更像“安全示例零件”和“教学脚本”，不是一个打算部署的统一系统。

### 4. 输入校验和数据暴露面

源码里能看到一些局部校验，但整体风格是“教育演示优先”，不是“输入默认不可信”。

- `sorts/merge_sort.py` 的命令行入口会对整数解析做 `try/except ValueError`，这是最基础的 CLI 容错。
- `web_programming/current_weather.py` 在没有任何 API key 时会直接抛 `ValueError`，避免空请求继续往下跑。
- `machine_learning/k_means_clust.py` 没有处理空簇；`member_data_points.mean(axis=0)` 在某个簇为空时可能直接出 `NaN`，这是算法层面的输入鲁棒性问题。

更值得写进审计报告的是暴露面：

- `web_programming/current_weather.py` 把 `WEATHERSTACK_URL_BASE` 写成了 `http://api.weatherstack.com/current`，而不是 HTTPS；后续 `access_key` 通过查询参数发送，这意味着如果有人真把密钥填进去，传输链路和日志层面都存在额外暴露面。
- `file_transfer/send_file.py` 对所有成功连接的客户端直接发送指定文件，没有白名单、没有身份校验、没有传输加密，也没有校验发送对象是否可信。
- `file_transfer/receive_file.py` 把收到的所有字节直接落到固定文件 `Received_file`，没有大小限制、类型校验、哈希校验、路径隔离。
- `web_programming/giphy.py` 直接把 API key 拼进 URL 查询串，虽然走的是 HTTPS，但日志、代理和历史记录仍然更容易看到整条 URL。

总结这部分：这个仓库的危险面不在“被动暴露数据库”，而在“很多脚本默认相信调用者和网络环境”，这和它的教学定位一致，但不适合直接搬去上线。

## 🚀 快速上手

系统要求和依赖建议：

- Python：项目声明 `>=3.14`，不要默认拿系统自带的 Python 3.10/3.11/3.12 硬跑。
- 工具：推荐 `uv`，因为仓库已经自带 `pyproject.toml` 和 `uv.lock`。
- 依赖：纯算法脚本很多可以裸跑，但 `machine_learning/`、`web_programming/`、`digital_image_processing/` 这些目录依赖外部包和网络。

推荐的安装与运行命令：

```bash
cd /home/trade/ctf_workspace/gh_trending/TheAlgorithms-Python
uv sync --all-groups
```

先跑几个不依赖重型外部服务的模块：

```bash
cd /home/trade/ctf_workspace/gh_trending/TheAlgorithms-Python
uv run python -m doctest -v sorts/merge_sort.py
uv run python graphs/dijkstra.py
uv run python strings/autocomplete_using_trie.py
uv run python data_compression/lz77.py
```

跑一个需要科学计算栈的 K-Means 示例：

```bash
cd /home/trade/ctf_workspace/gh_trending/TheAlgorithms-Python
uv run python - <<'PY'
import numpy as np
from machine_learning.k_means_clust import get_initial_centroids, kmeans

X = np.array([[0., 0.], [0., 1.], [9., 9.], [9., 8.]])
init = get_initial_centroids(X, 2, seed=0)
centroids, labels = kmeans(X, 2, init, maxiter=20)
print(centroids)
print(labels)
PY
```

跑文件传输示例时需要两个终端：

```bash
cd /home/trade/ctf_workspace/gh_trending/TheAlgorithms-Python

# 终端 A
uv run python file_transfer/send_file.py

# 终端 B
uv run python file_transfer/receive_file.py
```

如果想做全量回归：

```bash
cd /home/trade/ctf_workspace/gh_trending/TheAlgorithms-Python
uv run pytest
```

常见坑：

- 当前环境里系统 `python` 是 3.12，但仓库声明是 3.14；直接混用很容易遇到行为差异。
- `machine_learning/k_means_clust.py` 不装 `scikit-learn` / `numpy` 跑不起来，我实际导入时就复现了 `ModuleNotFoundError: No module named 'sklearn'`。
- `graphs/dijkstra.py` 顶层有示例 `print()`，导入时会直接打出 `6 / 3 / 3`。
- `strings/autocomplete_using_trie.py` 返回项会自带尾随空格，这是实现细节，不是格式化 bug。
- `ciphers/rsa_cipher.py` 在当前仓库快照下不是开箱可跑的：它依赖的 `maths/greatest_common_divisor.py` 第 76 行还保留了旧式 `except IndexError, UnboundLocalError, ValueError:` 语法，实际导入会触发 `SyntaxError`。如果要跑密码学示例，先修这处源码。
- `web_programming/` 下不少脚本需要你自己准备 API key，而且有些只是示例骨架，不应该直接拿去部署。

## ⚖️ 一句话判词

值得关注，特别适合读源码学算法、找题解模板、快速验证某类经典实现；不适合直接当生产库，也不适合把 `web_programming/` 和 `file_transfer/` 里的示例脚本原样上线。

## 📊 元信息

- 截至 **2026-06-01** 的 GitHub 页面：**Stars 222k / Forks 50.7k / Language Python（99.8%） / License MIT**
- 本地分析快照：`456d644`
