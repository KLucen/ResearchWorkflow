# 自动分类与归档规则

> 本文件规定 Agent 在**不打扰研究者**的前提下可以做什么分类判断、什么时候只能**建议**、什么时候**必须请示**。
> 判定所依据的坐标系在 `Research_Profile.md`；入库分流的集合映射在 `Config.md` §6。
> **两条总则**：① Agent 应当**建议**，不得悄悄提升。② 研究者的明确决定**始终优先**于自动分类。

## 1. 分类（Classification）

四类 `research_position` 是**元数据**，不是目录分层——一篇论文只存一份 Paper Note，用 frontmatter 字段分类（见 `AGENTS.md`）。

### Core（核心）

用 `research_position: core` 当且仅当：

- `research_relevance >= 4`，且
- 论文与 `Research_Profile.md` §2 **核心兴趣**实质相关（不是"沾边"）。

### Mentor（导师 / 相邻方向）

用 `research_position: mentor` 当且仅当：

- 论文与 `Research_Profile.md` §3 **导师 / 相邻领域**或 §4 相邻主题实质相关，
- **但它并非当前核心方向的主要部分**。

### Intersection（交叉）

用 `research_position: intersection` 当且仅当：

- 主领域与相邻领域**两者都实质**（只占一边的归 core 或 mentor），
- 且论文对交叉方向有潜在价值。

### Exploration（探索）

用 `research_position: exploration` 当且仅当：

- `interest_level >= 4` 且 `research_relevance <= 3`，**或**
- 主题明确在当前研究计划之外，但研究者有意持续跟进。

### 判定顺序

`core` → `intersection` → `mentor` → `exploration`，**取第一个成立的**。
**冲突时以 🟣 紫色批注为准**（紫色是研究者亲手标的、唯一 Agent 推不出的信号）；若紫色与集合默认映射冲突，**提请研究者裁定并记录在 `pass2/` §7**，不要自行择一。

## 2. 自动提升建议（Automatic promotion suggestions）

出现下列情况时，Agent **可以提出**提升建议（写入 `pass2/` 或对话中，不直接改）：

- 一篇 `exploration` 论文精读后 `research_relevance` 升到 `>= 4`；
- 多篇 `exploration` 论文汇聚到同一主题；
- 某主题开始出现在研究问题或研究项目中。

**边界**：Agent 应当**建议**，**不得悄悄提升**。建议里要写清**依据**（哪几篇、哪条证据、触及 `Research_Profile.md` 的哪一条）。

## 3. 自动归档建议（Automatic archiving suggestions）

出现下列情况时建议 `reading_status: archived`：

- `interest_level <= 2` 且 `research_relevance <= 2`；
- 论文已被取代，且**没有独特证据**（若它提供了别处没有的证据，就不该归档）；
- 或研究者明确表示不值得继续关注。

**归档 = 保留但降级**：`archived` 只影响检索排序与注意力分配。

**铁律：归档时绝不删除 Zotero 条目**，也不删除已写的 Paper Note；Wiki 里由它支撑的主张行照旧保留（这正是"能遗忘但不抹除"的要求）。

## 4. 人工覆盖（Manual override）

研究者的明确决定**始终优先**于自动分类。

被覆盖时：把结论写进 Paper Note 的 frontmatter 与 `pass2/` §7（分类判定表），并在 `log.md` 记一行；**不要**在后续 lint 中把研究者的决定"自动纠正"回默认映射——那是把 Agent 的判断凌驾于研究者之上。

## 5. 与其它纪律的关系

| 事 | 去哪 |
|---|---|
| 集合默认映射（入库分流） | `Config.md` §6（**示例表，按自己结构改**） |
| 四类标签的完整定义与 lint 判据 | `AGENTS.md`「自动分类规则」 |
| Vocabulary 的 `acquired` | **只能研究者标记**，不在自动分类范围内 |
| 删除 Zotero 条目 | **永不自动**；需研究者明确同意（`Config.md` §8） |
