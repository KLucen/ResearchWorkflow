---
name: researchvault-query
description: ResearchVault 研究问答。用户问「文献中关于 X 的证据/观点/方法」、要跨论文综合、核对某个结论的来源、判断某个说法有没有证据、或要求 lint 时加载：先 02_Wiki → 再 01_Papers/pass2 → 最后 Zotero 原文，回答必须四分类（established / conflicting / researcher-approved / unresolved）。
---

# ResearchVault 研究问答规程

> **纪律**：`<VAULT>/00_System/AGENTS.md`。**路径与环境**：`<VAULT>/00_System/Config.md`。**五色语义与 API 陷阱**：`<VAULT>/00_System/Zotero_Access.md`（五色语义的唯一事实源）。
> 本规程只写「怎么答」。**Zotero 一律通过 `python "<PKG>/tools/zotero/rvzotero.py" <子命令>` 读取**（任何等价的 Zotero 只读访问能力都可以替代）。

## 一、下钻顺序（不许跳级、不许从最后一层直接开答）

```
① <VAULT>/02_Wiki/           持久主张层 —— 先答这里
        ↓ 不足
② <VAULT>/01_Papers/pass2/   证据层 —— 每篇论文的精读记录（E 对象所在）
        ↓ 不足
③ Zotero 原文                不可变源 —— 用 rvzotero.py 读
```

**`<VAULT>/01_Papers/pass1/` 是 5 分钟导读，属阅读辅助，永不作为引用来源。**

**检索期默认过滤**：`retired_at` 非空的内容默认不参与回答；若某条命中已废止，**显式标注「此条已废止」**而非静默略过。

开了新话题、或上一轮结论依赖的是已经被推翻的主张时，**重新从 ① 开始**，不要接着上一轮的结论往外推。

### 第 ① 层：查 Wiki

```bash
grep -ril "<关键词>" "<VAULT>/02_Wiki/"        # 或按 topics / 页面名定位
```

- Wiki 页分五类**目录**：`topic/` `concept/` `synthesis/` `gap/` `entity/`（**目录即类型**——frontmatter 里没有 `type` 字段，用 `file.folder` 判断）。
- §2 **主张登记表**是唯一事实源，8 列：`ID | 主张 | 证据 | 状态 | 批准 | 生效 | 失效 | 替代`。
- 采用某条主张前，**读它的「证据」列**：必须是 `[[Paper Note]]E编号 (页码)` 三件套——**缺任何一件都不能当作已确立证据**。

### 第 ② 层：查 pass2

```bash
ls "<VAULT>/01_Papers/pass2/"                  # 按题名/短标题找候选论文
grep -n "E0[0-9]" "<VAULT>/01_Papers/pass2/<文件名>.md"
```

- 每篇一个 `type: paper` 的 Paper Note；`E` 对象带 `claim / quote / quote_zh / location / source_type / source`。
- `source` 决定这个 `E` 的**分量**：`annotation:绿|蓝|红|紫` 是研究者批注带出来的；`agent` 是 Agent 补充的（**分量更轻**，且必须已标注为 Agent 补充）。
- §4 关键证据表是引用 `E` 编号的规范位置。

### 第 ③ 层：查 Zotero 原文

```bash
cd "<PKG>"
python tools/zotero/rvzotero.py search --query "<关键词>" --qmode everything --limit 25   # 全库检索（含全文索引）
python tools/zotero/rvzotero.py get --key <ITEMKEY> --fields all                          # 元数据
python tools/zotero/rvzotero.py annotations --key <ITEMKEY> --split-comment --all          # 研究者批注
python tools/zotero/rvzotero.py retrieve --key <ITEMKEY> --query "<问题>" --passages 8     # 按相关度取片段 + 页码
python tools/zotero/rvzotero.py fulltext --key <ITEMKEY> --pages 1-30            # 按页取全文
python tools/zotero/rvzotero.py attachment --key <ITEMKEY> --all                           # 需要 PDF 磁盘路径
```

- **`retrieve` 返回的 `page` 来自逐页全文索引，不是批注页码**；引用批注位置时用该批注自己的 `annotationPageLabel`，并注明是**哪个附件**的页码（多附件之间不保证同分页）。
- `fulltext` 只接受**附件** key；`rvzotero.py` 会自动把父条目 key 解析成最好的 PDF 附件（直接调 API 用父 key 会 404）。
- 全文索引给不出你要的细节时，用 `attachment --all` 拿 PDF 路径，把文本提取到**系统临时目录**（PDF 不进 Vault），或在 Paper Note 里已有的摘录中找。

---

## 二、回答必须四分类（每次都分，不许混成一锅）

| 类别 | 什么时候用 | 怎么写 |
|---|---|---|
| **established evidence**（已确立的证据） | 有 ≥2 篇**独立**论文支持，且证据可回溯 | 逐条给 `[[Paper Note]]` + `E` 编号 + 页码 / 章节 |
| **conflicting evidence**（彼此冲突的证据） | 论文之间结论不一致，或存在 `−` 证据 | **并列双方**，别只引一边 |
| **researcher-approved interpretation**（研究者已批准的解读） | Wiki 里标 `consensus`，或研究者明确 `approved_for_wiki: true` | 注明「研究者已批准」 |
| **unresolved uncertainty**（未解决的疑点） | 无人回答、证据不足、只有单篇、或你只能推断 | 标注为 **Agent Interpretation (Provisional)**，并说明缺什么证据 |

**同一篇论文的多个实验不算独立来源。**

## 三、引用 Wiki 主张时（状态必须一起给）

必须带页面与状态，形如 `[[页面]]C03 · contested`：

| 主张状态 | 你能说成什么 |
|---|---|
| `consensus` | **researcher-approved**（研究者已批准） |
| `supported`（≥2 篇独立论文，**未批准**） | **established**，并注明「尚未经研究者批准」 |
| `proposed`（仅 1 篇） | 只能说「**有一篇论文主张**…」，不能说成"文献认为" |
| `contested` / `refuted` | **conflicting**；`contested` 必须**列出 `−` 证据**，`refuted` 说明被什么替代 |

状态不得自行升级。你**不能**把 `proposed` 说成 `supported`，也不能把 `supported` 说成 `consensus`。

## 四、引用研究者批注时

- **只有 `annotationText`（论文原文）能当论文证据**；`annotationComment` 是研究者的话，属 **Researcher Response**，不是论文说的。
- **页码**用 `annotationPageLabel`（Zotero 官方标签）。
- **评论按 `🔤…🔤` 区间切分**：区间内是机器词典（`tool_generated`，**永不作 `quote`**）；区间外才是研究者本人写的话。用 `--split-comment` 拿到 `commentParts`（`machine_texts` / `researcher_text`）。**不得因为整条评论含 `🔤` 就把研究者的话一并丢掉。**
- **紫色（`#a28ae5`「与我的研究相关」）是标记而非回答**——它说明研究者觉得相关，**不说明他得出了什么结论**。紫批注只能作为 `R` 对象的候选，**不得替研究者作答**；未回答处保留 `PENDING_RESEARCHER_RESPONSE`。

## 五、每条论断都要落到位置

- 形式：`[[Paper Note]]` + `E` 编号 + **page / section / 图 / 表 / 附录**。缺位置即不可采信。
- Wiki → 原文的路径必须**两次点击内**可达（Wiki 证据列 → Paper Note 的 `E` 编号 → 原文页码）。
- 需要你自己的判断时，明确写成 **Agent Interpretation (Provisional)**，与上面四类分开；**不得**把推断混进 established。

## 六、诚实信号（宁可说不知道）

- `truncated` / `sourcesSkipped` / `scanned` / `attachments` / 空 `results` 都是**真信号**：**「没取到」不等于「不存在」**。要说明「哪些来源没覆盖到」，不能静默当成「没有」。
- 说「文献里没有 X」之前，**先回查是不是查询方式错了**：Zotero 的批注查询在**不带 `itemType=annotation`** 时**静默返回 0 条**；Zotero API **每页上限 100**（`annotations --page-size` 的帮助原话是「Zotero 在 100 处静默截断，勿调大」）——但 `rvzotero.py annotations` **已自动翻完全部分页、默认取全部命中**，不会停在 100 条；批注可能**只挂在某一个附件**上。正确做法：用 `annotations`（始终显式带该参数、自动翻页、默认聚合全部附件，输出顶层 `attachments` 直接给出逐附件分项）。
- **空结果本身就是结论的一部分**：如实写成「在所查范围内未找到」，并列出**查了什么、范围多大**。

## 七、产生新综合时

如果回答过程中形成了新的跨论文结论：

1. **不要直接写进 `02_Wiki/`**——先作为**提案**给出（页面类型 / 拟新增主张 / 依据的 `E` 编号 / 建议状态）。
2. 得到研究者**明确批准**后再写入；写入时走**最小 diff**（只改受影响的具体行），并遵守：主张 ID 永不复用 · 只增行只改状态 · 证据列三段式 · 状态不跳级。
3. 相关纪律见 `agent/skills/researchvault/SKILL.md` §四。

## 八、被要求 lint 时

按六组检查（结构 / 证据 / 溯源 / 知识 / 主张一致性 / 研究），**覆盖写** `<VAULT>/00_System/lint-report.md`，并在末尾写 `本次覆盖：<已查页数> / <总页数> 页，<已查主张数> / <总主张数> 条主张`。完整清单见 `agent/skills/researchvault/SKILL.md` §六。
