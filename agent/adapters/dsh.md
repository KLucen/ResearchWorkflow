---
title: DSH（DeepSeek Harness）接入
scope: agent/adapters
---

# DSH 接入：`zotero_*` 工具 ↔ `rvzotero.py` 子命令

> 本文件回答一个问题：**在 DSH 上跑这套工作流时，Zotero 到底怎么读**。
> 结论先给：**可以不装任何 Zotero 插件**——发布包自带的只读访问层 `tools/zotero/rvzotero.py` 覆盖了工作流需要的全部读取能力，而且是**唯一不会静默漏数据的那条路径**。
> 若你已经装了 `dsh-zotero` 插件，也能用：按下面的表把每个 `zotero_*` 调用翻译成子命令即可。

**通用接入契约**：[../AGENTS.md](../AGENTS.md)（先读它）。**五色语义**：`<VAULT>/00_System/Zotero_Access.md`（唯一事实源）。

---

## 一、装什么、装到哪

| 组件 | 装到哪 | 说明 |
|---|---|---|
| 技能 `researchvault` | `<DSH_HOME>/skills/researchvault/SKILL.md` | `<DSH_HOME>` 默认是 `~/.dsh`（Windows：`%USERPROFILE%\.dsh`），以 `DSH_HOME` 环境变量为准 |
| 技能 `researchvault-query` | `<DSH_HOME>/skills/researchvault-query/SKILL.md` | 同上 |
| Zotero 读取能力 | **不用装**——直接用 `<PKG>/tools/zotero/rvzotero.py` | 纯 Python 标准库，无依赖 |
| `dsh-zotero` 插件 | **可选** | 装了可以用 `zotero_*`；不装也不影响任何工作流步骤 |

**安装（bash / zsh）**：

```bash
mkdir -p "$DSH_HOME/skills/researchvault" "$DSH_HOME/skills/researchvault-query"
cp "<PKG>/agent/skills/researchvault/SKILL.md"       "$DSH_HOME/skills/researchvault/SKILL.md"
cp "<PKG>/agent/skills/researchvault-query/SKILL.md" "$DSH_HOME/skills/researchvault-query/SKILL.md"
```

**安装（PowerShell）**：

```powershell
$dsh = if ($env:DSH_HOME) { $env:DSH_HOME } else { "$env:USERPROFILE\.dsh" }
New-Item -ItemType Directory -Force -Path "$dsh\skills\researchvault","$dsh\skills\researchvault-query" | Out-Null
Copy-Item "<PKG>\agent\skills\researchvault\SKILL.md"       "$dsh\skills\researchvault\SKILL.md" -Force
Copy-Item "<PKG>\agent\skills\researchvault-query\SKILL.md" "$dsh\skills\researchvault-query\SKILL.md" -Force
```

**技能目录名必须与 frontmatter 的 `name` 一致**（`researchvault` / `researchvault-query`），文件名必须是 **`SKILL.md`**（全大写）。

**frontmatter 示例**（两份 SKILL.md 的头部就是这形状，直接可用）：

```yaml
---
name: researchvault
description: ResearchVault 科研工作流（Zotero 不可变源 + Obsidian 精读笔记与 Wiki，三层证据纪律 Paper Evidence / Agent Interpretation (Provisional) / Researcher Response）。用户要求精读或 ingest 论文、继续未完成的阅读问答、提出或批准 Wiki 变更、运行 lint、批量处理 Zotero 文献时加载。
---
```

`description` 决定**技能何时被自动加载**，所以要写清触发场景（这一段不要省）。

**装完自检**：

```bash
python "$RV_PKG/tools/zotero/rvzotero.py" ping       # 退出码 0
```

---

## 二、`zotero_*` ↔ `rvzotero.py` 完整对照表

**八个 DSH 工具，全部有等价项，一个不缺。**

| # | DSH 工具 | 等价子命令 | 参数映射 | 备注 |
|---|---|---|---|---|
| 1 | `zotero_search` | `search` | `query`→`--query/-q`；`mode`→`--qmode {titleCreatorYear,everything}`；`itemTypes`→`--item-type`（可重复）；`tags`→`--tag`；`collection`→`--collection`；`itemLevel:"top"`→`--top`；`limit`→`--limit`（≤100）；`offset`→`--offset`；`sort`/`direction` 同名 | 语义一致。**集合名要用集合 key 更稳**：先 `collections` 拿 key |
| 2 | `zotero_get` | `get` | `ref`→`--key/-k`；`include`→`--include notes,attachments,annotations`（逗号分隔）；`fields:"all"`→`--fields all` | 返回归一化元数据；`--fields all` 会把未被模型消费的字段放进 `extraFields` |
| 3 | `zotero_children` | `children` | `ref`→`--key/-k`；`include`→`--include attachments,notes,annotations`（**逗号分隔、复数**）；`limit`/`offset` 同名 | ⚠️ **见 §三：不带过滤参数会静默返回 0 条批注** |
| 4 | `zotero_retrieve` | `retrieve` | `ref`→`--key/-k`；`query`→`--query/-q`；`passages`→`--passages`；`sources`→ **无直接对应**：改用 `annotations --color` 单独取某一色批注、或 `annotations` + `get --include notes` 自行合并 | 返回相关度排序的片段 + 页码；**页码来自逐页全文索引，不是批注标签** |
| 5 | `zotero_attachment` | `attachment` | `ref`→`--key/-k`；`全部附件`→`--all`；`storage 目录`→`--storage <目录>`（不给则自动探测，或读 `RV_ZOTERO_STORAGE`） | `--all` 返回每个附件的 `path` / `pathKind` / `exists` / `linkMode` |
| 6 | `zotero_export` | `export` | `refs`→`--key/-k`（**可重复**）；`format`→`--format {bibtex,biblatex,ris,csljson,citation}`；`style`→`--style {apa,ieee,gb-t-7714}` | `citation` 由脚本本地排版（Local API 不支持 `format=citation`，直连会 400） |
| 7 | `zotero_browse` | `collections` / `tags` / `searches` | `kind:"collections"`→`collections`；`kind:"tags"`→`tags`（`q`→`--query/-q`，`limit`/`offset` 同名）；`kind:"savedSearches"`→`searches` | 一个 DSH 工具拆成三个子命令。**`kind:"libraries"` / `"itemTypes"` / `"itemFields"` 无对应项**（本工作流用不到：库固定 `users/0`，条目类型在 `Config.md` 里） |
| 8 | `zotero_changes` | `changes` | `since`→`--since`；`快照文件`→`--db` | **机制不同**：Local API 没有 `/changes` 端点，`changes` 是**本地快照比对**。首次运行返回 `mode: "baseline"` + `libraryVersion`；没有 `--db` 就只能看新增/修改，**删除检测需要 `--db` 快照** |
| ＋ | *(无)* | `ping` | — | DSH 无对应工具；**这是每条工作流的第 0 步**，退出码 `0` 才能继续 |
| ＋ | *(无)* | `fulltext` | `--key/-k`、`--pages A-B`（如 `3-7`；单页写 `5`）、`--out` | DSH 无对应工具。**按页取全文**只能靠它；`--pages` 是**本地切页**（Zotero 不支持按页取，整篇仍会被取回一次）；直接调 `/items/<key>/fulltext` 用父条目 key 会 404 |
| ＋ | *(无)* | `annotations` | `--key/-k`、`--color`（`yellow/green/blue/red/purple` 或 `#rrggbb`）、`--attachment`、`--first-attachment`、`--all`、`--limit`、`--page-size`、`--split-comment` | DSH 无对应工具。**这是读批注的正规入口**，见 §三。输出顶层带 `attachments`（逐附件分项），「每个附件各多少条批注」直接读它，不必绕 `children`；`--all` 默认已是全部、此开关无操作 |

### 参数映射速查（高频）

| 概念 | DSH | `rvzotero.py` |
|---|---|---|
| 条目引用 | `ref: "zotero://user/0/item/ABCD1234"` | `--key ABCD1234`（**只要 key，不要整条 ref**） |
| 只要顶层条目 | `itemLevel: "top"` | `--top` |
| 输出给人看 | 工具自带渲染 | `--human`（不要自己排版） |
| 输出给程序 | 工具返回对象 | `--json`（**默认**） |
| 评论区间切分 | 无 | `--split-comment`（拿到 `commentParts`） |
| 库 | 插件设置 | `RV_ZOTERO_LIBRARY`（默认 `users/0`） |
| API 端口 | 插件设置 | `RV_ZOTERO_API`（默认 `http://127.0.0.1:23119/api`） |

---

## 三、为什么可以完全不装插件

三个理由，按重要性排序：

### 1. 插件在批注读取上有一个**静默漏数据**的历史缺陷

DSH 的 Zotero 工具链底层就是 Zotero Local API。Local API 的 `/items/<key>/children` **默认不返回批注**——批注在 Zotero 里是**挂在 PDF 附件下**的子对象，只有显式传 `itemType=annotation` 才会返回：

| 调用方式 | 结果 |
|---|---|
| `zotero_children`（**不带**批注过滤参数，如只传 `ref`） | **HTTP 200 + 批注 0 条**——不报错，看起来就是「这篇论文没有批注」 |
| `rvzotero.py annotations --key <ITEMKEY>` | **始终显式带 `itemType=annotation`**，并自动翻页到 `Total-Results` |

**这是本工作流最危险的一类错误**：五色批注是 `pass2/` 与 `gap/` 页的**唯一输入信号**。静默返回 0 条 → 你会写出一份「这篇论文没有批注」的 `pass2/`，而实际上研究者的批注一条没读。

历史上研究者为此专门给插件打过补丁；`rvzotero.py` 把这套行为固化在代码里，**不依赖插件补丁是否还在位**。

### 2. 插件是「可选增强」，不是依赖

工作流要的读取能力有 12 项（列集合 / 读元数据 / 读批注 / 读全文 / 全文检索 / 找 PDF 路径 / 导出引用 / 看库变化 …），`rvzotero.py` 全部覆盖，且**只用 Python 标准库**——不需要 pip、不需要 MCP、不需要网络。

### 3. 少一个会漂移的层

插件的设置（API 地址、库 ID、批注读取行为）是**插件自己的状态**，跟着插件版本走；`rvzotero.py` 的行为跟着发布包走，且参数可以随时用 `--help` 自查。**层数越少，出错的地方越少。**

### 那什么时候还用插件

- 你只想**快速看一眼**某条元数据，不想敲命令；
- 插件已经装好且你**已验证它这次能读出批注**（见下面的核对流程）。

**一旦它和 `rvzotero.py` 的结果不一致，以 `rvzotero.py` 为准。**

---

## 四、从插件迁移过来的注意事项

| # | 注意什么 | 怎么做 |
|---|---|---|
| 1 | **批注条数必须核对** | 迁移后对同一篇论文跑两次：`zotero_children`（或插件读批注）与 `rvzotero.py annotations --key <ITEMKEY> --all`。**条数不一致 → 以 `rvzotero.py` 为准**，并检查是不是插件那条路径漏了 |
| 2 | **ref 要转成 key** | 插件收 `zotero://user/0/item/ABCD1234`，脚本只要 `--key ABCD1234`。整条 ref 传进去会 `5`（not found） |
| 3 | **`--include` 只认复数** | 三类取值在 `get` 与 `children` 上**都是复数**（`notes` / `attachments` / `annotations`）；写单数会直接报**参数错误**（退出码 `2`）。**旧版本**的 `children --help` 曾把取值印成单数（只看帮助会被带偏），**已修正**：实现与帮助文本现在都只认复数，并有回归测试锁死 |
| 4 | **批注只挂在某一个附件上** | 迁移后**先跑 `children`** 看结构：一篇论文常有多份 PDF（原文 / 双语 / 译文），批注只在研究者实际读的那份上。**只查第一个附件会漏**；`annotations --key` 默认聚合全部附件 |
| 5 | **100 条截断** | Local API **每页**最多 100 条且**静默截断**。`rvzotero.py annotations` **已自动翻完全部分页、默认取全部命中**（取完还会**校验总数**，对不上就报错而不是悄悄少给）；`--all` 只是把「取全部」的意图写明白（默认已是全部）。**别把 `--page-size` 往大调**（上限就是 100） |
| 6 | **`zotero_retrieve` 的 `sources` 没有对应项** | 想「批注 + 笔记 + 摘要 + 全文一起排」时，用 `annotations` / `get --include notes` / `retrieve` 分别取，再自己合并 |
| 7 | **`zotero_changes` 不是服务端 delta** | Local API 无 `/changes`；`changes` 靠本地快照。**想要删除检测必须持续用同一个 `--db` 文件**，否则只能看到新增/修改 |
| 8 | **`zotero_export` 的 `citation` 是本地渲染** | Local API 不支持 `format=citation`（直连 400）。脚本在本地排版，所以样式只用 `--style {apa,ieee,gb-t-7714}` 这三档 |
| 9 | **PowerShell 不要直连 API** | Local API 回 **HTTP/1.0**，`Invoke-RestMethod` 在握手阶段就失败。**用脚本**，或 `curl.exe -o out.json` |
| 10 | **不要为了「快」跳过 `ping`** | 插件停了/端口变了，脚本会给你明确的退出码（`3` 连不上、`4` 库不对），比插件静默返回空结果好排查 |

---

## 五、迁移核对流程（跑一遍再删插件）

```bash
cd "<PKG>"

# 1) 底层连通性
python tools/zotero/rvzotero.py ping                       # 期望 0

# 2) 挑一篇你知道「肯定有批注」的论文
python tools/zotero/rvzotero.py search --query "<题名片段>" --limit 5

# 3) 看结构：几个附件、每条附件上分别多少条批注
python tools/zotero/rvzotero.py children --key <ITEMKEY> --include attachments,notes,annotations

# 4) 读批注（全附件聚合 + 区间切分），把条数与插件的结果对比
python tools/zotero/rvzotero.py annotations --key <ITEMKEY> --split-comment --all

# 5) 五色各取一次，确认颜色映射与 Zotero_Access.md 一致
python tools/zotero/rvzotero.py annotations --key <ITEMKEY> --color purple
python tools/zotero/rvzotero.py annotations --key <ITEMKEY> --color red

# 6) 全文两条路
python tools/zotero/rvzotero.py retrieve --key <ITEMKEY> --query "<问题>" --passages 5
python tools/zotero/rvzotero.py attachment --key <ITEMKEY> --all
```

**第 4 步条数一致** → 可以放心不用插件。**不一致** → 用 `rvzotero.py`，并记下差异（很可能是插件那条路径没带 `itemType=annotation`，或漏了某个附件）。

---

## 六、本 harness 上最容易踩的三个坑

1. **`zotero_children` 静默 0 条批注**（§三·1）——凡是要用批注的地方，一律改用 `rvzotero.py annotations`。
2. **评论里的机器词典被当成研究者的话**（或反过来，整条被丢掉）——`annotationComment` 常见形态是「`🔤机器译文🔤` + 换行 + 研究者自己写的话」。**按 `🔤…🔤` 区间切分**：区间内是 `tool_generated`（**永不作 `quote`**），区间外才是研究者本人写的话。用 `--split-comment` 让脚本替你切。
3. **把 `retrieve` 的页码当成批注页码**——`retrieve` 的 `page` 来自逐页全文索引；引用批注位置要用 `annotationPageLabel`，并注明是哪个附件的页码。

---

## 七、相关文档

- 通用接入契约：[../AGENTS.md](../AGENTS.md)
- 技能正文：[../skills/researchvault/SKILL.md](../skills/researchvault/SKILL.md) · [../skills/researchvault-query/SKILL.md](../skills/researchvault-query/SKILL.md)
- 其它 harness：[claude-code.md](claude-code.md) · [cursor.md](cursor.md) · [codex.md](codex.md) · [generic.md](generic.md)
- 五色语义与 API 陷阱（唯一事实源）：`<VAULT>/00_System/Zotero_Access.md`
- 完整参数：`python tools/zotero/rvzotero.py <子命令> --help`
