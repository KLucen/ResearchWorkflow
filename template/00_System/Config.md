# Config（配置事实源）

> **这是本 Vault 的配置事实源**：路径、Zotero 映射、体例参数、当前状态一律以本文件为准。
> `AGENTS.md` 只写纪律；Agent 每次执行任务前先读本文件，**不要凭记忆假设路径**。
> 本文件在模板中是**占位符 + 首次运行清单**：复制 `template/` 到你的 Vault 之后，按 §1 逐项填掉。

## 1. 首次运行清单（照着勾）

- [ ] 1. 把 `template/` 的内容复制到你的 Vault 根目录（Obsidian 打开这个目录）。
- [ ] 2. 填下面 **§1.1 环境事实表**——尤其是 `<VAULT>` 与 Zotero Local API 地址。
- [ ] 3. 装好 Zotero 与 Python 3.8+；在 Zotero 里打开 `Settings → Advanced → General → Allow other applications on this computer to communicate with Zotero`。
- [ ] 4. 验证访问层：`python tools/zotero/rvzotero.py ping`，退出码应为 `0`（退出码 `3` = 连不上 Zotero，按提示修）。
- [ ] 5. 填 **§4 你的研究坐标摘要**（详细内容写在 `Research_Profile.md`）。
- [ ] 6. 按你的 Zotero 集合结构改 **§6 集合 ↔ `research_position` 映射**（默认表是示例）。
- [ ] 7. 决定 **§5 体例参数**（默认：正文中文 + 原文摘录保留原语言并附中文翻译）。
- [ ] 8. 确认 **§7 路径约定**里的"勿动目录"清单与你的实际插件一致。
- [ ] 9. 打开 Obsidian 的 Dataview 插件（`Dataview_Dashboard.md` 与 `_WikiIndex.md` 依赖它）。
- [ ] 10. 在 `AGENTS.md` 与 `Workflow.md` 之间跑一次空转：让 Agent 读本文件，确认它能说出你的 Vault 路径与 Zotero API 地址。

## 1.1 环境事实表

| 项 | 值（**请填**） | 说明 |
|---|---|---|
| Vault 根目录 | `<VAULT>` | Obsidian 打开的目录；下文所有相对路径都以它为根 |
| Zotero 数据目录 | `<ZOTERO_DATA>` | PDF 通常在其 `storage/<attachment_key>/` 下；**只读**，不要放进 Vault |
| Zotero Local API | `http://127.0.0.1:23119/api` | 默认值；需先运行 Zotero 并打开上面第 3 步的开关 |
| Local API 覆盖变量 | `RV_ZOTERO_API` | 换端口 / 换机器时用环境变量覆盖，不要改脚本 |
| 库（library） | `users/0` | 个人库默认；团队库用 `groups/<id>`；覆盖变量 `RV_ZOTERO_LIBRARY` |
| Python | `≥ 3.8` | `tools/zotero/rvzotero.py` 只用标准库，无需 `pip install` |
| 访问层脚本 | `tools/zotero/rvzotero.py` | 发布包内；相对发布包根目录调用 |
| 访问层文档 | `tools/zotero/README.md` | 子命令与参数的权威说明 |
| Agent 接入契约 | `agent/AGENTS.md` | 换 harness / 换机器时先读它 |
| Obsidian 插件 | Dataview（必需） | `_WikiIndex.md`、`Dataview_Dashboard.md` 依赖 |

> **本文件不得写入任何个人信息**（真实用户名、本机绝对路径、私有库 ID）。占位符保持 `<...>` 形式。

## 2. Vault 结构

```text
<VAULT>/
├── 00_System/                 # 纪律与 schema（本目录）
│   ├── AGENTS.md              # Agent 宪法（纪律）
│   ├── Config.md              # 本文件（配置事实源）
│   ├── Workflow.md            # ingest / query / lint 操作手册
│   ├── Paper_Schema.md        # 阅读导览 + Paper Note 结构
│   ├── Wiki_Schema.md         # Wiki 五类 + 六节 + 主张登记表
│   ├── Vocabulary_Schema.md   # 生词词条结构
│   ├── Research_Profile.md    # 研究坐标（研究者填写）
│   ├── Zotero_Access.md       # Zotero 访问规范 + 五色批注 + API 陷阱
│   ├── Automatic_Archiving_Rules.md
│   ├── Dataview_Dashboard.md
│   └── lint-report.md         # lint 产物（唯一输出位置）
├── 01_Papers/
│   ├── pass1/                 # 5 分钟阅读导览（阅读辅助，不是证据）
│   │   ├── _Reading_Guide_Template.md
│   │   ├── 待精读/            # 位置即状态：还没有 pass2/
│   │   └── 已精读/            # 位置即状态：已经有 pass2/
│   └── pass2/                 # 精读总结（证据层，唯一来源）
│       └── _Paper_Template.md
├── 02_Wiki/                   # 持久知识（主张层）
│   ├── _WikiIndex.md          # 入口投影页（不是事实源）
│   ├── _Wiki_Template.md
│   ├── topic/                 # 主题地图
│   ├── concept/               # X 是什么
│   ├── synthesis/             # 文献整体说了什么
│   ├── gap/                   # 什么还不知道
│   └── entity/                # 专名实体
├── 03_Vocabulary/             # 生词库（语言层）
│   └── _Vocabulary_Template.md
├── index.md                   # Vault 入口页
└── log.md                     # 研究日志（只追加）
```

**`01_Papers/pass1/` 下只有两件事**：两个状态目录 + 一份模板。导览落在 `pass1/` 根下即违规。

## 3. 文件职责表

| 文件 / 目录 | 职责 | 谁写 |
|---|---|---|
| `00_System/AGENTS.md` | 纪律（必须 / 禁止 / 流程） | 研究者（改纪律时）；Agent 只读 |
| `00_System/Config.md` | 配置事实源（本文件） | 研究者；Agent 只在被要求时改 |
| `00_System/Workflow.md` | 三阶段操作手册 | Agent 可读；改需研究者同意 |
| `00_System/*_Schema.md` | 结构与字段定义 | 同上 |
| `00_System/Research_Profile.md` | 研究坐标 | **研究者**（Agent 起草需批准） |
| `00_System/lint-report.md` | lint 输出 | **Agent 覆盖写**（每次 lint 重写全文） |
| `01_Papers/pass1/待精读/**` | 5 分钟导览 | Agent（ingest 时一次性写出，此后不改） |
| `01_Papers/pass1/已精读/**` | 已配对的导览 | Agent（移动，不改内容） |
| `01_Papers/pass2/**` | 精读总结 + 证据对象 | Agent（**批注之后**生成，研究者可改） |
| `02_Wiki/**` | 持久主张 | Agent（**需研究者批准**） |
| `03_Vocabulary/**` | 生词词条 | Agent 追加；`acquired` **只能研究者标** |
| `index.md` | 入口页 | 研究者 |
| `log.md` | 日志 | Agent **只追加**，不重写历史行 |
| Zotero | PDF / 元数据 / 批注 | **只读**；写回需研究者明确同意 |

## 4. 处理循环（每阶段 → 落点）

| 阶段 | 谁做 | 产出落点 |
|---|---|---|
| Raw Source | — | Zotero（PDF + 元数据 + 批注；**不进 Vault**） |
| ①生成导览 | Agent | `01_Papers/pass1/待精读/<zotero_key>_<短标题>.md` |
| 阅读 + 五色批注 | **研究者** | Zotero 批注（颜色 + 评论） |
| ②生成精读总结 | Agent | `01_Papers/pass2/<同名>.md`（13 节 + E 对象 + 1–3 问 + §11 提案）；导览移入 `pass1/已精读/` |
| 回答 Agent 问题 | **研究者** | 同一份 `pass2/`（`R` 对象；未答留 `PENDING_RESEARCHER_RESPONSE`） |
| Compile（Wiki 变更） | Agent **经批准后**写 | `02_Wiki/{topic,concept,synthesis,gap,entity}/` |
| Query | Agent | 对话回答（四分类），必要时回写笔记 |
| Lint | Agent | `00_System/lint-report.md`（覆盖写）+ `log.md` 追加 |

## 5. Schema 速查（字段定义以 `*_Schema.md` 为准）

### 阅读导览（`pass1/`）

`type: reading-guide`、`schema_version: 4`、`zotero_key`、`title`、`created`、`last_reviewed`。
**不写状态字段**（位置即状态）；**不写** `E` 编号 / 主张 / Wiki 提案 / `R` 对象。

### Paper Note（`pass2/`）

`type: paper`、`schema_version: 3`、`title`、`zotero_key`、`primary_area`、`research_position`、`reading_status`、`interest_level`、`research_relevance`、`last_reviewed`。

- `research_position`: `core` | `mentor` | `intersection` | `exploration`
- `reading_status`: `deep-read` | `completed` | `archived`

正文 13 节：§0 阅读轮次 · §1 研究问题 · §2 核心贡献 · §3 方法 · §4 关键证据 · §5 主要结果 · §6 局限 · §7 与研究的关系 · §8 批注沉淀与二次总结（§8.1 研究者评论 / §8.2 机器词典 / §8.3 Agent 补充）· §9 新知识与假设 · §10 未决问题 · §11 Wiki 更新提案（主张级变更表）· §12 相关论文。

**`E` 证据对象**：`claim`、`quote`、`quote_zh`、`location`、`source_type`、`source`（`pass1` | `annotation:<颜色>` | `agent`）、`confidence`。
**`R` 对象**：`agent_question`、`researcher_response`、`response_type`、`approved_for_wiki`。

### Wiki（`02_Wiki/<五类目录>/`）

`schema_version: 4`、`title`、`status`（`draft` | `active` | `retired`）、`effective_from`、`source_papers`、`topics`、`confidence`、`updated`。
**不写 `type`**（目录即类型）；内容页必须在五个目录之一。
正文六节：§1 综合与当前理解 · §2 主张登记表（**唯一事实源**，8 列 `ID | 主张 | 证据 | 状态 | 批准 | 生效 | 失效 | 替代`）· §3 共识 · §4 分歧 · §5 未解决问题 · §6 变更记录。

### Vocabulary（`03_Vocabulary/`）

`type: vocabulary`、`lemma`、`surface_forms`、`dictionary`、`encounters`、`acquired`、`first_seen`、`last_seen`。
一个词元一份文件；同一个词再遇到时回原文件追加一节。

## 6. Zotero 集合 ↔ `research_position` 映射

> ⚠️ **下表是示例映射，请按你自己的 Zotero 集合结构改。**
> 它只决定**入库时**的默认分流，不决定状态；`research_position` 的最终判定以 Paper Note frontmatter 为准（依据见 `AGENTS.md`「自动分类规则」与 `Research_Profile.md`）。

| Zotero 顶层集合（示例） | 默认 `research_position` | 备注 |
|---|---|---|
| `00_Inbox` | 待判定 | 新入库；判定后再归位 |
| `10_<核心领域>` | `core` | 你的主攻方向 |
| `20_<相邻 / 导师方向>` | `mentor` | 相邻领域，尚未成为自身核心 |
| `30_<交叉>` | `intersection` | 两个方向都实质 |
| `40_<探索>` | `exploration` | 有意跟进，但不在当前研究计划内 |
| `90_Archive` | `archived` | **只归档，不删除条目** |

规则：

- 一篇论文可同时在多个**子**集合，但**顶层归属唯一**（决定默认 position）。
- 同时挂在两个顶层集合时，按**编号更小**（更核心）的那个处理。
- 集合只承担「入库分流」，**不承担状态**——状态由 `reading_status` 表达。

详细读取规范见 `Zotero_Access.md`。

## 7. 路径约定与勿动目录

- 一切路径以 Vault 根（`<VAULT>`）为基准写**相对路径**；文档里不写机器绝对路径（换机器会全断）。
- **Zotero 数据目录与本 Vault 严格分离**：PDF 不进 Vault；需要全文时把文本提取到系统临时目录，用完即弃。
- **勿动目录**（Obsidian / 插件 / 同步工具自己管理，Agent 不读不写不整理）：

| 目录 / 文件 | 归属 |
|---|---|
| `.obsidian/` | Obsidian 配置（含插件列表） |
| `.git/` | 版本控制（若启用了 git） |
| 同步工具目录（如 `nutstore-sync/` 之类） | 云同步 |
| `.trash/` | Obsidian 回收站 |

> 按你实际启用的插件增删此表；**原则是：不是本工作流产出的目录，一律不碰。**

## 8. 自动化边界

**Agent 可自动做**：读取 Zotero（只读）、生成 / 更新 Paper Note、生成导览、**建议** Wiki 变更、追加 `log.md`、覆盖写 `lint-report.md`、把 PDF 文本提取到临时文件、重建 Dataview 视图。

**必须研究者明确同意**：向 Zotero 写回任何内容（含 AI 生成的笔记）、删除或批量修改 Zotero 条目、覆盖研究者已写段落、删除或大规模移动 Vault 文件、把研究者判断提升为 Wiki 持久结论、标记 Vocabulary 的 `acquired`。

**Agent 永远不能做**：代研究者回答（`PENDING_RESEARCHER_RESPONSE` 只能由研究者填）、直接解析 Zotero 内部数据库（`zotero.sqlite` / `prefs.js`）、把机器词典（`🔤…🔤` 内文本）当作论文原文引用。

## 9. 当前状态

> 每次实质变更后更新本节；**不写个人身份信息**。

| 项 | 值 |
|---|---|
| Vault 建立日期 | `<YYYY-MM-DD>` |
| 已精读论文数 | `0` |
| Wiki 页数 / 主张数 | `0 / 0` |
| 最近一次 lint | `<未运行>` |
| 最近一次合并检查（每 5 篇） | `<未运行>` |
| 已知待办 | `<无>` |

## 10. 迁移记录（本地）

> 记录本 Vault 自己的结构 / schema 变更。**只追加**，不删历史行。

| 日期 | 变更 | 影响文件 | 备注 |
|---|---|---|---|
| `<YYYY-MM-DD>` | 初始化（从 `template/` 复制） | 全部 | schema_version = 4 |
