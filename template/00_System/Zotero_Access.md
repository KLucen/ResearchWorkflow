# Zotero 访问规范

> 本文件回答「**读 Zotero 时必须遵守什么**」：五色批注语义、评论归属判据、已知 API 陷阱、读取步骤。
> 具体命令与参数**不在本文件**——工具用法见发布包的 `tools/zotero/README.md`。
> 本文件不假设任何 harness 的专有工具：下面一律用 `python tools/zotero/rvzotero.py <子命令>` 表述；**任何等价的 Zotero 只读访问能力都可以替代它**（包括你所在环境自带的 Zotero 读取工具），但**陷阱与判据同样适用**。

## 1. 硬约束

| 约束 | 说明 |
|---|---|
| **只读** | Zotero 是不可变源。本工作流从不写入 Zotero；写回任何内容（含 AI 生成的笔记）都需研究者明确同意 |
| **禁止解析内部数据库** | 不得读取 `zotero.sqlite`、`prefs.js` 或 Zotero 的任何内部文件；一律走 Local API（或已封装它的访问层） |
| **PDF 不进 Vault** | 需要全文时读 PDF 所在路径提取文本到系统临时目录，用完即弃 |
| **不假设工具名** | 任何「只能用它」的写法都是错的；换了环境就换算子命令（能力映射表见 `agent/AGENTS.md`） |

Local API 默认地址 `http://127.0.0.1:23119/api`，可用环境变量 `RV_ZOTERO_API` 覆盖；库默认 `users/0`，可用 `RV_ZOTERO_LIBRARY` 覆盖。**须先运行 Zotero**，并打开 `Settings → Advanced → General → Allow other applications on this computer to communicate with Zotero`。

## 2. 能力映射（本工作流需要什么 → 用什么）

| 用途 | 访问层子命令 |
|---|---|
| 连通性自检 | `ping` |
| 检索条目（元数据 / 全文） | `search` |
| 单条目元数据（含笔记 / 批注 / 附件） | `get` |
| 子对象图（笔记 / 附件 / 批注） | `children` |
| **批注（自动分页补齐）** | `annotations` |
| 证据片段（Zotero 全文索引，带位置的排序片段） | `retrieve` |
| PDF 磁盘路径 | `attachment` |
| 全文 | `fulltext` |
| 引用 / 书目 | `export` |
| 集合树 | `collections` |
| 标签 | `tags` |
| 库增量 | `changes` |

*用 DSH（DeepSeek Harness）时*：内置的 `zotero_*` 工具是等价路径；**一旦它返回 0 条批注，不要相信「这篇论文没有批注」**——改用 `rvzotero.py annotations` 复核（原因见 §4.1）。完整对照表见发布包 `agent/adapters/dsh.md`。

**ingest 读取顺序**：`search` 定位条目 → **取研究者批注（§5，最优先）** → `get`（元数据 + 笔记）→ `retrieve`（证据片段；注意 `truncated` / `sourcesSkipped` 这类信号）→ 需要全文时 `attachment` 取路径 + 文本提取 → 引用信息按需 `export`。

## 3. 五色批注语义（研究者批注通道）

颜色是**研究者的输入信号**，既不是论文证据，也不是 Agent 的推断。Agent 必须按颜色分流，**不得自行改变语义**：

| 颜色 | 代码 | 语义 | 去向 |
|---|---|---|---|
| 🟡 黄 | `#ffd400` | **生词** | → `03_Vocabulary/`；**不进** E 对象、不进 Wiki |
| 🟢 绿 | `#5fb236` | **定义术语或术语解释内容**（"这里在定义什么"） | → E 对象 → `concept` 页 |
| 🔵 蓝 | `#2ea8e5` | **影响、观点、解决方法**（"作者主张什么、提出怎么解"） | → E 对象 → 主张登记表（默认 `+`） |
| 🔴 红 | `#ff6666` | **缺陷、现有问题、现有挑战**（"哪里有问题、还缺什么"） | → E 对象 → `−` 证据、§4 分歧、`gap/`（**`gap/` 页的主要来源**） |
| 🟣 紫 | `#a28ae5` | **与我的研究相关（可迁移 / 可借鉴）** | → §7 研究关系；`research_position` / `research_relevance` 判定的**首要依据** |

**红与蓝的边界**：🔵 是"作者提出 / 主张了什么"（含解决方法），🔴 是"哪里有问题、还缺什么"——后者**不限于本文自身的局限**，也包含领域层面的现有问题与挑战，因此它是 `gap/` 页的主要来源。

**紫色的特殊地位**：它是唯一 Agent 无法从文本自行推断的信号（绿蓝红都能推），因此是 `research_relevance` 与 `research_position` 判定的**首要依据**。
但紫色是**标记**，不是**回答**——只能作为 `R` 对象的候选，**不得自动写成 Researcher Response**。

## 4. 已知 API 陷阱

> 这四条是**真实踩过的坑**，不是理论风险。任何 Zotero 只读访问能力都必须按这里的办法复核。

### 4.1 `children` 不带 `itemType=annotation` 会静默返回 0 条批注

Zotero Local API 的 `GET /items/<key>/children` **默认不返回 annotation 条目**，必须显式带 `?itemType=annotation`：

| 请求 | 返回 |
|---|---|
| `/items/<attachment_key>/children` | **0 条** |
| `/items/<attachment_key>/children?itemType=annotation` | 全部批注 |

**不报错、不给提示**——这是最危险的失败模式：Agent 会据此得出「这篇论文没有批注」，从而错过研究者的全部输入。

**判据**：只要一条论文「应该有批注」（研究者说读完了 / 你在 Zotero 界面里看得到高亮），而工具读到 0 条，**先怀疑工具，不要怀疑研究者**。改用 `annotations` 子命令，并对本地 API 直接只读 GET 复核。

### 4.2 批注数量在 100 条处**静默截断**

按「取子对象」的方式读批注时（`children` 类接口、或把批注并入 `get` 的返回），只返回**前 100 条**，且**不报错、不给提示**。一篇批注密集的论文很容易超过 100 条——只按工具结果作业会**静默漏掉尾部批注**。

**补齐办法（只读）**：对本地 API 分页 GET，用响应头 `Total-Results` 判断总数，用 `start` 翻页：

```bash
# 只读；把 <attachment_key> 换成你的附件 key，<api> 换成你的 Local API 地址
curl.exe -s -o ann_a.json "<api>/users/0/items/<attachment_key>/children?itemType=annotation&limit=100&start=0"
curl.exe -s -o ann_b.json "<api>/users/0/items/<attachment_key>/children?itemType=annotation&limit=100&start=100"
```

- **优先用访问层的 `annotations` 子命令**——它已内置分页补齐；下面的直连办法只在没有访问层、或需要核验时用。
- **Windows 上必须用 `curl.exe`，不要用 PowerShell 的 `Invoke-RestMethod`**：Zotero Local API 回的是 `HTTP/1.0`，.NET 的 HTTP 栈会以「基础连接已经关闭」失败。这是协议版本问题，不是网络问题。
- **判据**：批注条数与工具读数不一致时，**先怀疑截断**——比对 `Total-Results` 与实际拿到条数；若某附件批注数接近或等于 100，必须分页补齐。

### 4.3 批注可能只挂在**某一个**附件上

一篇论文常有多个版本附件（原文 / 双语版 / 译文版 / 补充材料）。批注**可能只挂在其中一个上**——常见情形是研究者只在双语版上做了批注，而原始英文版是 0 条。

**做法**：取该条目的**全部** PDF 附件，逐个取批注；不要因为第一个附件是 0 条就收工。

### 4.4 附件之间**不保证同分页**

用章节标题类批注交叉验证页码基准：若批注挂在与导览声明的**不同附件**上，先确认两者分页是否一致，再决定 `location` 怎么写。**不要假设「同一个 PDF 的不同版本页码相同」。**

**归属提醒**：**集合作用域 ≠「这篇论文的批注」**。同一次阅读会话的批注可能落在不同论文上（一篇论文挂在多个集合、或批注工具按"最近读的"归属）；最终归属要靠**内容与 `annotationPageLabel`** 判断，不能靠集合。

## 5. 评论归属（按 `🔤…🔤` 区间切分）

`annotationComment` 里**机器词典与研究者的话经常同时出现**——典型形态是「`🔤机器译文🔤` + 换行 + 研究者自己写的话」。因此**判据是区间，不是"整条含不含 `🔤`"**：

| 来源 | 判据 | 归属 |
|---|---|---|
| 论文原文 | `annotationText`（高亮本身） | **Paper Evidence** ✔ 可作 `quote`；页码用 Zotero 官方 `annotationPageLabel` |
| 机器词典 | 评论中 `🔤…🔤` **区间内**的文字 | **`tool_generated`**：既不是论文原文，也不是研究者判断。只能进 Vocabulary 的「机器词典」行 |
| 研究者的话 | 评论中 `🔤…🔤` **区间外**的非空文字 | **研究者本人写的话**：如实记入 `pass2/` §8.1「研究者评论」列；要写成 `R` 对象仍需研究者确认 |
| 无评论 | `annotationComment` 为空 | 只有高亮，按颜色分流即可 |

两条铁律：

1. **机器词典永远不能成为 `quote`**——它是释义，不是原文（哪怕它与原文高度相似）。
2. **不得因为整条评论含 `🔤` 就把研究者的话一并丢弃**——区间外的文字是研究者写的，丢了就是丢数据。

切分结果必须**分开落点**：区间内 → Vocabulary「机器词典」行；区间外 → `pass2/` §8.1「研究者评论」列。

## 6. ingest 读取步骤

1. 取该条目的**全部** PDF 附件（原文 / 双语 / 译文……）——批注可能挂在任意一个上，**且可能只挂在其中一个上**（§4.3）。
2. 逐个附件取批注。**若某附件批注数接近或等于 100，必须分页补齐**（§4.2）——那是静默截断。
3. 按颜色分流：🟡 → Vocabulary；🟢🔵🔴 → 证据候选；🟣 → 研究关系（§3）。
4. 每条批注记录：`annotationText`、`annotationPageLabel`、`annotationColor`、`annotationComment`；**并把评论按 `🔤…🔤` 区间切成「机器词典」与「研究者的话」两部分**（§5），两者去向不同。
5. **用章节标题类批注交叉验证页码基准**：若批注挂在与导览声明不同的附件上，先确认两者分页是否一致，再决定 `location` 怎么写（§4.4）。
6. 批注**优先于** Agent 自己的通读结论——研究者标过的位置就是重点。

## 7. 元数据完整性

元数据缺 authors / year / DOI / venue 时：在 Paper Note 中**如实标注缺失**，并把 `reading_status` 与 `research_relevance` 的判定依据写清楚。

**补全 Zotero 元数据属写操作，需研究者同意**——Agent 只报告缺口，不自行修补。
