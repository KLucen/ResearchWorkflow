---
title: Agent 接入契约
scope: 任何 Agent harness
---

# Agent 接入契约（ResearchWorkflow）

> **本文件是本发布包对外的唯一接入契约**：任何 Agent（无论跑在哪个 harness 上）进入这套研究工作流，都先读本文件。
> 它只回答两件事：**你需要什么能力**、**每个动作具体怎么执行**。
> **纪律**以 `<VAULT>/00_System/AGENTS.md` 为准，**路径与参数**以 `<VAULT>/00_System/Config.md` 为准，**五色批注语义**以 `<VAULT>/00_System/Zotero_Access.md` 为准——本文件不另立一套说法，只做映射。

---

## 0. 三句话版本

1. 这是一套**把 Zotero 里的文献变成有证据支撑的 Obsidian 精读笔记与 Wiki** 的工作流；Zotero 是不可变源，**只读**。
2. 读 Zotero 的统一入口是发布包内的只读访问层 `tools/zotero/rvzotero.py <子命令>`（纯 Python 标准库）。**任何等价的 Zotero 只读访问能力都可以替代它**——若你的 harness 自带 Zotero 工具，按 `agent/adapters/` 下的对照表映射即可。
3. 你**不需要**安装任何特定插件，也**不得**假设自己拥有某个 harness 的专有工具。

---

## 1. 先解析两个路径

本文档、`tools/` 与 `template/` 都在**发布包根目录**（下称 `<PKG>`）下。所有命令里的相对路径都以 `<PKG>` 为基准。

| 占位符 | 含义 | 怎么确定 |
|---|---|---|
| `<PKG>` | 发布包根目录（含 `tools/`、`template/`、`agent/`） | 本文件所在目录的上两级：`agent/AGENTS.md` → `<PKG>/agent/` → `<PKG>` |
| `<VAULT>` | 你的研究仓库根目录（Obsidian 打开的那个目录） | ① 用户直接告知；② `Config.md` 的 §1.1 环境事实表；③ 若 `<PKG>/template/` 已被复制进 Vault，则 `<VAULT>/00_System/Config.md` 存在即为标记 |

**建议先固化这两个变量**，后面所有命令都用它们，避免手抄长路径：

```bash
# bash / zsh
export RV_PKG="/path/to/ResearchWorkflow"     # 发布包根目录
export RV_VAULT="/path/to/your-vault"         # 你的 Vault 根目录
python "$RV_PKG/tools/zotero/rvzotero.py" ping
```

```powershell
# PowerShell
$env:RV_PKG   = "X:\path\to\ResearchWorkflow"
$env:RV_VAULT = "X:\path\to\your-vault"
python "$env:RV_PKG\tools\zotero\rvzotero.py" ping
```

> 这两个变量是**给命令用的约定**，不是访问层读取的环境变量（访问层读的是 `RV_ZOTERO_API` / `RV_ZOTERO_LIBRARY` / `RV_ZOTERO_STORAGE`，见 §3.2）。变量名不要混用。

**若 `<VAULT>/00_System/` 不存在**：说明还没初始化。让用户把 `<PKG>/template/` 的内容复制到 Vault 根目录，并按 `<VAULT>/00_System/Config.md` §1 的「首次运行清单」逐项填完（尤其是 §1.1 环境事实表）。**在环境事实表填完之前不要开始 ingest**——否则路径全靠猜。

---

## 2. 你需要的能力（只有三项）

| 能力 | 用途 | 最低要求 |
|---|---|---|
| **读文件** | 读 `00_System/*.md`、`pass1/`、`pass2/`、`02_Wiki/`、`03_Vocabulary/` | 能按路径读 UTF-8 文本 |
| **写文件** | 写导读、Paper Note、Wiki 页、`lint-report.md`、`log.md` | 能创建/覆盖写文本；能移动文件（`待精读/` ↔ `已精读/`） |
| **运行命令** | 调用 `python tools/zotero/rvzotero.py <子命令>` | 能执行 shell 命令并读取 stdout / 退出码 |

**你需要具备**：已安装 Python **3.8+**（访问层只用标准库，**不需要 pip 安装任何包**）、Zotero 正在运行、且在 Zotero 里已打开 `Settings → Advanced → General → Allow other applications on this computer to communicate with Zotero`。

**你不需要具备**：任何 Zotero 插件、MCP server、向量数据库、网络访问。

**自检（必须先通过）**：

```bash
python "$RV_PKG/tools/zotero/rvzotero.py" ping
```

| 退出码 | 含义 | 怎么办 |
|---|---|---|
| `0` | 通了 | 继续 |
| `2` | 参数错误 | 检查子命令与参数拼写 |
| `3` | **连不上 Zotero** | Zotero 没运行 / 未打开上面那个开关 / Local API 端口不是 23119（用 `RV_ZOTERO_API` 覆盖） |
| `4` | Zotero 返回了非 200/404 的错误 | 看报错正文；多为库路径或库 ID 不对（`RV_ZOTERO_LIBRARY`） |
| `5` | 没找到目标条目 / 附件 / 集合 | key 拼错，或该条目不在当前库 |

---

## 3. 能力映射表（**核心**）

左列是工作流里真正要做的动作；右列是**唯一权威实现**。命令一律从 `<PKG>` 调用：

```bash
python tools/zotero/rvzotero.py <子命令> [参数]
```

| # | 工作流动作 | 子命令 | 可执行命令示例 |
|---|---|---|---|
| 1 | **自检：Zotero 通不通** | `ping` | `rvzotero.py ping` |
| 2 | **列集合**（拿集合 key / 条目数 / 层级） | `collections` | `rvzotero.py collections` |
| 3 | **按关键词/标签/集合找条目** | `search` | `rvzotero.py search --query "survey" --item-type journalArticle --top --limit 25` |
| 4 | **列标签** | `tags` | `rvzotero.py tags --query "<关键词>" --limit 50` |
| 5 | **读条目元数据**（题名 / 作者 / 年份 / DOI / venue） | `get` | `rvzotero.py get --key <ITEMKEY> --fields all` |
| 6 | **读条目的批注**（五色分流的原料） | `annotations` | `rvzotero.py annotations --key <ITEMKEY> --split-comment` |
| 7 | **读批注并只看某一色** | `annotations --color` | `rvzotero.py annotations --key <ITEMKEY> --color purple --split-comment` |
| 8 | **看子对象结构**（附件 / 笔记 / 批注各有几条） | `children` | `rvzotero.py children --key <ITEMKEY> --include attachments,notes,annotations` |
| 9 | **找 PDF 的磁盘路径**（准备提取全文） | `attachment` | `rvzotero.py attachment --key <ITEMKEY> --all` |
| 10 | **拿全文**（Zotero 全文索引，按页） | `fulltext` | `rvzotero.py fulltext --key <ITEMKEY> --pages 1-20` |
| 11 | **全文检索**（按相关度返回片段 + 页码） | `retrieve` | `rvzotero.py retrieve --key <ITEMKEY> --query "<问题>" --passages 5` |
| 12 | **导出引用**（bibtex / ris / csljson / 本地排版 citation） | `export` | `rvzotero.py export --key <ITEMKEY> --format bibtex` |
| 13 | **看库有没有变化**（新增 / 修改 / 删除） | `changes` | `rvzotero.py changes --since <上次库版本号> --db <快照文件>` |

**三项通用开关**（除个别子命令外都适用）：

- `--json`：输出 JSON（**默认**；程序化处理用它）。
- `--human`：人类可读表格（**需要给用户看结果时用它**，不要自己排版）。
- `--split-comment`：**按 `🔤…🔤` 区间切分评论归属**（`annotations` / `get` / `children` 支持）。**做批注分流时必须带上它**——否则机器词典与研究者的话混在一个字段里，一定会出错。

完整参数（每个子命令的 `--help`）见 `tools/zotero/README.md`；随时可直接查：

```bash
python tools/zotero/rvzotero.py annotations --help
```

### 3.1 常用动作的推荐序列

**ingest 一篇新论文（读阶段）**：

```bash
# 1) 定位条目
python tools/zotero/rvzotero.py search --query "<题名片段>" --limit 5
# 2) 元数据（顺带看有没有缺 authors / year / venue / DOI）
python tools/zotero/rvzotero.py get --key <ITEMKEY> --fields all --include notes,attachments
# 3) 子对象全貌：几个附件、几条笔记、**每条附件上分别有多少条批注**
python tools/zotero/rvzotero.py children --key <ITEMKEY> --include attachments,notes,annotations
# 4) 研究者批注（全附件聚合 + 区间切分）
python tools/zotero/rvzotero.py annotations --key <ITEMKEY> --split-comment --all
# 5) 全文：先按相关度取片段，再按需取页（--pages 是本地切页，Zotero 不支持按页取，整篇仍会被取回一次）
python tools/zotero/rvzotero.py retrieve --key <ITEMKEY> --query "<要回答的问题>" --passages 8
python tools/zotero/rvzotero.py fulltext --key <ITEMKEY> --pages 1-30
# 6) 需要磁盘上的 PDF 时（全文索引给不出你要的细节）
python tools/zotero/rvzotero.py attachment --key <ITEMKEY> --all
```

**query（回答研究问题）时的下钻顺序**：`02_Wiki/` → `01_Papers/pass2/` → Zotero（第 5、6 步）→ 仍不足再取 PDF 文本。**`01_Papers/pass1/` 是导读，不作引用来源。**

### 3.2 可用环境变量（访问层读取，不是你随便起的名字）

| 变量 | 作用 | 默认 |
|---|---|---|
| `RV_ZOTERO_API` | Local API 基址 | `http://127.0.0.1:23119/api` |
| `RV_ZOTERO_LIBRARY` | 库 | `users/0`（团队库写 `groups/<id>`） |
| `RV_ZOTERO_STORAGE` | Zotero storage 目录（`attachment` 找不到文件时用） | 自动探测 |

> **换机器时**：先填 `Config.md` 的 §1.1 环境事实表，再跑 `ping`。若端口或库不同，**优先用环境变量覆盖，不要改 `rvzotero.py` 的代码**（改了就无法跟着发布包升级）。

---

## 4. 纪律契约（进入工作流即生效，不得弱化）

### 4.1 三层证据不得混淆

| 层 | 是什么 | 你能做什么 |
|---|---|---|
| **Paper Evidence** | 论文原文 + 精确定位（页 / 节 / 图 / 表 / 附录） | 可作 `quote`；页码优先用 Zotero 官方的 `annotationPageLabel` |
| **Agent Interpretation (Provisional)** | 你的推断 | 必须**显式标注为暂定**，不得写成结论 |
| **Researcher Response** | **只有研究者本人说的话** | 未回答处保留 `PENDING_RESEARCHER_RESPONSE` |

**你永远不得代研究者作答。** 需要研究者判断的地方，就把问题留下，把空位留空。

### 4.2 `🔤…🔤` 是机器词典，不是论文原文

`annotationComment` 里机器词典与研究者的话**经常同时出现**（典型形态：`🔤机器译文🔤` + 换行 + 研究者自己写的话）。**判据是区间，不是「整条含不含 `🔤`」**：

| 来源 | 判据 | 归属 |
|---|---|---|
| 论文原文 | `annotationText` | **Paper Evidence** ✔ 可作 `quote` |
| 机器词典 | 评论中 `🔤…🔤` **区间内**的文字 | `tool_generated`；**永不作 `quote`**，只能进 Vocabulary 的「机器词典」行 |
| 研究者的话 | 评论中 `🔤…🔤` **区间外**的非空文字 | 研究者本人写的话，记入 `pass2/` §8.1 |
| 无评论 | `annotationComment` 为空 | 只有高亮，按颜色分流即可 |

**不得因为整条评论含 `🔤` 就把研究者的话一并丢掉。** 用 `--split-comment` 让访问层替你切分：切分结果在 `commentParts` 里，`machine_texts` = 机器词典，`researcher_text` = 研究者的话。

### 4.3 五色批注语义

> **唯一事实源**：`<VAULT>/00_System/Zotero_Access.md` §3。下表是速查，**冲突时以该文件为准**。

| 颜色 | 代码 | 语义 | 去向 |
|---|---|---|---|
| 🟡 黄 | `#ffd400` | **生词** | `03_Vocabulary/`；**不进** E 对象、不进 Wiki |
| 🟢 绿 | `#5fb236` | **定义术语或术语解释** | E 对象 → `02_Wiki/concept/` |
| 🔵 蓝 | `#2ea8e5` | **影响、观点、解决方法** | E 对象 → 主张登记表（默认 `+`） |
| 🔴 红 | `#ff6666` | **缺陷、现有问题、现有挑战** | E 对象（`−`）→ 分歧、`gap/`（**`gap/` 的主要来源**） |
| 🟣 紫 | `#a28ae5` | **与我的研究相关** | `pass2/` §7 研究关系；`research_position` 的**首要依据** |

红蓝边界：🔵 是「作者提出 / 主张了什么」，🔴 是「哪里有问题、还缺什么」（不限于本文局限，也包括领域层面的现有问题与挑战）。

**紫色是唯一你无法从文本推断的信号**，但紫是**标记**而非**回答**——只能作为 `R` 对象的候选，**不得自动写成 Researcher Response**。

### 4.4 两步 ingest：先导读，后成稿

| 文件 | 何时生成 | 性质 |
|---|---|---|
| `01_Papers/pass1/待精读/<zotero_key>_<短标题>.md` | ingest 时，**只此一次** | 5 分钟阅读导览（**阅读辅助，不是证据**） |
| `01_Papers/pass2/<同名>.md` | **研究者做完五色批注之后** | 精读总结（**证据层，唯一来源**） |

- **不得跳过批注直接生成 `pass2/`**——缺批注就不生成，否则会产出一个未经确认却长得像结论的证据源。
- **位置即状态**：导读在 `待精读/` = 尚未成稿；`pass2/` 一旦存在，导读就应移入 `已精读/`。**不在导读里写状态字段**（那是双写）。
- **pass1 绝不双写**：导读里**不得出现** `E` 编号、主张、Wiki 提案、`R` 对象、`PENDING_RESEARCHER_RESPONSE`。
- 导读**全文 ≈1000 中文字，1200–1300 字为上限**（宁短不长）；**不写实验结果、数字、作者对结果的解释与最终结论**。
- 两份文件**按文件名配对、互不复制内容**；文件名一旦确定保持稳定（重命名会打断 `[[链接]]` 与配对；在 `待精读/` ↔ `已精读/` 之间移动不算改名）。
- **`_` 前缀 = 基础设施**：以 `_` 开头的文件（模板、入口页、索引，如 `_WikiIndex.md`、`_Paper_Template.md`、`_Reading_Guide_Template.md`）是发布包自带的基础设施，Obsidian 视图、Dataview 查询与 lint **一律跳过它们**；给真实笔记 / Wiki 页 / 词条起名时**不要**用 `_` 开头。

### 4.5 Wiki 变更需研究者批准

- 主张（claim）**先提案**（写进 `pass2/` §11 主张级变更表）→ **研究者批准** → 才写入 `02_Wiki/`。
- 目录即类型：`topic/` `concept/` `synthesis/` `gap/` `entity/`；**frontmatter 不写 `type`**；内容页必须落在这五个目录之一——`02_Wiki/` 根下只允许 `_` 前缀的基础设施文件（`_WikiIndex.md`、`_Wiki_Template.md`），非 `_` 前缀的文件落在根下即违规。Dataview 查询用 `file.folder`。
- §2 主张登记表是**唯一事实源**，8 列固定：`ID | 主张 | 证据 | 状态 | 批准 | 生效 | 失效 | 替代`；证据列强制三段式 `[[Paper Note]]E编号 (页码)`。
- 状态**不得跳级**：`proposed → supported`（≥2 篇**独立**论文）`→ consensus`（研究者批准）；出现 `−` 证据转 `contested`；被推翻标 `refuted`。**同一篇论文的多个实验不算独立。**
- **只增行、只改状态，行永不删除**；`retired_at` 非空的内容**检索期默认过滤**；更新走**最小 diff**，**禁止把新素材追加到页尾**。
- 每第 5 篇 ingest 后**建议**跑一次合并检查——**只建议，不自行执行**。

### 4.6 Zotero 只读，PDF 不进 Vault

- Zotero 是**不可变源**：读它，不改它。**写回任何内容（含你生成的笔记）都需研究者明确同意。**
- **禁止**直接解析 `zotero.sqlite` / `prefs.js` 或任何 Zotero 内部数据库文件。
- **禁止**把 PDF 复制进 Vault；需要全文时把文本提取到**系统临时目录**，用完即弃。

### 4.7 需要研究者同意的动作

删除或批量修改 Zotero 条目 · 向 Zotero 写回任何内容 · 覆盖研究者已写的段落 · 删除或大规模移动 Vault 文件 · 把研究者判断提升为 Wiki 持久结论 · 标记 Vocabulary 的 `acquired`。

### 4.8 你没有权限碰的东西

- `<VAULT>/.obsidian/`、`.git/`、同步工具目录、`.trash/`——不是本工作流产出的，一律不读不写。
- `00_System/*_Schema.md`、`AGENTS.md`：**只读**（改纪律需研究者同意）。
- `00_System/Config.md`：研究者填；你只在被明确要求时改。

---

## 5. 语言与引文体例

- **说明性内容一律中文**：分析、解读、问题、局限、Wiki 正文、你的对话回复，都是中文。
- **原文摘录保持原语言**，**紧随其后给中文翻译**：多行用 `原文（EN）："…"` / `译文（ZH）："…"`；短句用 `> "…"（译：…）`。
- **不译**：数字、单位、公式、变量名、模型名、数据集名、指标名（如 F1、BLEU）、引用键。
- **术语**：首次出现写「中文（English）」，此后全文一致。
- **frontmatter 的键与枚举值一律英文**（机器可读，是 Dataview 与 lint 的接口，永不翻译）。
- **摘录纪律**：只摘支撑论断的短句，不成段复制原文——全文始终留在 Zotero。

---

## 6. 接口的稳定性承诺

- 子命令名与参数名**以 `python tools/zotero/rvzotero.py <子命令> --help` 的实时输出为准**（本文件的表按 v1.0.0 编写）。
- 访问层**只读**：任何子命令都不会写 Zotero。
- 若你必须写一套自己的 Zotero 读取实现（例如目标机器装不了 Python），**只要满足同样的能力清单与陷阱处理**（§3 + §7），就可以替代本访问层——但要在你的本地文档里记下替代关系。

---

## 7. 已知陷阱（**必须处理，否则会静默出错**）

| # | 陷阱 | 后果 | 正确做法 |
|---|---|---|---|
| 1 | 直接用 `/items/<key>/children` **不带** `itemType=annotation` | **静默返回 0 条批注**（HTTP 200，不报错）——看起来「这篇论文没有批注」，其实是查询方式错了 | 用 `annotations`（永远显式带该参数）或 `children --include annotations` |
| 2 | **绕过访问层**直接查批注时，Zotero API **每页最多 100 条且静默截断**（不报错） | 漏掉第 101 条之后的批注 | 用 `annotations`——它**已自动翻完全部分页、默认取全部命中**（并校验总数）；`--page-size` 不要调大（上限就是 100） |
| 3 | 一篇论文有**多个附件**（原文 PDF / 双语 PDF / 译文 PDF），批注**只挂在研究者实际读的那一个**上 | 只查第一个附件会漏 | 用 `annotations --key <ITEMKEY>`（**默认聚合全部附件**）；要精确定位用 `--attachment <附件KEY>`；先跑 `children` 看清哪个附件有批注 |
| 4 | 用父条目 key 调 `/items/<key>/fulltext` | `404`（该端点只接受**附件** key） | 用 `fulltext --key <ITEMKEY>`，访问层会自动解析成最好的 PDF 附件 |
| 5 | PowerShell 的 `Invoke-RestMethod` 直连 Local API | 握手阶段失败（Local API 回 **HTTP/1.0**） | 用本访问层；或 `curl.exe -o out.json`。**不要用 `Invoke-RestMethod`** |
| 6 | Zotero 集合作用域 ≠ 该论文的批注范围 | 把集合里别的论文的批注算到这篇头上 | 批注一律**按条目 key** 查 |
| 7 | 多个附件之间**不保证批注落在同一分页** | 页码对不上 | 页码一律用该批注自己的 `annotationPageLabel`，并注明是**哪个附件**的页码 |
| 8 | `--include` 写了单数（`attachment,note,annotation`） | 报**参数错误**（退出码 `2`）。注意：**旧版本**的 `children --help` 曾把取值印成单数，只看帮助会被带偏 | 三类取值**一律用复数**：`notes` / `attachments` / `annotations`（`get` 与 `children` 相同）。该帮助笔误**已修正**——实现与帮助文本现在都只认复数，并有回归测试锁死 |

**诚实信号**：访问层输出里的 `truncated` / `sourcesSkipped` / `scanned` / `attachments` / 空 `results` **都是真的信号**——**「没取到」不等于「不存在」**。见到它们要在结论里如实说明，不得静默当成「没有」。
`retrieve` 返回的 `page` 来自 Zotero 的**逐页全文索引**（从 1 开始），**不是**批注页码标签；引用批注位置时用 `annotationPageLabel`。

---

## 8. 按 harness 安装

选你正在用的那一栏，照做即可；**每一栏都给出具体文件路径、安装命令与 frontmatter 示例**。

| harness | 接入方式 | 文档 |
|---|---|---|
| **DSH（DeepSeek Harness）** | 技能装到 `<DSH_HOME>/skills/<技能名>/SKILL.md`；**可以不装 Zotero 插件**，`zotero_*` 工具 ↔ `rvzotero.py` 子命令有完整对照表 | [adapters/dsh.md](adapters/dsh.md) |
| **Claude Code** | `CLAUDE.md` 放契约；技能装到 `.claude/skills/<技能名>/SKILL.md` | [adapters/claude-code.md](adapters/claude-code.md) |
| **Cursor** | `.cursor/rules/*.mdc`（**必须是 `.mdc`**，`.md` 会被忽略） | [adapters/cursor.md](adapters/cursor.md) |
| **Codex / 通用 AGENTS.md 约定** | 把契约做成项目根 `AGENTS.md` | [adapters/codex.md](adapters/codex.md) |
| **任意其他 Agent** | 把 §2–§5 贴进 system prompt；cwd 指向 Vault | [adapters/generic.md](adapters/generic.md) |

技能正文见：

- [skills/researchvault/SKILL.md](skills/researchvault/SKILL.md) —— ingest / 继续问答 / Wiki 提案 / lint / 批量
- [skills/researchvault-query/SKILL.md](skills/researchvault-query/SKILL.md) —— 四分类问答与下钻顺序

两份 `SKILL.md` 是**通用格式**（YAML frontmatter + 可执行操作规程），与 harness 无关；上面五个 adapter 只负责「把它放到你那个 harness 会读的位置」。

---

## 9. 开工前的检查清单

- [ ] `python tools/zotero/rvzotero.py ping` 退出码为 `0`
- [ ] 已读 `<VAULT>/00_System/Config.md`（**路径与环境事实源**，别凭记忆假设路径）
- [ ] 已读 `<VAULT>/00_System/AGENTS.md`（纪律）
- [ ] 已读 `<VAULT>/00_System/Zotero_Access.md`（五色语义 + API 陷阱）
- [ ] ingest 前确认这篇论文**是否已有** `pass2/<同名>.md`；有则走「继续问答」，不要重出导读
- [ ] 读批注时带上 `--split-comment`，并先跑 `children` 确认批注挂在哪个附件上
- [ ] 写 `pass2/` 前确认研究者**已经批注**；否则停在 §4.4 的第一步
- [ ] 写 `02_Wiki/` 前确认**已有研究者批准**
