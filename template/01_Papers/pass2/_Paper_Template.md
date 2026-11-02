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

primary_area: ""       # 你的主领域（在 00_System/Config.md 里配置），例如 "NLP"
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

# {{title}}（中文译名）

> 体例：说明性文字用中文；**论文原文摘录保持原语言，并在其后附中文翻译**（原文本身是中文则译文留空）。
> **本文件是 `pass2/` 的产物**（精读笔记，**证据层**）。导读在 `pass1/已精读/<同名>.md`——**两份文件按文件名配对，互不复制内容**：导读不进总结，证据不进导读。
> 三层证据不得混淆：**Paper evidence**（原文 + 精确位置）/ **Agent Interpretation (Provisional)** / **Researcher Response**。未回答的位置一律保留 `PENDING_RESEARCHER_RESPONSE`，**Agent 永远不得代答**。
> **两种标记**：`==高亮==` = 「这段来自研究者批注」；行末 `（Pass 2 补充）` = 「这一处是后来补进去的」。
> 结构定义与字段含义见 `00_System/Paper_Schema.md`；本模板只给骨架，不含任何真实笔记内容。

<!--
怎么用这份模板（生成 `pass2/` 之前先读一遍）：

1. 时机：**研究者读完原文、在 Zotero 里做完五色批注之后**才生成 `pass2/`。
   缺批注就生成，会产出一个未经确认、却长得像结论的证据源。
2. 顺序：先读批注（按五色分流）→ 再重读原文 → 填 §8.1（原始批注）→ 填 §4（E 对象）
   → 再写 §1–§7（**受批注影响的段落用 ==高亮== 包住**）→ 最后填 §9–§12。
3. 文件名：`<zotero_key>_<短标题>.md`，与 `pass1/` 下的导读**逐字同名**。
4. 本文件里所有 `{{…}}`、`PENDING_RESEARCHER_RESPONSE`、示例行都是占位符：填完必须全部替换或删除。
   交付前搜一遍 `PENDING_RESEARCHER_RESPONSE`——**留下的每一处都应该是真的还没得到回答**。
5. 摆位：填完把导读从 `pass1/待精读/` 移到 `pass1/已精读/`；Wiki 变更批准落库后 `reading_status` 置 `completed`。
-->

## 0. Reading Pass Log / 阅读轮次

> **导读**：[[pass1/已精读/<同名>]]（YYYY-MM-DD） ｜ **批注**：__ 条（YYYY-MM-DD） ｜ **二次总结**：YYYY-MM-DD
> 编号范围：E01–E__、R01–R__；其他需要留痕的轮次（如研究者后续裁定）追加在此行下方。

---

## 1. Research Problem / 研究问题

> **阅读导引**：（本节讲什么、该关注什么、哪一处需要你判断、哪些是争议点——**给研究者的阅读辅助，不是给 Agent 自己的备注**；更细的读前导航留在 `pass1/`，此处不复制。）

### Paper evidence

> 原文（EN）：""
> 译文（ZH）：""

**Location:** （页 / 节 / 图 / 表 / 附录——**必须具体**）

### Agent Interpretation (Provisional)

PENDING_RESEARCHER_RESPONSE

### Agent Question

> 作者真正想解决的问题是什么（超出其表面动机的那部分）？（直接问研究者）

### Researcher Response

PENDING_RESEARCHER_RESPONSE

---

## 2. Core Contributions / 核心贡献

> **阅读导引**：

### Contribution 1

**Paper evidence**

> 原文（EN）：""
> 译文（ZH）：""

**Location:** 

**Agent Interpretation (Provisional)**

PENDING_RESEARCHER_RESPONSE

**Agent Question**

> 这一贡献相比前人工作，你认为真正新颖或有用的地方在哪里？

**Researcher Response**

PENDING_RESEARCHER_RESPONSE

### Contribution 2

**Paper evidence**

> 原文（EN）：""
> 译文（ZH）：""

**Location:** 

**Agent Interpretation (Provisional)**

PENDING_RESEARCHER_RESPONSE

**Agent Question**

> 第二个贡献对你的研究是否重要？为什么？

**Researcher Response**

PENDING_RESEARCHER_RESPONSE

---

## 3. Method / 方法

> **阅读导引**：

### Architecture / Algorithm

### Data / Experimental Setup

### Evaluation

**Paper evidence**

> 原文（EN）：""
> 译文（ZH）：""

**Location:** 

**Agent Question**

> 哪个方法学选择对该论文的结果最关键？你的依据是什么？

**Researcher Response**

PENDING_RESEARCHER_RESPONSE

---

## 4. Key Evidence / 关键证据

> **阅读导引**：

| ID | Claim（中文论断） | 原文摘录（保持原语言） | 中文翻译 | Location | Source type | Source | Confidence |
|---|---|---|---|---|---|---|---|
| E01 |  |  |  |  | main_text | pass1 | high |

> `Source`：`pass1`（Agent 首轮通读所得，**非批注**）· `annotation:绿/蓝/红`（研究者批注带出）· `agent`（Pass 2 Agent 补充）。
> `Source type`：`main_text` \| `figure` \| `table` \| `appendix` \| `author_quote`。
> **🟡 黄色（生词）与 🟣 紫色（研究关系信号）不进本表**——黄进 `03_Vocabulary/`，紫进 §7 与 §11。
> **铁律**：`quote` 只能来自论文原文（`annotationText`）。批注评论里 `🔤…🔤` 区间内的机器词典文本**永不作 `quote`**（它是释义，不是原文）。
> `E` 编号页内唯一、**永不复用**；表只增行，不删行。

---

## 5. Main Results / 主要结果

> **阅读导引**：

### Result 1

> 原文（EN）：""
> 译文（ZH）：""

**Location:** 

**Agent Question**

> 这个结果应该如何改变你当前的理解——或者并不改变？

**Researcher Response**

PENDING_RESEARCHER_RESPONSE

> 数字、单位、公式、指标名（F1 / BLEU…）**不译**，照原样保留。

---

## 6. Limitations / 局限

> **阅读导引**：

### Authors' stated limitations

> 原文（EN）：""
> 译文（ZH）：""

**Location:** 

### Agent Interpretation (Provisional)

PENDING_RESEARCHER_RESPONSE

### Agent Question

> 从你的角度看，哪一条局限最严重？为什么？

### Researcher Response

PENDING_RESEARCHER_RESPONSE

> **写本节前单独扫一遍无编号的尾部小节**：`Limitations` / `Ethics Statement` / `Broader Impact` / `Reproducibility` 之类常常没有编号标题，**编号标题扫描抓不到它们**。漏扫会得出「本文没有 Limitations」这种错误结论——那是最容易发生的硬错误。

---

## 7. Research Connection / 与研究的关系

> **阅读导引**：

### Connection to {{primary_area}}

### Connection to {{secondary_area}}

### {{primary_area}} × {{secondary_area}}

**Agent Question**

> 这篇论文在你的研究地图上属于哪一类：core / mentor / intersection / exploration？理由是什么？

### Researcher Response

PENDING_RESEARCHER_RESPONSE

> `research_position` 的**判定首要依据是 🟣 紫色批注**（Agent 无法从正文推断），但它只是**标记**、不是回答：只能作为候选，**不得自动写成 Researcher Response**。
> 判定结果是**元数据**，不为它建目录、不复制笔记。

---

## 8. Annotation Synthesis / 批注沉淀

> **Pass 2 的主产物**：先读批注，再重读原文，把研究者的标注沉淀成证据与判断。
> **🟡 黄色（生词）不写在这里**——它进 `03_Vocabulary/`。
> 本节的 §8.1 / §8.2 / §8.3 是三个固定子块，**顺序与标题不要改**。

**二次总结（Pass 2 Synthesis）**：（相对导读那一轮：哪些判断改变了、哪些加深了、哪些被推翻了。分歧要写清根源：**设定 / 数据 / 定义 / 评测**不同——「结论不同」本身不是解释。）

### 8.1 研究者批注（按颜色）

**🟢 绿 — 定义术语 / 术语解释内容**

| 页 | 原文（保持原语言） | 中文翻译 | 研究者评论 |
|---|---|---|---|
|  |  |  |  |

**🔵 蓝 — 影响、观点、解决方法**

| 页 | 原文 | 中文翻译 | 研究者评论 |
|---|---|---|---|
|  |  |  |  |

**🔴 红 — 缺陷、现有问题、现有挑战**

| 页 | 原文 | 中文翻译 | 研究者评论 |
|---|---|---|---|
|  |  |  |  |

**🟣 紫 — 与我的研究相关（可迁移 / 可借鉴）**

| 页 | 原文 | 中文翻译 | 研究者评论 |
|---|---|---|---|
|  |  |  |  |

> **页码一律用 Zotero 官方的 `annotationPageLabel`**，不要自己按 PDF 顺序推。
> **评论归属按 `🔤…🔤` 区间切分**（**不是**「整条评论含不含 `🔤`」）：区间**内**的文字是翻译插件写入的机器词典，**不是研究者的话**，留在 Vocabulary 的「机器词典」行即可（本页 §8.2 只留索引）；区间**外**的非空文字才是**研究者本人写的**，如实抄进上表的「研究者评论」列（升格为 `R` 对象仍需研究者确认）。**不得因为整条评论含 `🔤` 就把研究者的话一并丢掉。**
> **🔴「红」与 🔵「蓝」的边界**：🔵 是「作者提出 / 主张了什么」（含解决方法），🔴 是「哪里有问题、还缺什么」——后者不限于本文自身的局限，也包括领域层面的现有问题与挑战，因此它是 `gap/` 页的**主要来源**。

**两类批注不进 §8.1 的四张表**（否则表会被噪音灌满）：

| 情形 | 去向 |
|---|---|
| 纯结构锚点（只标了 `3.1.2 Misinformation Analysis.` 这类章节标题，无可摘论断） | 折进下面的「已批注章节」表 |
| 🟡 生词类**短语 / 搭配**（`in the wild` 之类） | 收进下面的「短语与搭配」小节——Vocabulary 只收**单词**，短语没有 `lemma` |

**已批注章节**

| 页 | 章节 | 说明 |
|---|---|---|
|  |  |  |

**短语与搭配（不含单词，单词进 `03_Vocabulary/`）**

| 短语 | 本语境义 |
|---|---|
|  |  |

### 8.2 机器词典（`tool_generated`）

> 来源：批注评论中 `🔤…🔤` **区间内**的文本。性质：**`tool_generated`**——既不是论文原文，也不是研究者的判断。
> **两条禁令**：① 永不作 `quote`；② 永不作为研究者的话写入「研究者评论」列。
> 持久位置是 `03_Vocabulary/<lemma>.md` 的「机器词典」行；本小节只保留**索引**，避免同一段文本在两处各自演化。

| 页 | 词 / 术语 | 机器词典文本（`tool_generated`） | 去向 |
|---|---|---|---|
|  |  |  | [[../../03_Vocabulary/<lemma>]] |

### 8.3 Agent 补充（批注不足处）

（研究者批注较少时，Agent 在此补该论文的重点与细节。**本子块内容一律视为 Agent 产出，不得混入研究者信号、不得当作研究者判断**；引用原文时同样要给位置。）

---

## 9. New Knowledge / Hypotheses / 新知识与假设

### Candidate Wiki Topics

- 

### Agent Questions

> 这篇论文里有什么想法值得脱离论文本身保留下来？

> 它是否改变了你此前持有的某个信念或假设？

### Researcher Responses

PENDING_RESEARCHER_RESPONSE

---

## 10. Open Questions / 未决问题

1. 
2. 
3. 

> 编号列表；与被移入 frontmatter `open_questions` 的条目保持一致。反复出现在多个页面里的问题，是升级为 `gap/` 页的候选（见 `Wiki_Schema.md` 的升级条件）。

---

## 11. Wiki Update Proposal / Wiki 更新提案

### 主张级变更（Claim-level changes）

<!-- 下面 4 行是示例行，教你格式；填完必须删除或替换成真实变更。 -->

| 动作 | 页面 | Claim ID | 变更 | 依据 |
|---|---|---|---|---|
| 新增主张 | [[页面名]] | C03 | — → proposed | E12 |
| 状态流转 | [[页面名]] | C01 | supported → contested | E13（−） |
| 新建页面 | — | — | 放入 `synthesis/`（**目录即类型**） | E03, E07 |
| 升级为 gap | [[页面名]] | — | §10 问题 2 → `gap/` 页 | 已在 2 个页面重复出现 |

> 动作枚举：**新增主张 / 状态流转 / 新增分歧 / 分歧消解 / 共识达成 / 新建页面 / 升级为 gap**——不要自己发明动作。
> **新建页面的类型由目录决定**（`topic/` `concept/` `synthesis/` `gap/` `entity/`），frontmatter **不写 `type`**。
> 每条都必须能追溯到上面的 `E` 编号；**没有对应证据的提案不要提**。
> 变更落库时证据列必须写全 `[[Paper Note]]E编号 (页码)` 三件套，并走「最小 diff」流程（见 `Wiki_Schema.md`）。
> **每次 ingest 都必须回答：本次读到的 `E` 证据，是否触及 `02_Wiki/` 中已有的某条主张？** 触及则提状态流转，不触及则只提新增主张或新建页面。

### Researcher approval

- [ ] Approved
- [ ] Rejected
- [ ] 需要修改（Needs revision）

> 勾选**只能由研究者本人**做出。批准前不要做任何持久化的 Wiki 修改。

---

## 12. Related Papers / 相关论文

- [[<zotero_key>_<短标题>]] — 一句话说明相关性

<!--
交付前自检（逐条打勾，任何一条不过就不要交付）：

- [ ] frontmatter 的 `type` / `schema_version` 未被改动；枚举值保持英文；没有加计数类字段（如 `evidence_count`）。
- [ ] 文件名与 `pass1/` 下的导读**逐字同名**；导读已移入 `pass1/已精读/`。
- [ ] §1–§7 中**由批注带出的段落**都用 `==…==` 包住；后续补进去的位置行末有 `（Pass 2 补充）`。
- [ ] §4 的每个 `E` 编号唯一、不复用；每条都有 `Location`；`quote` 是原文、不是机器词典。
- [ ] `==高亮==` 没有被当成强调装饰使用（它只表示「来自批注」）。
- [ ] 所有 `PENDING_RESEARCHER_RESPONSE` 都是真的尚未回答；没有任何 Agent 代答的痕迹。
- [ ] §8.3 的内容没有被写成研究者的判断；§11 的每条提案都有 `E` 编号支撑。
- [ ] 没有把 PDF 复制进 Vault；全文仍只存在于 Zotero。
-->
