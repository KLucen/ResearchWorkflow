---
title: Claude Code 接入
scope: agent/adapters
---

# Claude Code 接入

> 结论先给：Claude Code **没有** `zotero_*` 这类 Zotero 工具，所以它**天然**就走发布包自带的只读访问层 `tools/zotero/rvzotero.py`——**不需要装任何插件**，只需要 Bash 工具 + Python。
>
> **通用接入契约**：[../AGENTS.md](../AGENTS.md)（先读它）。**五色语义**：`<VAULT>/00_System/Zotero_Access.md`（唯一事实源）。

---

## 一、装什么、装到哪

Claude Code 的**技能**是目录 + `SKILL.md`：

| 装到哪 | 生效范围 | 路径 |
|---|---|---|
| 项目级（推荐） | 只在这个工程里生效 | `<工程根>/.claude/skills/researchvault/SKILL.md` |
| 用户级 | 你所有工程都生效 | `~/.claude/skills/researchvault/SKILL.md` |

**文件名必须是 `SKILL.md`（全大写）**；**目录名必须与 frontmatter 的 `name` 一致**（`researchvault` / `researchvault-query`）。

```bash
# 项目级：在 <VAULT> 里建（<VAULT> 作为工程根，见 §四）
cd "<VAULT>"
mkdir -p .claude/skills/researchvault .claude/skills/researchvault-query
cp "<PKG>/agent/skills/researchvault/SKILL.md"       .claude/skills/researchvault/SKILL.md
cp "<PKG>/agent/skills/researchvault-query/SKILL.md" .claude/skills/researchvault-query/SKILL.md
```

```powershell
# PowerShell 等价写法
Set-Location "<VAULT>"
New-Item -ItemType Directory -Force -Path ".claude\skills\researchvault",".claude\skills\researchvault-query" | Out-Null
Copy-Item "<PKG>\agent\skills\researchvault\SKILL.md"       ".claude\skills\researchvault\SKILL.md" -Force
Copy-Item "<PKG>\agent\skills\researchvault-query\SKILL.md" ".claude\skills\researchvault-query\SKILL.md" -Force
```

### frontmatter 示例（Claude Code 可识别的字段）

```yaml
---
name: researchvault
description: ResearchVault 科研工作流。精读或 ingest 论文、继续未完成的阅读问答、提出或批准 Wiki 变更、运行 lint、批量处理 Zotero 文献时使用。
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
disable-model-invocation: false
---
```

要点：

- `name` **必填**，且**必须等于目录名**；只允许小写字母、数字、连字符（`researchvault-query` 合法）。
- `description` **强烈建议写全**——它是 Agent 判断"要不要加载这个技能"的唯一依据，把触发场景写进去（上面这行就是可直接用的版本，长度在 1024 字符以内）。
- `allowed-tools` 是**逗号分隔的字符串**，不是 YAML 数组。Zotero 读取必须给 `Bash`（要跑 `rvzotero.py`）。
- `disable-model-invocation: false` 表示允许模型自动加载；设 `true` 就只能由你用 `/researchvault` 手动调用。

---

## 二、让 Agent 一进来就知道规矩：`CLAUDE.md`

Claude Code 会**自动读工程根目录的 `CLAUDE.md`**。把契约写进去，Agent 不需要你每次提醒：

```markdown
# CLAUDE.md

本工程是 ResearchVault。执行任何文献任务前：

1. 读 `<VAULT>/00_System/Config.md`（路径与环境事实源）与 `<VAULT>/00_System/AGENTS.md`（纪律事实源）。
2. 读 Agent 接入契约：`<PKG>/agent/AGENTS.md`。
3. Zotero 一律只读，且**只**通过 `<PKG>/tools/zotero/rvzotero.py <子命令>` 访问；
   禁止解析 `zotero.sqlite` / `prefs.js`，禁止把 PDF 复制进 Vault。
4. 三层证据不得混淆：Paper Evidence / Agent Interpretation (Provisional) / Researcher Response。
   **不得代研究者作答**；未回答的位置留 `PENDING_RESEARCHER_RESPONSE`。
5. 论文笔记的生成顺序是**两步**：ingest 只出 5 分钟导读，研究者做完五色批注后才出 `pass2/`。
   `pass1/` 绝不双写（不得出现 `E` 编号、主张、Wiki 提案、`R` 对象）。
6. Wiki 变更需研究者批准；`🔤…🔤` 区间内是机器词典，永不作 `quote`。
```

`<PKG>` / `<VAULT>` 换成你的真实绝对路径。若你的版本支持 `@` 引入语法，也可以把第 2 条换成一行引入；**不支持就直接写绝对路径**，同样有效。

（把这段放进 `CLAUDE.md` 是**你自己工程里的运行时动作**，发布包不替你写这个文件。）

---

## 三、Zotero 怎么读：全部走 `rvzotero.py`

Claude Code 这一侧**没有** `zotero_*` 工具，因此不存在"插件还是脚本"的选择题——**只有脚本这一条路**，也就没有 DSH 上那类"工具静默返回 0 条批注"的问题。

```bash
# 0) 自检（退出码 0 才继续）
python "<PKG>/tools/zotero/rvzotero.py" ping

# 1) 找条目
python "<PKG>/tools/zotero/rvzotero.py" search --query "<题名或关键词>" --limit 10

# 2) 结构与附件（看清批注挂在哪份 PDF 上）
python "<PKG>/tools/zotero/rvzotero.py" children --key <ITEMKEY> --include attachments,notes,annotations

# 3) 读批注（正规入口；--all 会翻页并校验总数）
python "<PKG>/tools/zotero/rvzotero.py" annotations --key <ITEMKEY> --split-comment --all

# 4) 取全文 / 全文检索
python "<PKG>/tools/zotero/rvzotero.py" fulltext --key <ITEMKEY> --pages 1-30
python "<PKG>/tools/zotero/rvzotero.py" retrieve --key <ITEMKEY> --query "<问题>" --passages 5

# 5) PDF 磁盘路径
python "<PKG>/tools/zotero/rvzotero.py" attachment --key <ITEMKEY> --all
```

**建议放行命令**：在 `.claude/settings.json` 里为 `python` 与只读查看类命令加白名单（规则形如 `Bash(python:*)`；**具体规则语法以你所用版本的文档为准**），否则每次调用都要你点确认。

**并把 `cd` 固定到 `<VAULT>`**——脚本会读 Vault 里的笔记，Agent 也要写 `pass1/` `pass2/`，工作目录不对会写到工程外。

---

## 四、把工程根设在 `<VAULT>`

Claude Code 的文件工具以**工程根**为参照。把 `<VAULT>` 作为工程根打开（`cd <VAULT> && claude`），理由：

- 笔记、Wiki、词条都在工程内，读写不需要反复授权；
- `<PKG>` 用**绝对路径**引用即可（脚本本身可以在任意位置）；
- 想同时改发布包时，再单独开一个 `<PKG>` 的会话，**不要**把两者混在一个工程里改。

---

## 五、可选：登记一个子代理

如果你希望"精读"这件事有独立的上下文预算，可以在 `.claude/agents/researchvault.md` 建一个子代理：

```markdown
---
name: researchvault
description: 按 ResearchVault 规程做单篇论文的 ingest / pass2 成稿；当需要专门处理一篇论文的完整精读流程时使用。
tools: Read, Write, Edit, Glob, Grep, Bash
---

先读 `<PKG>/agent/AGENTS.md` 与 `<VAULT>/00_System/Config.md`、`AGENTS.md`，然后按
`<PKG>/agent/skills/researchvault/SKILL.md` 的规程执行。一次只做一篇论文。
Zotero 只读，且只通过 `<PKG>/tools/zotero/rvzotero.py` 访问。
```

注意 `tools` 这一行是**逗号分隔的字符串**（不是 YAML 数组）——写成数组会解析失败。

---

## 六、这一侧最容易踩的坑

1. **工作目录不在 `<VAULT>`** → 笔记写到别处，或读不到 `00_System/`。开工第一件事 `pwd`。
2. **`--include` 只认复数**：`get` 与 `children` **都**用复数（`notes` / `attachments` / `annotations`）；写单数会报**参数错误**（退出码 `2`），不是静默少返回。**旧版本**的 `children --help` 曾把取值印成单数（只看帮助会被带偏），**已修正**：实现与帮助文本现在都只认复数，并有回归测试锁死。
3. **批注可能只挂在某一份 PDF 上**——一篇论文常有原文 / 双语 / 译文多份附件，先 `children` 看结构，再用 `annotations --key` 聚合全部附件。
4. **把评论里的机器词典当成研究者的话**（或整条丢掉）：`annotationComment` 常见形态是「`🔤机器译文🔤` + 换行 + 研究者自己写的话」，要**按 `🔤…🔤` 区间切分**；用 `--split-comment` 让脚本替你切。
5. **PowerShell 直连 Local API 会失败**：Local API 回 HTTP/1.0，`Invoke-RestMethod` 在握手阶段就挂。**用脚本**（或 `curl.exe`）。
6. **`search --limit` 上限 100**，翻页用 `--offset`；`annotations` **默认就取全部命中**（自动翻完所有分页并校验总数），`--all` 只是把意图写明白。

---

## 七、相关文档

- 通用接入契约：[../AGENTS.md](../AGENTS.md)
- 技能正文：[../skills/researchvault/SKILL.md](../skills/researchvault/SKILL.md) · [../skills/researchvault-query/SKILL.md](../skills/researchvault-query/SKILL.md)
- DSH 侧的 `zotero_*` 对照表（本 harness 用不到，但排查差异时有用）：[dsh.md](dsh.md)
- 其它 harness：[cursor.md](cursor.md) · [codex.md](codex.md) · [generic.md](generic.md)
- 五色语义与 API 陷阱（唯一事实源）：`<VAULT>/00_System/Zotero_Access.md`
- 完整参数：`python <PKG>/tools/zotero/rvzotero.py <子命令> --help`
