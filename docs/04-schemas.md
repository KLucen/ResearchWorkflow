# Schema 速查：字段、状态与写权限

> **权威规范在 Vault 内**：`00_System/Paper_Schema.md`、`00_System/Wiki_Schema.md`、`00_System/Vocabulary_Schema.md`。
> 本文是**人读版速查**——把「有哪些字段、谁能写、状态怎么流转」压到一处。与 Vault 内规范冲突时，以 Vault 内的为准。
> 设计理由见 [01-design.md](01-design.md)；流程见 [03-workflow.md](03-workflow.md)。

## 结论先行

只有 **4 类文件**，分属 **3 层**：

| 文件类型 | 位置 | 所属层 | 谁能写 | 权威规范 |
|---|---|---|---|---|
| **5 分钟导览** | `01_Papers/pass1/{待精读,已精读}/` | 阅读辅助（**不是事实源**） | Agent，**生成后冻结** | `00_System/Paper_Schema.md` 下半部分 |
| **Paper Note** | `01_Papers/pass2/` | **证据层** | Agent 写，研究者可覆盖；`R` 对象只有研究者能定 | `00_System/Paper_Schema.md` |
| **Wiki 页** | `02_Wiki/<五类目录>/` | **主张层** | Agent 提案，**研究者批准** | `00_System/Wiki_Schema.md` |
| **Vocabulary 词条** | `03_Vocabulary/` | **语言层** | Agent 追加，`acquired` 只有研究者能改 | `00_System/Vocabulary_Schema.md` |

三层的硬边界：**`pass1/` 不作引用来源；Vocabulary 不进 Wiki、不进 `E` 证据对象。**

两条贯穿所有文件的规则：

1. **frontmatter 的键与枚举值永远用英文**——它是 Dataview 与 lint 的机器可读接口，翻译了就坏。
2. **文件名创建后保持稳定**——改名会打断 `[[链接]]`、`source_papers` 和 pass1/pass2 配对。（在 `待精读/` 与 `已精读/` 之间**移动**不算改名。）

---

# 1. 命名与目录约定

| 类型 | 文件名 | 备注 |
|---|---|---|
| 5 分钟导览 | `01_Papers/pass1/待精读/<zotero_key>_<短标题>.md` | 成稿后移到同级 `已精读/` |
| Paper Note | `01_Papers/pass2/<zotero_key>_<短标题>.md` | 与导览**同名配对**，靠文件名对应 |
| Wiki 页 | `02_Wiki/<目录>/<短标题>.md` | 目录决定类型 |
| Vocabulary | `03_Vocabulary/<lemma>.md` | 小写词元；`unify.md` 收 `unified/unifies/unifying` |

**配对是隐式的**：不引入索引文件、不加关联字段。`pass1/待精读/X.md` 与 `pass2/X.md` 就是同一篇论文的两步产物。

**位置即状态**（导览侧）：`待精读/` = 还没成稿；`已精读/` = 已有 `pass2/<同名>.md`。所以导览**不写状态字段**。

模板文件（`_` 前缀，不参与查询视图）：

```text
01_Papers/pass1/_Reading_Guide_Template.md
01_Papers/pass2/_Paper_Template.md
02_Wiki/_Wiki_Template.md
03_Vocabulary/_Vocabulary_Template.md
```

---

# 2. 5 分钟导览（`pass1/`）

### Frontmatter

| 字段 | 值 | 必填 | 说明 |
|---|---|---|---|
| `type` | `reading-guide` | ✅ | 固定值 |
| `schema_version` | `4` | ✅ | 固定值 |
| `zotero_key` | 字符串 | ✅ | 同时用作文件名前缀 |
| `title` | 论文原标题 | ✅ | **保留原语言，不翻译** |
| `created` | 日期 | ✅ | 生成日期 |
| `last_reviewed` | 日期 | ✅ | 最近复核日期 |

**没有** `reading_status`——状态由所在文件夹表达。

### 正文七段（固定）

| # | 段 | 约束 |
|---|---|---|
| 顶部 | 页码基准 + 一句话 | ≤ 40 字，**不评价** |
| 一 | 要解决的问题 | ≤ 150 字，**不写它做成了没有** |
| 二 | 论文架构地图 | 表格 `章 \| 页 \| 在做什么 \| ★ \| 建议`，一行一章 |
| 三 | 核心观点 | 作者**明确声称**的 3–5 条，每条标章节定位 |
| 四 | 读前必备的概念与记号 | 3–5 条，只给「是什么」 |
| 五 | 阅读路线 | 表格 `目的 \| 读法 \| 约需` |
| 六 | 带着这几个问题读 | 3–5 问，每问附一行定位；判断类标「**论文不答**」 |

### 硬约束（越界即违规）

| 禁止出现 | 原因 |
|---|---|
| `E01` 等证据对象 | 会产生第二个证据源 |
| 主张 / Wiki 提案 | 尚无批注，只会产生单来源噪音页 |
| `R01` 等研究者回应对象 | 还没有人能回应 |
| `PENDING_RESEARCHER_RESPONSE` | 同上 |
| 实验结论、数字、作者对结果的解释 | 导览是"读之前"的辅助 |
| 状态字段 | 位置就是状态 |
| 全文超过 ~1300 中文字 | 5 分钟读不完 |

---

# 3. Paper Note（`pass2/`，证据层）

### Frontmatter

| 字段 | 值 | 必填 | 谁能写 |
|---|---|---|---|
| `type` | `paper` | ✅ | 固定 |
| `schema_version` | `3` | ✅ | 固定 |
| `title` | 论文原标题 | ✅ | Agent（取自 Zotero，**保留原语言**） |
| `authors` | 列表 | | Agent |
| `year` / `venue` / `doi` | | | Agent（**缺失留空并如实标注，不要猜**） |
| `zotero_key` | 字符串 | ✅ | Agent（同时是文件名前缀） |
| `zotero_uri` | 字符串 | | Agent |
| `primary_area` | 字符串 | ✅ | Agent |
| `secondary_areas` | 列表 | | Agent |
| `research_position` | `core \| mentor \| intersection \| exploration` | ✅ | Agent 判定，**研究者可覆盖**；首要依据是 🟣 紫批注 |
| `topics` | 列表 | | Agent（供 Dataview 聚合） |
| `reading_status` | `reading \| deep-read \| completed \| archived` | ✅ | Agent |
| `interest_level` | 1–5 整数 | ✅ | Agent 判定，研究者可覆盖 |
| `research_relevance` | 1–5 整数 | ✅ | Agent 判定，研究者可覆盖 |
| `wiki_pages` | 列表 | | Agent |
| `related_papers` | 列表 | | Agent |
| `open_questions` | 列表 | | Agent（与 §10 对应） |
| `last_reviewed` | 日期 | ✅ | Agent |

### 正文 13 节

| 节 | 内容 | 谁写 |
|---|---|---|
| §0 阅读轮次 | 导读日期｜批注数与二次总结日期 | Agent，生成时 |
| §1 研究问题 | 原文证据 + 暂定解读 + 阅读导引 + 提问 + 回应 | Agent |
| §2 核心贡献 | 每个贡献一节 | Agent |
| §3 方法 | 架构 / 数据 / 评测 | Agent |
| §4 关键证据 | **`E` 对象汇总表**，生成时建表、后续追加 | Agent |
| §5 主要结果 | 结果 + 位置 + 提问 | Agent |
| §6 局限 | 作者自述局限 + Agent 局限 | Agent |
| §7 与研究的关系 | + 分类判定 | Agent（依 🟣 批注） |
| **§8 批注沉淀与二次总结** | **主产物**：按颜色分组的批注 + 二次总结 + Agent 补充 | 见 §3.3 |
| §9 新知识与假设 | 候选 Wiki 主题 | Agent |
| §10 未决问题 | 编号列表 | Agent |
| §11 Wiki 更新提案 | **主张级变更表** + 批准框 | Agent 提案，**研究者批准** |
| §12 相关论文 | 引用键或 `[[Paper Note]]` | Agent |

§1–§7 每节顶部有一行 `> **阅读导引**：…`，由 Agent 写，是**给研究者的**阅读辅助（本节讲什么、该关注什么、哪一处需要你判断），不是 Agent 的自用备注。

### §8 的三个子块（**不要混**）

| 子块 | 内容 | 来源标记 |
|---|---|---|
| §8.1 研究者评论列 | 研究者**本人写的**话（如实记录） | 批注评论中 `🔤…🔤` **区间外**的文字 |
| §8.2 二次总结 | Agent 对批注的沉淀 | 来自批注 |
| §8.3 Agent 补充 | Agent 自行补的重点与细节 | **必须标注**，不得混入研究者信号 |

### 证据对象（`E`）

```yaml
- id: E01                                    # E01, E02, … 按出现顺序，永不复用
  claim: ""                                  # 中文论断
  quote: ""                                  # 原文摘录，保持论文原语言
  quote_zh: ""                               # 中文翻译（原文非中文时必填）
  location: "p. X, Sec. Y"                   # 必须具体；来自批注时用官方页码标签
  source_type: main_text                     # main_text | figure | table | appendix | author_quote
  source: pass1                              # pass1 | annotation:黄|绿|蓝|红|紫 | agent
  confidence: high                           # low | medium | high
```

| 字段 | 关键约束 |
|---|---|
| `id` | 永不复用；删除后编号作废 |
| `quote` | **只能来自论文原文**（`annotationText` 或正文） |
| `quote_zh` | 原文非中文时必填 |
| `location` | 页码 / 章节 / 图 / 表 / 附录必须具体 |
| `source` | `pass1`=Agent 通读所得（**非批注**）；`annotation:<颜色>`=研究者批注带出；`agent`=Agent 补充 |
| `confidence` | 反映这条证据本身的强度 |

**🟡 黄与 🟣 紫不进 `E` 对象**：黄是生词（进 `03_Vocabulary/`）；紫是研究关系信号（进 §7 与 §11），**不是论文证据**。

**`🔤…🔤` 区间内的机器词典文本永不作 `quote`**——它是 `tool_generated`，只能填进 Vocabulary 的「机器词典」行。

### 研究者回应对象（`R`）

```yaml
- id: R01
  agent_question: ""                         # 中文
  researcher_response: ""                    # 中文，只有研究者本人能提供
  response_type: interpretation              # interpretation | critique | connection | hypothesis | decision
  confidence: medium                         # low | medium | high
  approved_for_wiki: false                   # 只有研究者本人能改成 true
```

**Agent 只能写 `agent_question`。** `researcher_response` 与 `approved_for_wiki: true` 是研究者的专属字段——未回答时该位置保留 `PENDING_RESEARCHER_RESPONSE`，**不要代填**。

**🟣 紫色批注不是 `researcher_response`**：它是**标记**不是**回答**，只能作 `R` 的候选，须研究者确认后才写入。

### 两种标记

| 记号 | 含义 | 什么时候加 |
|---|---|---|
| `==高亮==` | **这段来自批注** | 首次生成时就要标；只用于批注带出的内容，**不做强调装饰** |
| 行末 `（Pass 2 补充）` | **这一处是后来补进去的** | 后续轮次（继续批注 / 对话中回答）修订的位置 |

两者可同时出现。

---

# 4. Wiki 页（`02_Wiki/`，主张层）

### 目录即类型（**frontmatter 没有 `type`**）

| 目录 | 回答的问题 | 核心产物 |
|---|---|---|
| `topic/` | 这个方向由哪些问题构成？ | 方向地图（**本身不写主张**） |
| `concept/` | X 是什么？ | working definition |
| `synthesis/` | 关于 X，文献整体说了什么？ | 带边界的当前最佳理解 |
| `gap/` | 什么还不知道、值得做？ | **可研究问题 + 验证路径** |
| `entity/` | 这个具体的人/组/系统/模型/数据集是谁？ | 实体档案 |

拿不准时的判据顺序：`topic` 最粗 → `concept` 有「定义」的对象 → `synthesis` 跨论文主张 → `gap` 可研究问题 → `entity` 专名。

**三条后果**：

1. frontmatter 不写 `type`——移动文件就是改类型，不存在第二份真相；
2. Dataview 用 `file.folder` 判断类型，不是 `type`；
3. `02_Wiki/` 根下**只有** `_WikiIndex.md` 与 `_Wiki_Template.md`；任何内容页落在五个目录之外，lint 报错。

### Frontmatter

| 字段 | 值 | 必填 | 谁能写 |
|---|---|---|---|
| `schema_version` | `4` | ✅ | 固定 |
| `title` | 字符串 | ✅ | Agent |
| `status` | `draft \| active \| retired` | ✅ | Agent 可改 `draft`→`active`；**转 `retired` 需研究者批准** |
| `effective_from` | 日期 | ✅ | Agent（本页结论开始生效） |
| `retired_at` | 日期 / 空 | | Agent 提案，研究者批准 |
| `superseded_by` | 页面名 / 空 | | 仅 `retired` 时填 |
| `domains` | 列表 | | Agent |
| `topics` | 列表（≥1） | ✅ | Agent（**批量合并的聚类键**） |
| `source_papers` | Paper Note 文件名（**不含 `.md`**） | ✅ | Agent |
| `confidence` | `low \| medium \| high` | ✅ | Agent（页面级，反映综合结论可靠程度） |
| `created` / `updated` / `last_reviewed` | 日期 | ✅（`updated`） | Agent |

**刻意没有的字段**：

| 不存在的字段 | 为什么 |
|---|---|
| `type` | 由目录推导 |
| `claim_count` / `contested_count` / `open_questions` 等计数 | 从 §2 表算得出来，写进 frontmatter 就是**状态双写** |

这类验收指标统一放 `_WikiIndex.md` 的验收区，由检查生成。

### 正文六节

| 节 | 写什么 | 特别约束 |
|---|---|---|
| §1 综合与当前理解 | 本页**最接近结论**的东西，3–6 句 | 只写已达 `consensus` 的主张 + 研究者批准过的判断；写清**适用边界**；**全页唯一允许整段重写的地方** |
| **§2 主张登记表** | **唯一事实源** | **行只增、状态只改，行永不删除** |
| §3 共识 | **只写解释，不重复列主张**（用 `C` 编号引用） | 写适用边界、为什么可靠、写进 §1 的哪一句 |
| §4 分歧 | 对立双方编号 + **分歧根源** + 适用条件 + 目前判断 | 证据不足时保留待确认，**不强行裁定** |
| §5 未解决问题 | 问题本身 + **还缺什么证据** | `gap/` 页的例外：本节是页面主体（RQ / 为什么重要 / 需要什么证据 / 可行性） |
| §6 变更记录 | 一行一次变更 | `日期 — 变更类型 — C 编号 — 触发来源` |

### §2 主张登记表（8 列）

```markdown
| ID | 主张 | 证据 | 状态 | 批准 | 生效 | 失效 | 替代 |
|----|------|------|------|------|------|------|------|
| C01 | 示例主张 | +[[PaperA]]E03 (p.5) · −[[PaperC]]E07 (p.9) | contested | — | 2026-09-14 | — | — |
```

| 列 | 含义 | 谁能写 |
|---|---|---|
| `ID` | `C01, C02, …` 页内唯一、**永不复用** | Agent |
| `主张` | 这条论断是什么 | Agent 提案，研究者批准 |
| `证据` | 从哪条证据而来 | Agent |
| `状态` | 证据强度档位（见状态机） | Agent 提案，研究者批准 |
| `批准` | **谁在什么时候批准**（`研究者 · YYYY-MM-DD`；`—` = 未经批准） | **只有研究者** |
| `生效` / `失效` | 起止日期；**失效非空即已下线，检索期默认过滤** | Agent |
| `替代` | 被哪条主张取代（`→ C07`） | Agent |

**证据列语法**（检索命中依据的关键）：

```text
+ [[Paper Note 文件名]] E编号 (页码)      ← 支持
− [[Paper Note 文件名]] E编号 (页码)      ← 反对
~ [[Paper Note 文件名]] E编号 (页码)      ← 限定（仅部分成立 / 仅特定设定下成立）
```

三件套**缺一不可**：`[[…]]` 可点击（跳回 `pass2/` 笔记）、`E编号` 指到 §4 的具体证据行、`(页码)` 免去翻找。

**没有回链的主张视为无依据，lint 报警。**

### 状态机

```text
proposed ──(第 2 篇独立论文给出 + 证据)──► supported
                                             │
                              (研究者批准) ──┴──► consensus
                                             │
                    (出现 − 证据，强度相当或更强) ──► contested
                                             │        │
                    (− 被限定解释为 ~，或研究者裁定) ──┘ ──► consensus
                                             
任意状态 ──(被明确推翻)──► refuted
```

| 流转 | 条件 |
|---|---|
| `proposed → supported` | 第 2 篇**独立**论文给出 `+` 证据 |
| `supported → consensus` | 研究者明确批准（Paper Note 中 `approved_for_wiki: true` 的 `R` 对象） |
| `supported` / `consensus → contested` | 出现 `−` 证据，强度相当或更强 |
| `contested → consensus` | `−` 证据被限定解释（转为 `~`），或研究者裁定 |
| 任意 → `refuted` | 被明确推翻 |

- **独立性的定义**：不同研究组、或在不同数据集上的独立验证。**同一篇论文的多个实验不算独立。**
- **状态不能跳级。**
- **状态 ≠ 是否现行**：状态说**证据强度**，`失效` 说**是否仍是当前答案**。一条 `supported` 的主张完全可以因被更精确的主张取代而失效——此时填 `失效` + `替代`，**状态保持不变**。

### `_WikiIndex.md`

**投影，不是事实源**——与页面正文冲突时以页面正文为准。四个区：§1 主题清单（Dataview 自动）、§2 最近变更（Dataview 自动）、§3 开放问题（Agent 增量重建）、§4 验收指标（Agent 每次检查后重建）。

---

# 5. Vocabulary 词条（`03_Vocabulary/`，语言层）

### Frontmatter

| 字段 | 值 | 必填 | 谁能写 |
|---|---|---|---|
| `type` | `vocabulary` | ✅ | 固定 |
| `lemma` | 小写词元，**与文件名一致** | ✅ | Agent（词形归一） |
| `surface_forms` | 列表（**追加式**） | ✅ | Agent |
| `dictionary` | **这个词本身的意思**（稳定） | ✅ | Agent |
| `encounters` | 语境记录条数 | ✅ | Agent（与记录条数一致） |
| `acquired` | 布尔 | ✅ | **Agent 只能建议；`true` 只有研究者能定** |
| `first_seen` / `last_seen` | 日期 | ✅ | Agent |

> **Vocabulary **有意不设** `schema_version`**（也没有 `status` / `effective_from` / `retired_at` 这类生命周期字段）。它是语言层——词条结构极简且只追加，版本号没有承载任何东西。另外三层各自带版本号：**5 分钟导览 `4` / Paper Note `3` / Wiki 页 `4`**，这三个数字是 Dataview 查询与 lint 的接口，不要随手改。

### 正文两节（**只追加，不改旧**）

```markdown
# unify

## 词典义
v. 统一；使成一体；使一元化

## 语境记录

### 2026-09-14 · [[<zotero_key>_<短标题>]] p.2
- 原文（EN）："unified"
- 本语境义：把碎片化的研究收敛到同一框架下（不是"合并"，是"统一坐标系"）
- 机器词典：🔤v. "unify"的过去式和过去分词；统一的；一元化的；同一标准的🔤
- 备注：
```

**两个「意思」必须分开写**，这是本库的核心价值：

| 位置 | 是什么 | 稳定吗 |
|---|---|---|
| `dictionary` / `## 词典义` | **这个词本身的意思** | 稳定、可复用 |
| 每节的 `本语境义` | **它在这句话里的意思** | 随语境漂移；同一个词在不同论文里常常不同 |

**语言层隔离**：本库内容**不得**出现在 Wiki 页、`E` 证据对象或主张登记表中。

---

# 6. 写权限矩阵

**这是本文最该记住的一张表。**

| 内容 | Agent | 研究者 | 说明 |
|---|---|---|---|
| 导览全部内容 | ✅ 写 | — | 生成后冻结，不再改 |
| Paper Note frontmatter | ✅ 写 | 可覆盖 | `research_position` / `interest_level` / `research_relevance` 按批注判定 |
| Paper Note §1–§7、§9、§10、§12 | ✅ 写 | 可覆盖 | |
| §8.1 研究者评论列 | ✅ **如实记录** | ✅ 说 | Agent 不得改写、不得润色、不得丢弃 |
| §8.3 Agent 补充 | ✅ 写 | — | **必须标注来源**，不得混入研究者信号 |
| `E` 对象 | ✅ 写 | 可修正 | `quote` 只能来自论文原文 |
| `R` 对象的 `agent_question` | ✅ 写 | — | |
| `R` 对象的 `researcher_response` | ❌ **禁止** | ✅ | 未回答留 `PENDING_RESEARCHER_RESPONSE` |
| `R` 对象的 `approved_for_wiki: true` | ❌ **禁止** | ✅ | 只有研究者本人 |
| §11 主张级变更表 | ✅ 提案 | ✅ 批准 | 无 `E` 编号支撑的提案不要提 |
| Wiki `§批准` 列 | ❌ **禁止** | ✅ | 写 `研究者 · YYYY-MM-DD` |
| Wiki `§2` 表**删行** | ❌ **禁止** | ❌ | 行永不删除，只流转状态 |
| Wiki `status → active` | ✅ | 可覆盖 | |
| Wiki `retired_at` / `superseded_by` | ⚠️ 提案 | ✅ 批准 | `draft`→`retired` 需批准 |
| Wiki §6 变更记录 | ✅ 追加 | — | 每次改动记一行 |
| Vocabulary `acquired: true` | ⚠️ **建议** | ✅ 定 | Agent 不得自标 |
| 归档（`reading_status: archived`） | ⚠️ 建议 | ✅ 定 | **绝不删除 Zotero 条目** |
| 提升 `research_position` | ⚠️ 建议 | ✅ 定 | Agent 应建议，**不得悄悄提升** |
| 合并检查（每第 5 篇） | ⚠️ **建议** | ✅ 定 | 只建议，不自行执行 |
| 写回 Zotero（任何内容） | ❌ **禁止**（除非明确同意） | ✅ | Zotero 是不可变源 |
| 删除 / 大规模移动 Vault 文件 | ❌ 需同意 | ✅ | |
| 覆盖研究者已写的段落 | ❌ 需同意 | ✅ | |

## Agent 的六条绝对禁区

1. **不代研究者作答**——`researcher_response` 永远不由 Agent 填。
2. **不给 `approved_for_wiki` 盖章**。
3. **不删 `§2` 表的行**——推翻是知识进化，标 `refuted` 保留。
4. **不把研究者判断提升为 Wiki 持久论断**（未经批准）。
5. **不自行创建 `gap/` 页、不自行执行合并检查、不自行标记 `acquired`**。
6. **不把 `🔤…🔤` 机器词典写成 `quote`**，也不因为它而丢掉研究者的话。

---

# 7. 生命周期状态速查

| 字段 | 取值 | 含义 | 变更者 |
|---|---|---|---|
| `reading_status`（Paper Note） | `reading` | 保留值，一般不用 | Agent |
| | `deep-read` | 已读并完成批注沉淀（`pass2/` 生成后的主状态） | Agent |
| | `completed` | Wiki 变更已落定 | Agent |
| | `archived` | 已归档（Zotero 条目**不删**） | 研究者决定 |
| 导览位置 | `pass1/待精读/` | 还没成稿 | Agent |
| | `pass1/已精读/` | 已有 `pass2/<同名>.md` | Agent |
| `status`（Wiki） | `draft` | 新建待复核 | Agent |
| | `active` | 现行 | Agent |
| | `retired` | 已下线，保留供回溯 | 研究者批准 |
| `acquired`（Vocabulary） | `false` | 仍在学 | Agent |
| | `true` | 已掌握 → ingest 跳过，**文件保留** | 研究者 |

**迁移循环**：`pass1/待精读/` →（批注 + 成稿）→ `pass2/` 生成 + 导读移入 `pass1/已精读/` + `reading_status: deep-read` →（Wiki 变更落定）→ `reading_status: completed`。

---

# 8. lint 会查的字段级约束

| 检查 | 具体判据 |
|---|---|
| **必填缺失** | 各类型的必填字段是否齐全 |
| **YAML 非法** | frontmatter 能否解析 |
| **枚举越界** | 值是否在允许集合内 |
| **键名翻译** | frontmatter 键/枚举是否被写成了中文 |
| **文件名与字段一致** | 导览/Paper Note 的 `<zotero_key>` 前缀、Vocabulary 的 `lemma` 与文件名 |
| **计数一致** | Vocabulary `encounters` 与 `## 语境记录` 条数 |
| **导览位置与 `pass2/` 一致** | `待精读/` ⇒ 无 `pass2/<同名>.md`；有 ⇒ 导读应在 `已精读/` |
| **`pass1/` 双写** | 出现 `E` 编号 / 主张 / Wiki 提案 / `R` 对象 / `PENDING_...` 即违规 |
| **导览体量** | 超过约 1300 中文字需精简 |
| **Wiki 目录即类型** | 内容页必须在五个目录之一；frontmatter 不得出现 `type` |
| **证据回链三件套** | 每条证据必须是 `[[Paper Note]]E编号 (页码)` |
| **`E` 编号悬空** | `E` 在证据列出现但 Paper Note 中不存在 |
| **页尾追加痕迹** | 违反最小 diff：新内容堆在页尾 |
| **主张一致性** | 标 `consensus` 却只有 1 篇来源；标 `contested` 却无 `−` 证据；同一主张多页重复登记 |
| **`acquired` 滥用** | 是否被 Agent 自行标记 |

lint 产物**只有一个输出位置**：`00_System/lint-report.md`（覆盖写）。完整流程见 [03-workflow.md](03-workflow.md)。

---

## 权威规范在哪

| 想知道 | 读 |
|---|---|
| Paper Note 与导览的完整规范 | `00_System/Paper_Schema.md` |
| Wiki 五类页面、六节、状态机、检索链、更新纪律 | `00_System/Wiki_Schema.md` |
| Vocabulary 词条规范 | `00_System/Vocabulary_Schema.md` |
| 阶段流程与产出物 | `00_System/Workflow.md` |
| 纪律（必须 / 禁止） | `00_System/AGENTS.md` |
| 路径、映射、体例参数 | `00_System/Config.md` |
| 仪表盘查询 | `00_System/Dataview_Dashboard.md` |

模板都在 `template/` 下——复制到你的 Vault 后，路径就是 `00_System/...`、`01_Papers/...`。

## 相关文档

| 文档 | 内容 |
|---|---|
| [01-design.md](01-design.md) | 为什么这样设计 |
| [02-quickstart.md](02-quickstart.md) | 15 分钟跑通 |
| [03-workflow.md](03-workflow.md) | ingest / query / lint 全流程 |
| [05-zotero-access.md](05-zotero-access.md) | Zotero 访问层 |
| [06-agent-integration.md](06-agent-integration.md) | 接入任意 Agent |
| [07-faq.md](07-faq.md) | 常见问题 |
