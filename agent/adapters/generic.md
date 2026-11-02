---
title: 通用接入（任意 Agent）
scope: agent/adapters
---

# 通用接入：任何能读文件、能跑命令的 Agent

> 本文件是**最低公共分母**方案，不依赖任何 harness 的专有特性（没有技能系统、没有插件、没有 MCP 也行）。
> 只要你的 Agent 满足下面三条硬下限，就能完整跑这套工作流。
>
> **通用接入契约**：[../AGENTS.md](../AGENTS.md)（完整版）。**五色语义**：`<VAULT>/00_System/Zotero_Access.md`（唯一事实源）。

---

## 一、硬下限：三个能力

| 能力 | 用途 | 缺失后果 |
|---|---|---|
| **读文件** | 读 `Config.md` / `AGENTS.md` / 已有笔记 / 两份 SKILL.md | 无法接入 |
| **写文件** | 写 `pass1/` `pass2/` `02_Wiki/` `03_Vocabulary/` `log.md` | 只能问答，不能 ingest |
| **运行命令** | 跑 `python tools/zotero/rvzotero.py <子命令>` | **读不到 Zotero**（这一步没有替代品） |

以及环境侧三条：

1. **Python ≥ 3.8**（`rvzotero.py` **只用标准库**，不需要 pip 装任何东西）；
2. **Zotero 正在运行**，且已开启 `Settings → Advanced → General → "Allow other applications on this computer"`；
3. 本机 `http://127.0.0.1:23119` 可访问（**不需要外网**）。

**做不到"运行命令"的 Agent（纯对话、只有搜索工具）**：可以读笔记、答问题，但**不能做 ingest**——因为 Zotero 里的批注与 PDF 全文它拿不到。这一点不要勉强，如实说明即可。

---

## 二、三步接入

### 第 1 步：把契约放进系统提示（或用一条项目指令文件引入）

把 §三 那段贴进 Agent 的 **system prompt**，或写进它的项目指令文件（`AGENTS.md` / `CLAUDE.md` / `.cursor/rules/*.mdc` …，见 [§六](#六已经支持指令文件的-harness)）。

**必须同时给它两个绝对路径**（Agent 无法从别处推断）：

- `<VAULT>` —— 知识库根（笔记写在里面）；
- `<PKG>` —— 发布包根（`rvzotero.py` 在里面）。

### 第 2 步：把工作目录固定到 `<VAULT>`

```bash
cd "<VAULT>"          # 或： <你的 harness> --cwd "<VAULT>"
```

理由：笔记、Wiki、`00_System/` 都在 `<VAULT>` 下；工作目录不对就会写到别处，或者读不到事实源。`<PKG>` 用**绝对路径**引用即可，脚本可以在任意位置。

### 第 3 步：自检

```bash
python "<PKG>/tools/zotero/rvzotero.py" ping      # 退出码 0 = 通
```

| 退出码 | 含义 | 怎么办 |
|---|---|---|
| `0` | 正常 | 继续 |
| `2` | 参数用法错 | 看 `--help` |
| `3` | 连不上 Zotero | 打开 Zotero；开 "Allow other applications…"；确认端口 |
| `4` | HTTP 非 200 | 常见是库 ID 不对（`RV_ZOTERO_LIBRARY`，默认 `users/0`） |
| `5` | 条目/附件找不到 | 核对 key；先 `search` 找 key |

再挑一篇**你自己知道肯定有批注**的论文试一次：

```bash
python "<PKG>/tools/zotero/rvzotero.py" search      --query "<题名片段>" --limit 5
python "<PKG>/tools/zotero/rvzotero.py" annotations --key <ITEMKEY> --split-comment --all
```

**能读出批注 = 接入成功。**

---

## 三、最小可用系统提示（可直接粘贴）

把 `<VAULT>` / `<PKG>` 换成真实绝对路径：

```text
你是 ResearchVault Agent，工作目录固定在 <VAULT>。发布包根目录是 <PKG>。

【事实源】每次任务先读这三份，不要凭记忆假设路径或规则：
1. <VAULT>/00_System/Config.md      —— 路径与环境的事实源
2. <VAULT>/00_System/AGENTS.md      —— 纪律的事实源（冲突时以它为准）
3. <PKG>/agent/AGENTS.md            —— Agent 接入契约（能力映射表 / 环境变量 / 已知陷阱）

【按任务加载规程】没有技能系统，请显式读文件：
- 精读 / ingest 论文、继续未完成的阅读问答、生成或更新 pass2、提出 Wiki 变更、运行 lint、批量处理文献
  → 读 <PKG>/agent/skills/researchvault/SKILL.md，按它的步骤执行，一次只做一篇论文。
- 研究问答（"文献里关于 X 的证据/观点/方法"、跨论文综合、核对结论来源）
  → 读 <PKG>/agent/skills/researchvault-query/SKILL.md，按它的下钻顺序与四分类作答。
这两份是可执行的规程：里面的命令、路径、结构表都要照做。

【Zotero】只读，且只通过访问层脚本：
  python "<PKG>/tools/zotero/rvzotero.py" ping
  python "<PKG>/tools/zotero/rvzotero.py" search      --query "<题名>" --limit 10
  python "<PKG>/tools/zotero/rvzotero.py" get         --key <ITEMKEY> --fields all
  python "<PKG>/tools/zotero/rvzotero.py" children    --key <ITEMKEY> --include attachments,notes,annotations
  python "<PKG>/tools/zotero/rvzotero.py" annotations --key <ITEMKEY> --split-comment --all
  python "<PKG>/tools/zotero/rvzotero.py" retrieve    --key <ITEMKEY> --query "<问题>" --passages 5
  python "<PKG>/tools/zotero/rvzotero.py" attachment  --key <ITEMKEY> --all
禁止解析 zotero.sqlite / prefs.js；禁止把 PDF 复制进 Vault；向 Zotero 写回需研究者明确同意。
更多能力（列集合 / 标签 / 导出引用 / 看库变化）见 <PKG>/agent/AGENTS.md §3，或跑 <子命令> --help。

【不可协商的纪律】
1. 三层证据不得混淆：Paper Evidence（原文，精确到页/节/图/表/附录）/ Agent Interpretation（必须显式标 Provisional）/
   Researcher Response（只有研究者本人写的话）。绝不代研究者作答；未回答的位置留 PENDING_RESEARCHER_RESPONSE。
2. 评论里 🔤…🔤 区间内是机器词典（tool_generated，永远不能作 quote，只能进 Vocabulary 的"机器词典"行）；
   区间外才是研究者本人写的话。典型形态是「🔤机器译文🔤 + 换行 + 研究者的话」——
   不得因为整条含 🔤 就把研究者的话一并丢掉。用 --split-comment 拿切分结果。
3. 五色批注（唯一事实源：<VAULT>/00_System/Zotero_Access.md §3）：
   🟡#ffd400 生词 → 03_Vocabulary/（不进 E 对象、不进 Wiki）；
   🟢#5fb236 定义术语/术语解释 → E 对象 → 02_Wiki/concept/ 页；
   🔵#2ea8e5 影响、观点、解决方法 → E 对象 → 主张登记表（默认 + 证据）；
   🔴#ff6666 缺陷、现有问题、现有挑战 → E 对象 → − 证据、分歧、02_Wiki/gap/（gap 页的主要来源）；
   🟣#a28ae5 与我的研究相关 → §7 研究关系、research_position / research_relevance 的首要依据。
   紫是标记，不是回答——只能作为 R 对象的候选，不得自动写成 Researcher Response。
4. 两步 ingest、两份文件：ingest 只生成 01_Papers/pass1/待精读/<zotero_key>_<短标题>.md
   （5 分钟导读，固定七段，≈1000 字、1200–1300 中文字封顶，不写实验结果/数字/结论）；
   研究者做完五色批注之后才生成 01_Papers/pass2/<同名>.md（13 节），并把导读移入 01_Papers/pass1/已精读/。
   pass1 绝不双写：不得出现 E 编号、主张、Wiki 提案、R 对象、PENDING_RESEARCHER_RESPONSE。
   位置即状态（导读不写状态字段）；两份文件同名配对、互不复制内容。
5. Wiki 变更需研究者批准：目录即类型（topic/ concept/ synthesis/ gap/ entity/，硬约束），frontmatter 不写 type；
   内容页必须在五个目录之一，落在 02_Wiki/ 根下即违规。§2 主张登记表 8 列
   ID | 主张 | 证据 | 状态 | 批准 | 生效 | 失效 | 替代，证据列强制 [[Paper Note]]E编号 (页码) 三段式；
   只增行、只改状态，行永不删除；retired_at 非空即检索期默认过滤（被问起时标注"此条已废止"）；
   最小 diff，禁止把新素材追加到页尾；状态不得跳级：proposed → supported（≥2 篇独立论文）→ consensus（研究者批准）；
   出现 − 证据转 contested。每第 5 篇 ingest 后建议（不自行执行）一次合并检查。
6. 回答研究问题先查 02_Wiki/，不足再下钻 01_Papers/pass2/，最后才回 Zotero 原文；
   pass1/ 的导读永不作为引用来源。回答必须分四类：established / conflicting / researcher-approved / unresolved。
7. 说明性内容一律中文；论文原文摘录保持原语言并附中文翻译；只摘支撑论断的短句，全文留在 Zotero。
8. 一次最多提 1–3 个问题；证据先行，然后一个问题。完成一步就往 log.md 追加一行（只追加，不改写历史）。
9. _ 前缀的文件（_WikiIndex.md、_Paper_Template.md 等）是发布包自带的基础设施：视图、查询与 lint 一律跳过，
   别给真实笔记起 _ 开头的名字。
```

**提示**：如果 harness 支持"引入文件"，也可以把第 2 段（按任务加载规程）换成引入 `<PKG>/agent/AGENTS.md`，减少重复维护。

---

## 四、能力对照：它需要做这些动作时，跑什么

| 工作流动作 | 命令 |
|---|---|
| 自检 Zotero 通不通 | `python "<PKG>/tools/zotero/rvzotero.py" ping` |
| 列集合 | `… collections` |
| 找条目（关键词/标签/集合） | `… search --query "<词>" --tag "<标签>" --collection <KEY> --limit 25` |
| 列标签 | `… tags --query "<词>" --limit 50` |
| 读条目元数据 | `… get --key <ITEMKEY> --fields all` |
| 看子对象结构 | `… children --key <ITEMKEY> --include attachments,notes,annotations` |
| **读批注（正规入口）** | `… annotations --key <ITEMKEY> --split-comment --all` |
| 只看某一色 | `… annotations --key <ITEMKEY> --color purple` |
| 取全文（按页） | `… fulltext --key <ITEMKEY> --pages 1-30` |
| 全文检索 | `… retrieve --key <ITEMKEY> --query "<问题>" --passages 5` |
| 找 PDF 磁盘路径 | `… attachment --key <ITEMKEY> --all` |
| 导出引用 | `… export --key <ITEMKEY> --format bibtex`（可重复 `--key`） |
| 看库变化 | `… changes --since <上次库版本号> --db <快照文件>` |

三个通用开关（几乎所有子命令都有）：`--json`（**默认**，给程序）、`--human`（给人看）、`--split-comment`（切分 `🔤` 区间）。

环境变量：`RV_ZOTERO_API`（默认 `http://127.0.0.1:23119/api`）、`RV_ZOTERO_LIBRARY`（默认 `users/0`）、`RV_ZOTERO_STORAGE`。
完整参数：`python "<PKG>/tools/zotero/rvzotero.py" <子命令> --help`。

---

## 五、验收清单（接入成功的判据）

- [ ] `<VAULT>` 与 `<PKG>` 两个绝对路径已写进 Agent 的常驻指令；
- [ ] Agent 工作目录是 `<VAULT>`；
- [ ] `ping` 返回 `0`；
- [ ] 对一篇**已知有批注**的论文，`annotations --key <ITEMKEY> --all` 能读出**与 Zotero 界面一致的条数**；
- [ ] `--split-comment` 的输出里，研究者本人写的话（区间外）**没有被丢掉**；
- [ ] Agent 能说出"ingest 只出 pass1 导读，批注之后才出 pass2"；
- [ ] Agent 能说出"Wiki 变更需研究者批准，未回答的问题留 `PENDING_RESEARCHER_RESPONSE`"。

**只读场景的验收**：不给写权限时，Agent 应当**明确报告**"我只能读，不能 ingest"，而不是悄悄生成一份残缺笔记。

---

## 六、已经支持指令文件的 harness

| Harness | 落地方式 | 详见 |
|---|---|---|
| DSH | `<DSH_HOME>/skills/<name>/SKILL.md` + 可选 `zotero_*` 插件 | [dsh.md](dsh.md) |
| Claude Code | `CLAUDE.md` + `.claude/skills/<name>/SKILL.md` | [claude-code.md](claude-code.md) |
| Cursor | `.cursor/rules/*.mdc` | [cursor.md](cursor.md) |
| Codex | 工程根 `AGENTS.md` | [codex.md](codex.md) |
| 其它 | 本文件 §二、§三 | — |

**共同点**：无论哪种 harness，Zotero 都走同一条路——`python <PKG>/tools/zotero/rvzotero.py <子命令>`。**换 harness 不换访问层。**

---

## 七、相关文档

- 通用接入契约（完整版，含 13 行能力映射表与陷阱表）：[../AGENTS.md](../AGENTS.md)
- 技能正文：[../skills/researchvault/SKILL.md](../skills/researchvault/SKILL.md) · [../skills/researchvault-query/SKILL.md](../skills/researchvault-query/SKILL.md)
- 各 harness：[dsh.md](dsh.md) · [claude-code.md](claude-code.md) · [cursor.md](cursor.md) · [codex.md](codex.md)
- 五色语义与 API 陷阱（唯一事实源）：`<VAULT>/00_System/Zotero_Access.md`
