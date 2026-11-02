# Vocabulary Schema（生词库结构）

> Vocabulary 是**语言层**，不是知识层。它记录「读文献时遇到的、还不认识的词」。
> 它不进 `02_Wiki/`、不参与主张登记表、不影响 `research_position`，也不参与主张一致性 lint。
>
> 执行纪律见 `AGENTS.md`；批注读取见 `Zotero_Access.md`。

## 1. 触发条件

只有 **🟡 黄色高亮**（`#ffd400`）的词进入本库。**是否算生词由你的高亮行为判定，不由 Agent 判断**——Agent 不得因为「觉得这个词难」就自行收进来。

## 2. 目录与文件名

`03_Vocabulary/<lemma>.md` —— 小写词元。例如 `unify.md` 收录 `unified / unifies / unifying`。

- Agent 负责**词形归一**（lemma 化）；拿不准时先用高亮原词形建文件，并在 `surface_forms` 里标注待归一，下次遇到再合并。
- 文件名创建后**保持稳定**。
- 本目录根下只放模板与词条；不要建子目录。

## 3. Frontmatter

```yaml
---
type: vocabulary
lemma: "unify"
surface_forms: [unified, unifies, unifying]
dictionary: "v. 统一；使成一体；使一元化"
encounters: 1
acquired: false
first_seen: 2026-01-01
last_seen: 2026-01-01
---
```

| 字段 | 说明 |
|---|---|
| `type` | 固定为 `vocabulary`（**本目录是唯一允许写 `type` 的笔记目录**；`02_Wiki/` 与之相反，不写类型字段） |
| `lemma` | 词元，小写，**与文件名一致** |
| `surface_forms` | 已遇到的变形，**追加式** |
| `dictionary` | **这个词本身的意思**（稳定，不随语境变） |
| `encounters` | 语境记录条数，**必须与正文 `## 语境记录` 下的小节数一致** |
| `acquired` | 是否已掌握 |
| `first_seen` / `last_seen` | 首见 / 最近一次遇见 |

> **本层有意不设 `schema_version`**（不是遗漏）：Vocabulary 是语言层，不参与 Wiki、主张登记表与主张一致性 lint，字段只增不改语义，没有跨版本迁移的需求。另外三层各带版本号：导读 `4`、Paper Note `3`、Wiki `4`。

## 4. 正文（只追加，不改旧）

```markdown
# unify

## 词典义

v. 统一；使成一体；使一元化

## 语境记录

### 2026-01-01 · [[ABCD1234_Paper Title]] p.2
- 原文（EN）："unified"
- 本语境义：把碎片化的研究收敛到同一框架下（不是"合并"，是"统一坐标系"）
- 机器词典：🔤v. "unify"的过去式和过去分词；统一的；一元化的；同一标准的🔤
- 备注：

### 2026-01-02 · [[EFGH5678_Another Paper]] p.7
- 原文（EN）："a unified continuous process"
- 本语境义：…
- 机器词典：
- 备注：
```

**两个「意思」必须分开写**，这是本库的核心价值：

- `## 词典义` / frontmatter 的 `dictionary` = **这个词本身的意思**（稳定、可复用）
- 每节的 `本语境义` = **它在这句话里的意思**（会随语境漂移；同一个词在不同论文里常常不同）

## 5. 规则

1. **只追加，不重写**：每次遇到就在 `## 语境记录` 下加一节，时间**正序**（最新在下）。
2. `encounters` 与 `last_seen` 随追加更新；`surface_forms` 追加新变形。
3. **机器词典与你的理解分开**：带 `🔤…🔤` 的释义是翻译插件产物（`tool_generated`），**只能填进「机器词典」行**；「本语境义」必须是中文解读，**不得直接粘贴词典**。
4. **掌握判定** `acquired: true`：
   - 你明确说「这个词我认识了」，或你直接改字段；
   - Agent 可以**建议**（例如 `encounters >= 3` 且近两篇未再高亮），但**需你确认**——不得自行标记。
5. `acquired: true` 后 ingest **跳过**该词，不再追加；文件保留供回溯（**不要删**）。
6. **语言层隔离**：本库内容**不得出现**在 Wiki 页、`E` 证据对象或主张登记表中。

## 6. 语言与引文

说明性内容用中文；高亮原文保持原语言（英文就写英文原句）。词条标题与文件名用英文词形（它是被记录的对象本身）。

## 7. 与其他文件的关系

- **模板**：`_Vocabulary_Template.md`（本目录内）。
- **批注来源**：🟡 黄色高亮。读取用 `python tools/zotero/rvzotero.py annotations`（支持 `--color` 过滤与 `--split-comment` 按 `🔤…🔤` 区间切分；具体参数见 `tools/zotero/README.md`），或任何**等价的只读 Zotero 读取能力**。
- **视图**：`00_System/Dataview_Dashboard.md` 的「生词库」两视图（需装 Dataview 插件）。
- **lint**：只做轻量检查（YAML 合法、文件名与 `lemma` 一致、`encounters` 与记录条数一致、`acquired` 未被滥用）。
