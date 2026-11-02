---
schema_version: 4

title: "WikiIndex — Wiki 入口页"
status: active
effective_from: 2026-01-01
retired_at:
superseded_by:

updated: 2026-01-01
---

# WikiIndex

> **需要 Obsidian 的 Dataview 插件**（必需）：§1 与 §2 是 Dataview 查询块，没装插件时它们只是普通代码块，本页等于空壳。
> **本页是投影，不是事实源**——与页面正文冲突时，一律以页面正文为准。
> §1 与 §2 由 Dataview **自动生成**；§3 与 §4 由 Agent 在每次 Wiki 变更 / 定期检查后**增量重建**（只重建受影响的行，不整页重写）。
> **检索链**：本页 → 主题 / 页面 → 该页 §2 主张行 → 证据列的 `[[Paper Note]]E编号 (p.X)` → `pass2/` 精读笔记。全程**两次点击**到论文原文位置。
> **本页没有 frontmatter `type`**——`02_Wiki/` 下任何文件都不写 `type`，类型由目录表达（见下方五类导航）。

**五类目录导航**（内容页必须落在其中之一，放根下即违规）：

| 目录 | 回答什么问题 | 典型内容 |
|---|---|---|
| `topic/` | 这个主题的地图长什么样 | 主题范围、子问题切分、主要路线 |
| `concept/` | X 是什么 | 定义、术语辨析、边界 |
| `synthesis/` | 文献整体说了什么 | 跨论文综合、共识与分歧总览 |
| `gap/` | 什么还不知道 | 研究空白、需要什么证据、可行性 |
| `entity/` | 某个专名实体是什么 | 人 / 组 / 系统 / 模型 / 数据集 |

> ⚠️ 检索时注意：`retired_at` 非空的页面与主张行**默认不参与检索**，被问起时标注「此条已废止」。

## 1. 主题清单（按 `topics` 分组）

```dataview
TABLE WITHOUT ID key AS "主题", rows.file.link AS "页面", rows.file.folder AS "类型"
FROM "02_Wiki"
WHERE !startswith(file.name, "_")
FLATTEN topics
GROUP BY topics
SORT key ASC
```

> `类型` 列显示 `02_Wiki` 本身即表示该页**错放在根目录**（根下只应有 `_WikiIndex.md` 与 `_Wiki_Template.md`，两者已被 `_` 前缀排除）。
> 没有 `topics` 的页面不会出现在本区——`topics` 是批量合并检查的聚类键，缺了就无法归并。

## 2. 最近变更

```dataview
TABLE file.folder AS "类型", status AS "状态", confidence AS "置信度", updated AS "更新"
FROM "02_Wiki"
WHERE !startswith(file.name, "_")
SORT updated DESC
LIMIT 15
```

## 3. 开放问题

> 来源：各页 §5 与各 `gap/` 页的 RQ。**只列当前未解决的**；已升级为 `gap/` 页的只保留指针，不重复其内容。
> 本区**不增量重建就不会更新**——它是 lint 会查的一致性项。

### 3.1 已升级为独立 gap 页（保留指针，原问题不删）

| 原问题 | 出处 | 升级到 |
|---|---|---|
| （问题文本） | （页面）§5-1 | （`gap/` 页） |

### 3.2 仍在页内、未升级

| 问题 | 出处 | 升级判据状态 |
|---|---|---|
| （问题文本） | （页面）§5-1 | 否（仅 1 页出现） |

> 升级为 `gap/` 页的条件见 `../00_System/Wiki_Schema.md`；满足条件也要**先经研究者批准**。

### 3.3 主张层面的未决（卡在证据不足）

| 主张 | 卡在哪 |
|---|---|
| （页面）`C0x` | 需第 2 篇**独立**论文给出 `+` 证据，方可 `proposed → supported`（不得跳级） |

> **同一篇论文的多个实验不算独立来源**；综述的转述与被转述论文也不是独立来源。

## 4. 验收指标

> 由 Agent 在每次检查后重建。**没有指标就无法发现退化**——这是本区存在的唯一理由。
> 指标只写在这里，**不写进各页 frontmatter**（那会造成状态双写）。

| 指标 | 当前值 | 判读 |
|---|---|---|
| 页面总数 | —（topic — · concept — · synthesis — · gap — · entity —） | 某类长期为 0 说明该层还没建立 |
| 主张总数 | — | |
| 状态分布 | `proposed` — · `supported` — · `consensus` — · `contested` — · `refuted` — | **`consensus` 为 0 = 没有任何结论走完状态机** |
| 已批准主张 | — | 批准记录写在 §2 的 `批准` 列 |
| 悬空证据引用 | — | 每次检查必查：`E` 编号能否在对应 Paper Note 中找到 |
| 已退役页面 / 已失效主张行 | — / — | 检索期默认过滤 |
| 逾 90 天未复核 | — | 与 `last_reviewed` 对照 |
| **单来源页面占比** | — | **最关键的指标**：占比高说明跨论文价值尚未形成 |
| 缺 `topics` 的页面 | — | `topics` 是批量合并的聚类键，缺失即无法归并 |
| 主张表被追加到页尾的痕迹 | — | 违反「最小 diff」纪律的信号 |

> 每第 5 篇 ingest 之后，Agent 应**主动建议**跑一次合并检查——只建议，不自行执行。
