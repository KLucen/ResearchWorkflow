# Paper Note Schema（阅读导览 + 精读笔记结构）

> 本文件规定 `01_Papers/` 下两份产物的结构：**阅读导览**（`pass1/`，阅读辅助）与**精读笔记**（`pass2/`，证据层）。
> **一份论文两份文件、先后两步**：先出 `pass1/待精读/` 的 5 分钟导览 → 研究者在 Zotero 里读原文并做五色批注 → 才生成 `pass2/` 的精读笔记。两份**按文件名配对、互不复制内容**。
> **`pass2/` 只在研究者批注之后生成**——批注是它的主要输入，不是事后补丁。
> **Wiki 提案只在 `pass2/` 提**——导读阶段尚无研究者批注，此时提主张只会产生单来源噪音页。

相关文档：执行纪律见 `AGENTS.md`；操作步骤见 `Workflow.md`；Zotero 读取与五色批注见 `Zotero_Access.md`；Wiki 侧结构见 `Wiki_Schema.md`。

## 0. 文件与命名

| 产物 | 路径 | 何时生成 | 何时再改 |
|---|---|---|---|
| 阅读导览 | `<VAULT>/01_Papers/pass1/待精读/<zotero_key>_<短标题>.md` | ingest 时 | **不再改** |
| 阅读导览（已读） | `<VAULT>/01_Papers/pass1/已精读/<zotero_key>_<短标题>.md` | 移动即可，不新建 | 不再改 |
| 精读笔记 | `<VAULT>/01_Papers/pass2/<zotero_key>_<短标题>.md` | **研究者批注之后** | 研究者继续批注 / 回答时增补 |

- `<VAULT>` 是你复制 `template/` 后得到的工作区根目录，实际值写在 `Config.md`。
- `01_Papers/pass1/` 根目录**只放模板**（`_Reading_Guide_Template.md`）；导览落在根下即违规。
- 文件名创建后**不再改动**：`zotero_key` 保证唯一与稳定，`<短标题>` 可中文。两份文件前缀与短标题**完全一致**，靠文件名配对。
- **位置即状态**：导览待在 `待精读/` = 还没成稿；`pass2/<同名>.md` 一旦存在，该导览就应已在 `已精读/`。导览内**不写状态字段**。

---

## 1. 精读笔记（`pass2/`）Frontmatter

```yaml
---
type: paper
schema_version: 3

title: ""
authors: []
year: 2026
venue: ""
doi: ""
zotero_key: ""
zotero_uri: ""

primary_area: ""       # 你的主领域，例如 "AI"
secondary_areas: []    # 次要 / 交叉领域
research_position: "exploration"  # core | mentor | intersection | exploration

topics: []
reading_status: "reading"  # reading | deep-read | completed | archived
interest_level: 3          # 1-5
research_relevance: 3      # 1-5

wiki_pages: []
related_papers: []
open_questions: []

last_reviewed: 2026-01-01
---
```

| 字段 | 说明 |
|---|---|
| `type` / `schema_version` | 固定为 `paper` / `3`（Dataview 与 lint 依赖） |
| `title` | 论文**原标题**，保留原语言，不翻译 |
| `authors` / `year` / `venue` / `doi` | 取自 Zotero；**缺失就留空并在笔记中如实标注，不要猜** |
| `zotero_key` / `zotero_uri` | Zotero 条目定位；`zotero_key` 同时用作文件名前缀 |
| `primary_area` / `secondary_areas` | 领域标签。默认值在 `Config.md` 里配置；换领域就改 `Config.md`，不要临时发明同义标签 |
| `research_position` | `core`（当前核心）\| `mentor`（团队 / 导师方向，非自身核心）\| `intersection`（两域都实质）\| `exploration`（兴趣高但不在当前计划内）。**判定首要依据是 🟣 紫色批注**，判定是**元数据**，不建分层目录、不复制笔记 |
| `topics` | 主题标签，供 Dataview 聚合与 Wiki 合并检查聚类 |
| `reading_status` | `deep-read`（批注已沉淀，`pass2/` 的主状态）\| `completed`（Wiki 变更已落定）\| `archived`。`reading` 保留但一般不用——**尚无 `pass2/` 时状态由导览所在目录表达** |
| `interest_level` / `research_relevance` | 1–5 整数，是分类规则（core / mentor / intersection / exploration / archive）的输入 |
| `wiki_pages` | 本笔记贡献或关联的 Wiki 页 |
| `related_papers` | 相关 Paper Note |
| `open_questions` | 未决问题（与正文 §10 对应） |
| `last_reviewed` | 最近复核日期 |

> **不要往 frontmatter 加计数类字段**（如 `evidence_count`）——能从正文算出来的数字写进 frontmatter 就是状态双写。

## 2. 精读笔记正文结构（13 节）

| 节 | 内容 | 何时写 |
|---|---|---|
| **§0 阅读轮次** | 两行：导读日期 ｜ 批注数与二次总结日期 | 生成时 |
| §1 研究问题 | 原文证据 + 暂定解读 + 阅读导引 + 提问 + 回应 | 生成时 |
| §2 核心贡献 | 每个贡献一小节 | 生成时 |
| §3 方法 | 架构 / 算法 / 数据 / 评测 | 生成时 |
| §4 关键证据 | `E` 对象汇总表 | 生成时建表，后续追加 |
| §5 主要结果 | 结果 + 位置 + 提问 | 生成时 |
| §6 局限 | 作者自述局限 + Agent 局限 | 生成时 |
| §7 与研究的关系 | 主领域 / 次领域 / 交叉 + 分类判定 | 生成时 |
| **§8 批注沉淀** | **主产物**：§8.1 研究者批注（含研究者评论列）· §8.2 机器词典 · §8.3 Agent 补充 | 生成时 |
| §9 新知识与假设 | 候选 Wiki 主题 | 生成时 |
| §10 未决问题 | 编号列表 | 生成时 + 后续 |
| §11 Wiki 更新提案 | **主张级变更表** + 批准框 | 生成时 + 后续 |
| §12 相关论文 | 引用键或 `[[Paper Note]]` | 生成时 |

**阅读导引（Reading Guide）**：§1–§7 每节顶部一行 `> **阅读导引**：…`，由 Agent 写，说明本节讲什么、该关注什么、哪一处需要研究者判断、哪些是争议点。它是**给研究者的阅读辅助**，不是给 Agent 自己的备注；更细的读前导航留在 `pass1/` 的导览里，此处**不复制**。

## 3. 证据对象（Evidence object）

写在 §4 关键证据表中，是**整个知识库的最小证据单位**。

```yaml
id: E01
claim: ""        # 中文论断
quote: ""        # 原文摘录，保持论文原语言
quote_zh: ""     # 中文翻译（原文非中文时必填）
location: "p. X, Sec. Y"
source_type: "main_text" # main_text | figure | table | appendix | author_quote
source: "pass1"  # pass1 | annotation:黄|绿|蓝|红|紫 | agent
confidence: "high"        # low | medium | high
```

| 字段 | 说明 |
|---|---|
| `id` | `E01, E02, …`，按出现顺序编号，**页内唯一、永不复用** |
| `claim` | 用**中文**写这条论断 |
| `quote` | **原文摘录，保持论文原语言**（英文论文就写英文原句）；只摘支撑论断的短句，不成段复制，全文始终留在 Zotero |
| `quote_zh` | 中文翻译；原文本身就是中文时留空 |
| `location` | 页码 / 章节 / 图 / 表 / 附录，**必须具体**；来自批注时用 Zotero 官方 `annotationPageLabel` |
| `source_type` | `main_text` \| `figure` \| `table` \| `appendix` \| `author_quote` |
| `source` | 这条证据从哪来：`pass1`（Agent 通读原文所得，**非批注**）\| `annotation:黄/绿/蓝/红/紫`（研究者批注带出）\| `agent`（Agent 补充） |
| `confidence` | `low` \| `medium` \| `high` |

**黄与紫不进 `E` 对象**：🟡 黄色是生词（进 `03_Vocabulary/`）；🟣 紫色是研究关系信号（进 §7 与 §11），不是论文证据。

**铁律**：`quote` 只能来自 `annotationText`（论文原文）。`🔤…🔤` 区间内的机器词典文本**永不作 `quote`**。

## 4. 研究者回应对象（Researcher response object）

写在对应小节的 `Researcher Response` 下：

```yaml
id: R01
agent_question: ""      # 中文
researcher_response: "" # 中文
response_type: "interpretation" # interpretation | critique | connection | hypothesis | decision
confidence: "medium"
approved_for_wiki: false
```

- `agent_question` 与 `researcher_response` 都用中文。
- `approved_for_wiki: true` **只由研究者本人给出**，Agent 不得代填。
- **紫色批注不是 `researcher_response`**：它是标记而非回答，只能作为 `R` 对象的**候选**，须研究者确认后才写入。
- 研究者尚未回答的位置一律保留 `PENDING_RESEARCHER_RESPONSE`，**不得编造回答**。

## 5. `pass2/` 的生成与标记

**`pass2/` 在研究者批注之后才生成**，因此它一出生就带着批注。三条标记规则：

| 要标什么 | 怎么标 |
|---|---|
| 某段判断来自研究者批注 | 用 Obsidian 高亮 `==…==` 把该段包住（「这段来自批注」）——首次生成时就要标 |
| 后续轮次补进去的位置（研究者继续批注、或在对话中回答问题） | 该处行末标 `（Pass 2 补充）`（「这一处是后来补的」） |
| 批注太少、Agent 自行补的重点与细节 | 一律写进 **§8.3 Agent 补充**，不得混入研究者信号 |

两种标记可以同时出现。**`==高亮==` 只用于批注带出的内容**，不要拿它做强调装饰——否则「哪些是研究者标的」这个信号就失效了。

**首次生成时的一致性**：`pass2/` 生成后 `reading_status` 置 `deep-read`；`pass1/待精读/<同名>.md` **移动到 `pass1/已精读/`**；`log.md` 追加一行。Wiki 变更获批准并落库后置 `completed`。

## 6. 设计规则（Design rule）

Agent 必须**提问**来获取研究者解读，而不是悄悄写一个叫「我的分析」的小节。

- 需要时给出简明的 **Agent Interpretation (Provisional)**，并显式标注为暂定；
- 提出**针对性**问题（1–3 个，优先问那些会实质改变解读或研究相关性的问题）；
- 研究者的回答存为 **Researcher Response**；
- 仅在**明确批准**后才提升到 Wiki。

Agent 自行补充的内容必须写在 **§8.3 Agent 补充**并标注来源，**不得混入研究者信号**；标 `==高亮==` 的段落同理，只能是批注带出的。

## 7. 语言与引文

- 分析、解读、问题、局限等**说明性文字用中文**。
- **摘录一律保持论文原语言**，并在其下给出中文翻译；短句可用 `（译：…）` 紧凑写法。
- 数字、单位、公式、变量名、模型名、数据集名、指标名**不译**。
- 术语首次出现写「中文（English）」，此后全文保持一致。
- frontmatter 的**键与枚举值保持英文**（Dataview 与 lint 依赖它们）。
- 以上三条是**默认体例**，可在 `Config.md` 中调整（换语言体例前先读该文件）。

## 8. 与 Wiki 的接口（claim impact check）

Paper Note 是**证据层**，Wiki 是**主张层**。两者的接口是 §11 Wiki 更新提案里的**主张级变更表**：

| 动作 | 页面 | Claim ID | 变更 | 依据 |
|---|---|---|---|---|
| 新增主张 / 状态流转 / 新增分歧 / 分歧消解 / 共识达成 / 新建页面 / 升级为 gap | Wiki 页 | `C0x` | 如 `supported → contested` | `E` 编号 |

**每次 ingest 都必须回答一个问题：本次读到的 `E` 证据，是否触及 `02_Wiki/` 中已有的某条主张？** 触及则提状态流转，不触及则只提新增主张或新建页面。**没有对应 `E` 编号支撑的提案不要提。**

- 新建页面的类型**由目录决定**（`topic/` `concept/` `synthesis/` `gap/` `entity/`），frontmatter **不写 `type`**。
- 变更落库时证据列必须写全 `[[Paper Note]]E编号 (页码)` 三件套。
- 变更会改动实质研究论断时，**先请求研究者批准**，再做持久化修改。

完整规则见 `Wiki_Schema.md`。

---

## 9. 阅读导览（`pass1/`）结构

阅读导览是**独立文件**，按 `../01_Papers/pass1/_Reading_Guide_Template.md` 写。**生成后不再改动。**

**两个子目录就是状态**：

| 目录 | 含义 | 判据 |
|---|---|---|
| `01_Papers/pass1/待精读/` | 还没精读 | 尚无 `pass2/<同名>.md` |
| `01_Papers/pass1/已精读/` | 已精读 | 已生成 `pass2/<同名>.md` |

不设状态字段——`reading_status` 只写在 `pass2/` 里，文件夹承担导览侧的状态，两者**不重复表达**。

```yaml
---
type: reading-guide
schema_version: 4

zotero_key: ""
title: ""
created: 2026-01-01
last_reviewed: 2026-01-01
---
```

### 9.1 定位：5 分钟导览，不是逐节导航

**一份导览 = 5 分钟读完的一页**，解决两件事：**读前速览**（值不值得读、重点在哪）与**回看抓要点**（架构 + 核心观点）。**不再逐小节总结**——小节层面的导航由「论文架构地图」一行一章承担。

### 9.2 七段固定结构

| # | 段 | 写什么 | 约束 |
|---|---|---|---|
| 顶部 | 页码基准 + 一句话 | 声明页码指哪个附件；一句话说明这篇在做什么 | 一句话 ≤ 40 字，**不评价** |
| 一 | 要解决的问题 | Problem / Gap / Motivation | ≤ 150 字；**不写它做成了没有** |
| 二 | **论文架构地图** | 表格：`章 \| 页 \| 在做什么 \| ★ \| 建议` | 一行一章；★ 按「与研究者研究相关、可复用」评，**不按作者篇幅权重** |
| 三 | **核心观点** | 作者**明确声称**的贡献与主张，3–5 条 | 每条标章节定位 |
| 四 | 读前必备的概念与记号 | 表格：`概念／记号 \| 一句话` | 3–5 条，只给「是什么」 |
| 五 | 阅读路线 | 表格：`目的 \| 读法 \| 约需` | 按目的给路线；时长按「边读边想」估算 |
| 六 | 带着这几个问题读 | 3–5 问 | 每问附**一行定位**；判断类标「**论文不答**」 |

**答案的写法**：优先让研究者自己从原文找答案，「答案在」只给**一行定位**（在哪、怎么判），**不给完整论证**。判断类问题（没有客观答案的）必须标「**论文不答**」——那只有研究者能回答。

### 9.3 硬约束（违反即违规）

1. **全文 ≈ 1000 字（含表格），5 分钟读完为上限**；**中文字数 1200–1300 是硬上限**，超过必须精简。**宁短不长。**
2. **不逐小节展开**。小节层面的信息只出现在「论文架构地图」的「在做什么」格里。
3. 保留论文原有的**章节编号**（§1 / §2.1 …）以便对照原文，但**不复制论文的标题层级结构**。
4. **不写实验结果、不写数字、不写作者对结果的解释与最终结论**——「核心观点」只记录作者**声称**什么，不记录作者**证明了**什么。
5. **不得出现** `E` 编号、主张、Wiki 提案、`R` 对象、`PENDING_RESEARCHER_RESPONSE`。出现任意一项即违规——它会产生**第二个证据源**。
6. **不设状态字段**——状态由所在文件夹（`待精读` / `已精读`）与 `pass2/` 的 `reading_status` 表达，避免状态双写。
7. 论文没有清晰章节时，按「摘要 / 引言 / 方法 / 实验 / 讨论 / 附录」粗分块，并在架构地图里注明。
8. **生成后不再改动。**

---

## 10. Zotero 读取要点（与 schema 相关）

读取一律通过仓库的 Zotero 访问层：`python tools/zotero/rvzotero.py <子命令>`（子命令与参数见 `tools/zotero/README.md`），或任何**等价的只读 Zotero 读取能力**。以下是与本 schema 直接相关的坑：

1. **批注要显式声明类型**：取子条目时若不带 `itemType=annotation`，Zotero 会**静默返回 0 条批注**（不报错）——最危险的失败模式。用 `rvzotero.py annotations` 子命令可避开。
2. **批注在 100 条处静默截断**，必须分页取全；条数与实际不符时先怀疑截断。
3. **批注可能只挂在某一个附件上**（一篇论文常有原文 / 双语 / 译文多个附件），必须逐个附件取。
4. **页码用 `annotationPageLabel`**（Zotero 官方页码），不要自己从 `annotationPosition.pageIndex` 推。
5. 批注条数、颜色分布、`🔤…🔤` 切分结果在读入后先核对一遍，再写进 §8。
