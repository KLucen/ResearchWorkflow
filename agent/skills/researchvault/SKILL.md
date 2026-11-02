---
name: researchvault
description: ResearchVault 科研工作流（Zotero 不可变源 + Obsidian 精读笔记与 Wiki，三层证据纪律 Paper Evidence / Agent Interpretation (Provisional) / Researcher Response）。用户要求精读或 ingest 论文、继续未完成的阅读问答、提出或批准 Wiki 变更、运行 lint、批量处理 Zotero 文献时加载。
---

# ResearchVault 操作规程

> 本文件是**给 Agent 的操作规程**：照做即可执行。纪律的完整表述见 `<VAULT>/00_System/AGENTS.md`，路径与环境事实见 `<VAULT>/00_System/Config.md`，五色批注语义的**唯一事实源**是 `<VAULT>/00_System/Zotero_Access.md`。本文件与它们冲突时，以 `00_System/` 下的文件为准。

## 0. 开工前（每次都做，不要跳）

1. **定路径**：确定发布包根目录 `<PKG>`（含 `tools/`）与 Vault 根目录 `<VAULT>`（含 `00_System/`）。用户没说就从 `Config.md` 的 §1.1 环境事实表读，**不要凭记忆假设**。
2. **自检**：
   ```bash
   python "<PKG>/tools/zotero/rvzotero.py" ping      # 退出码 0 才能继续
   ```
   退出码 `3` = 连不上 Zotero（没运行 / 未开「Allow other applications…」/ 端口不是 23119）；`4` = 库 ID 不对；`5` = 目标不存在。
3. **读三份必读**：`<VAULT>/00_System/Config.md`（路径 + 体例开关）、`<VAULT>/00_System/AGENTS.md`（纪律）、`<VAULT>/00_System/Zotero_Access.md`（五色 + API 陷阱）。
4. **判状态**：`<VAULT>/01_Papers/pass2/` 里有没有 `<zotero_key>_<短标题>.md`？
   - **没有** → 走「一、ingest（出导读）」；
   - **有** → 走「三、继续问答」；**不要重出导读**。

**本文用到的 Zotero 读取能力**：一律通过 `python "<PKG>/tools/zotero/rvzotero.py" <子命令>`。你的 harness 若自带 Zotero 工具，按 `agent/adapters/` 下的对照表映射即可；**任何等价的 Zotero 只读访问能力都可以替代**。本技能正文只写子命令，不写任何 harness 专有工具名。

---

## 一、ingest：只出 5 分钟导读

**触发**：用户说「精读这篇 / ingest 这篇 / 加入这篇论文」。

**产出**：`<VAULT>/01_Papers/pass1/待精读/<zotero_key>_<短标题>.md` **一份，仅此一份**。

### 1-A 检索与通读

```bash
cd "<PKG>"
python tools/zotero/rvzotero.py search --query "<题名片段>" --limit 5          # 定位条目
python tools/zotero/rvzotero.py get --key <ITEMKEY> --fields all --include notes,attachments
python tools/zotero/rvzotero.py children --key <ITEMKEY> --include attachments,notes,annotations
python tools/zotero/rvzotero.py annotations --key <ITEMKEY> --split-comment --all
python tools/zotero/rvzotero.py retrieve --key <ITEMKEY> --query "<要回答的问题>" --passages 8
python tools/zotero/rvzotero.py fulltext --key <ITEMKEY> --pages 1-30
python tools/zotero/rvzotero.py attachment --key <ITEMKEY> --all              # 需要 PDF 磁盘路径时
```

- **必须先跑 `children`** 看清这篇论文有几个附件、批注到底挂在**哪一个**附件上——批注常常只挂在研究者实际读的那一个（原文 PDF / 双语 PDF / 译文 PDF 三选一）。
- `annotations` **默认聚合全部附件**；要精确定位用 `--attachment <附件KEY>`；只查第一个附件会漏。
- 读批注**必须带 `--split-comment`**：评论里 `🔤…🔤` 区间内是机器词典，区间外才是研究者的话。
- 全文优先用 `retrieve`（按相关度给片段 + 页码），需要整章再 `fulltext --pages A-B`。Zotero 全文索引给不出你要的细节时，用 `attachment --all` 拿磁盘路径，把文本提取到**系统临时目录**（PDF 绝不进 Vault）。
- **单独扫一遍无编号的尾部小节**（`Limitations` / `Ethics Statement` / `Broader Impact` 等）——按编号标题扫会漏掉它们，漏扫会得出「本文没有 Limitations」这种错误结论。
- 理清论文**自身的章节编号与页码**，只到「章」这一层，不逐小节。**页码基准要写明是哪个附件**。

### 1-B 写导读（七段固定结构）

以 `<VAULT>/01_Papers/pass1/_Reading_Guide_Template.md` 为骨架（`type: reading-guide`，`schema_version: 4`）：

| 段 | 内容 | 上限 |
|---|---|---|
| 顶部 | **页码基准**（哪个附件）+ 一句话 | ≤ 40 字，不评价 |
| 一、要解决的问题 | Problem / Gap / Motivation | ≤ 150 字，**不写它做成了没有** |
| 二、论文架构地图 | 表格 `章 \| 页 \| 在做什么 \| ★ \| 建议`，一行一章 | ★ 按「与研究者研究相关、可复用」评，**不按作者篇幅权重** |
| 三、核心观点 | 作者**明确声称**的贡献与主张 3–5 条，每条标章节定位 | 只记「声称什么」，**不记「证明了什么」** |
| 四、读前必备的概念与记号 | 3–5 条，只给「是什么」 | — |
| 五、阅读路线 | 表格 `目的 \| 读法 \| 约需` | — |
| 六、带着这几个问题读 | 3–5 问，每问附**一行定位** | 判断类标「**论文不答**」 |

**硬约束（违反即返工）**：

- 全文 **≈1000 中文字，1200–1300 字为上限**，宁短不长。
- **不写实验结果、数字、作者对结果的解释与最终结论。**
- **不逐小节展开**（小节信息只出现在架构地图的「在做什么」格里）；不复制论文的标题层级结构，但保留章节编号以便对照原文。
- 论文没有清晰章节时，退化为「摘要 / 引言 / 方法 / 实验 / 讨论 / 附录」粗分块并注明。
- **pass1 绝不双写**：导读里**不得出现** `E` 证据对象、主张、Wiki 提案、`R` 对象或 `PENDING_RESEARCHER_RESPONSE`。一旦出现，就有了第二个证据源。
- **不写状态字段**——导读在 `待精读/` 还是 `已精读/` **就是**它的状态。
- **不写 Wiki 提案**——提案一律写在 `pass2/` 里。

### 1-C 收尾

1. `<VAULT>/log.md` **追加**一行（只追加，不改历史行）。
2. **本轮不写 `pass2/`。**
3. 告诉用户下一步：**去 Zotero 读原文并做五色批注**，批注完成后回来说一声。

> 为什么不能跳过批注直接成稿：`pass2/` 的证据基础是**研究者批注 + Agent 通读**；缺批注就生成，会产出一个未经确认、却长得像结论的证据源。

---

## 二、pass2：研究者批注之后才成稿

**触发**：用户说「读完了 / 批注好了」，或已经有 `pass2/<同名>.md` 而研究者又补了批注。

**产出**：`<VAULT>/01_Papers/pass2/<同名>.md`（`type: paper`，`schema_version: 3`，13 节 §0–§12），同时把导读从 `pass1/待精读/` **移入** `pass1/已精读/`。

```bash
python tools/zotero/rvzotero.py annotations --key <ITEMKEY> --split-comment --all
```

### 执行八步

1. **先读批注，再读原文**：批注**优先于**你自己的通读结论——研究者标过的位置就是重点。
2. **批注沉淀**：把批注转成 `E` 对象（`source: annotation:绿|蓝|红|紫`），写入 **§8 批注沉淀**。🟡 黄色**不进** `E` 对象，直接进 `03_Vocabulary/`。
3. **写 §1–§7**：以通读为底，**受批注影响的段落用 `==…==` 包住**，让「批注带出来的」一眼可辨。
4. **提问 1–3 个（Ask, do not assume）**：优先问那些会实质改变解读或研究相关性的问题。例：「作者声称 X，你认为这个结论可信吗？为什么？」「哪个贡献对你的研究最重要？」「这个方法能迁移到你的研究情境吗？」「哪个局限会让你无法采用它？」
   **不得编造回答**；未回答处保留 `PENDING_RESEARCHER_RESPONSE`。
5. **补充**：批注很少时你可以补该论文的重点与细节，但**必须标注为 Agent 补充**（§8.3），不得混入研究者信号。
6. **主张影响检查**：本次证据是否触及 `02_Wiki/` 已有主张？更新 **§11 主张级变更表**（动作 / 页面 / Claim ID / 变更 / 依据 E 编号）。
7. **改动实质研究论断时先请求批准**，再做持久化 Wiki 变更。
8. `reading_status: deep-read`；把导读移入 `已精读/`；Wiki 变更批准并写入后置 `completed`；`log.md` 追加一行。

**两种标记，一句话分清**：`==高亮==` = 这段来自批注；行末 `（Pass 2 补充）` = 这一处是后来补进去的。

---

## 三、继续问答（同一篇论文的后续轮次）

**触发**：`pass2/<同名>.md` 已存在，研究者又批注或回答了一个问题。

1. 读该 Paper Note，找**第一个未回答的** `PENDING_RESEARCHER_RESPONSE` 块。
2. 若研究者本轮已回答：把他的话**原文**填进 `researcher_response`（**不得改写、不得替他总结成结论**），按需补 `response_type`；只有他明确同意 `approved_for_wiki: true` 时，该判断才可提升到 Wiki。
3. 若研究者只是新增了批注：重跑 `annotations`，把新增批注**最小 diff** 地并入 §8，并同步受影响段落的高亮。
4. **一次最多问 1–3 个**高价值问题；风格简洁、苏格拉底式，证据先行，然后提问。
5. 收尾：`log.md` 追加一行。

**语言体例**（每次写作都适用）：

- 说明性内容**一律中文**；原文摘录**保持原语言**并紧随中文翻译（多行 `原文（EN）："…"` / `译文（ZH）："…"`；短句 `> "…"（译：…）`）。
- **不译**：数字、单位、公式、变量名、模型名、数据集名、指标名、引用键。
- **frontmatter 键与枚举值一律英文**（Dataview 与 lint 的接口，永不翻译）。
- 只摘支撑论断的短句，不成段复制原文。

---

## 四、Wiki 变更（需研究者批准）

**规则**：主张**先提案**（写进 `pass2/` §11 主张级变更表）→ **研究者批准** → 才写入 `02_Wiki/`。

```
<VAULT>/02_Wiki/
├── _WikiIndex.md      # 投影页，非事实源
├── _Wiki_Template.md
├── topic/             # 主题地图
├── concept/           # X 是什么        ← 🟢 绿批注的主要去向
├── synthesis/         # 文献整体说了什么
├── gap/               # 什么还不知道     ← 🔴 红批注的主要来源
└── entity/            # 专名实体（人 / 组 / 系统 / 模型 / 数据集）
```

- **目录即类型**：frontmatter **不写 `type`**；移动文件就是改类型。**任何内容页都必须在五个目录之一**；`02_Wiki/` **根下只允许 `_` 前缀的基础设施文件**，非 `_` 前缀的文件落在根下即违规。Dataview 用 `file.folder`。
- **§2 主张登记表是唯一事实源**，8 列固定：`ID | 主张 | 证据 | 状态 | 批准 | 生效 | 失效 | 替代`。主张 ID `C01, C02, …` 页内唯一、**永不复用**。
- **证据列强制三段式**：`[[Paper Note]]E编号 (页码)`——缺一不可；从 Wiki 命中的任何结论都要能在**两次点击内**到达论文原文位置。
- **状态不得跳级**：`proposed → supported`（≥2 篇**独立**论文）`→ consensus`（研究者批准）；出现 `−` 证据转 `contested`；被推翻标 `refuted`。**同一篇论文的多个实验不算独立。**
- **只增行、只改状态，行永不删除**；被推翻的行标 `refuted` 并保留，注明替代主张。
- **能遗忘**：内容带 `effective_from` / `retired_at`；**`retired_at` 非空即检索期默认过滤**，被问起时标注「此条已废止」。
- **最小 diff**：只改受影响的**具体行**，不重写整页；**禁止把新素材追加到页尾**。
- 更新顺序：① 先跑检查（frontmatter 合法 / 链接可达 / 证据链完整 / 无失效引用）→ ② 定位受影响的行 → ③ 增删改并同步 `topics` / `updated` / 证据引用 / §6 变更记录 → ④ **增量重建 `_WikiIndex.md` 的受影响区**（不整页重写）。
- **每第 5 篇 ingest 后主动建议**跑一次合并检查——**只建议，不自行执行**。

---

## 五、Vocabulary（语言层）

🟡 黄色批注 = **生词** → `<VAULT>/03_Vocabulary/`。一个词元一份词条（`type: vocabulary`，含 `lemma / surface_forms / dictionary / encounters / acquired / first_seen / last_seen`）。

- **同一个词再遇到时回到原文件追加一节，不新建文件**；`encounters` 与实际语境记录条数必须一致。
- `dictionary` 行可填 `🔤…🔤` 区间内的机器词典——它是**释义**，标注 `tool_generated`，**永远不能成为 `quote`**。
- **Vocabulary 是语言层**：其内容**不得**出现在 Wiki 页、`E` 证据对象或主张登记表中。
- `acquired` **不得由 Agent 自行标记**（需研究者判断）。

---

## 六、lint（六组）

**产出**：**覆盖写** `<VAULT>/00_System/lint-report.md`（唯一输出位置）。

| 组 | 查什么 |
|---|---|
| **结构** | YAML 非法/缺失；断链；必填字段缺失；**导读位置与 `pass2/` 一致**（`待精读/` ⇒ 尚无 `pass2/<同名>.md`；有 `pass2/` ⇒ 导读应在 `已精读/`；导读落在 `pass1/` 根下即违规）；**导读体量** >1300 中文字；**pass1 双写**（出现 `E01` 编号、`PENDING_...` 字面量、主张或提案表即违规——导读顶部「本文件不含 E 证据对象」这类**免责声明行不算**）；**Wiki 目录即类型**（内容页必须在五目录之一；根下非 `_` 前缀即违规；frontmatter 出现 `type` 即违规）；**Wiki 证据回链三件套**（缺回链或缺页码即报警）；**页尾追加痕迹**（新内容以「补充：…」堆在页尾、主张行未被 §6 覆盖）；`_WikiIndex.md` §3/§4 与各页不一致；Vocabulary 轻量检查（文件名与 `lemma` 一致、`encounters` 数目一致、`acquired` 未被滥用）；Paper Note 章号与模板不一致 |
| **证据** | 论断没有引用；引语没有位置；没有证据支撑的综合 |
| **溯源** | 未经批准的研究者判断被写入；Agent 解读被误标成研究者判断 |
| **知识** | 重复的 Wiki 概念；陈旧页面；未记录的矛盾；该更新却没更新 |
| **主张一致性** | 标 `consensus` 但独立来源 <2；标 `supported` 但仅 1 篇；标 `contested` 却无任何 `−` 证据；证据列的 `E` 编号在对应 Paper Note 中不存在（悬空引用）；同一主张在多页重复登记；§2 出现整行删除痕迹 |
| **研究** | 反复出现的未决问题；证据缺口；跨论文新兴主题；可能的研究空白 |

**两条判据口径**：`E` 编号唯一性**只在 §4 关键证据表内**检查；pass1 的免责声明行**不算**违规。

**定期检查（四类）**：A 去重合并 · B 回原始核查 · C 冲突场景限定 · D 失效下线。前三类属于批量核查，**必须输出覆盖清单**（查了哪些页 / 哪些主张 / 每条结论）——**保证全量而非抽样**。

`lint-report.md` 末尾固定写：`本次覆盖：<已查页数> / <总页数> 页，<已查主张数> / <总主张数> 条主张`。

---

## 七、批量处理

**触发**：用户说「把 Zotero 里某个集合的论文都过一遍 / 批量 ingest」。

1. **先列清单再动手**：`rvzotero.py collections` 拿集合 key → `rvzotero.py search --collection <KEY> --limit 100`（**上限 100**，超了要 `--offset` 翻页）。
2. **逐篇判状态**：已有 `pass2/<同名>.md` 的跳过并说明；已在 `待精读/` 的**不重出导读**。
3. **一次只做一篇的完整流程**，每篇结束追加一次 `log.md`。**不要批量写 `pass2/`**——每篇都得等研究者的批注。
4. **集合只管归置，不承担状态**（`00_Inbox` / `10_*` / `20_*` / `30_*` / `40_*` / `90_Archive` 是元数据式归置；`Config.md` §6 给了映射示例。双挂时取编号更小的那个；顶层唯一）。
5. 批量结束后报告：**处理了几篇 / 跳过几篇及原因 / 其中几篇已可成稿 / 下一步等研究者做什么**。
6. 累计到第 5 篇时，**建议**跑合并检查。

---

## 八、边界（越界即停）

- **Zotero 只读**。写回任何内容（含你生成的笔记）都要研究者**明确同意**。
- **禁止**解析 `zotero.sqlite` / `prefs.js` 或任何 Zotero 内部数据库文件——一律走 `rvzotero.py`。
- **PDF 不进 Vault**：全文提取到系统临时目录，用完即弃。
- **不代研究者作答**；不把 Agent 的推断写成研究者的判断。
- 需要研究者同意的动作：删除/批量修改 Zotero 条目 · 向 Zotero 写回 · 覆盖研究者已写的段落 · 删除或大规模移动 Vault 文件 · 把研究者判断提升为 Wiki 持久结论 · 标记 Vocabulary 的 `acquired`。
- 不碰 `<VAULT>/.obsidian/`、`.git/`、同步工具目录、`.trash/`；`00_System/*_Schema.md` 与 `AGENTS.md` **只读**。
- **诚实信号**：`truncated` / `sourcesSkipped` / `scanned` / `attachments` / 空 `results` 都是真信号——**「没取到」不等于「不存在」**，见到就要在结论里说明。
- 遇到「这篇论文没有批注」这类结论前，**先回查是不是查询方式错了**（见 `Zotero_Access.md` §4 的四类陷阱）。
