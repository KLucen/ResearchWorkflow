---
title: Cursor 接入
scope: agent/adapters
---

# Cursor 接入

> 结论先给：Cursor 没有 `zotero_*` 工具，Zotero 读取**全部走** `tools/zotero/rvzotero.py`（终端里跑 Python），**不需要任何插件**。
> 接入方式是把契约与两份技能正文转成 **`.cursor/rules/*.mdc`**（Project Rules）。
>
> **通用接入契约**：[../AGENTS.md](../AGENTS.md)（先读它）。**五色语义**：`<VAULT>/00_System/Zotero_Access.md`（唯一事实源）。

---

## 一、先记住一件事：`.mdc`，不是 `.md`

- Project Rules 放在**工程根**的 `.cursor/rules/` 下，扩展名必须是 **`.mdc`**。
- **放在 `.cursor/rules/` 里的普通 `.md` 会被直接忽略**——这是最常见的"我明明写了规则但 Cursor 不理会"的原因。
- `.mdc` 的头部是 **YAML frontmatter**，三个字段决定这条规则**什么时候进上下文**：

| frontmatter | 何时被加载 |
|---|---|
| `alwaysApply: true` | **总是**进上下文（适合短契约） |
| `globs: <通配>`（且 `alwaysApply: false`） | 当上下文里出现**匹配的文件**时自动挂上 |
| 只有 `description`（`alwaysApply: false`、无 `globs`） | Agent 认为相关时**自己拉取** |
| 三者都没有 | 只有你手动 `@规则名` 才进上下文 |

**据此拆分**：短契约用 `alwaysApply`，长规程（技能正文）用 `description` 让 Agent 按需拉取，路径相关的细则用 `globs`。

---

## 二、装什么、装到哪

| 文件 | 内容来源 | frontmatter 策略 |
|---|---|---|
| `<工程根>/.cursor/rules/researchvault-contract.mdc` | 手写（§三） | `alwaysApply: true` |
| `<工程根>/.cursor/rules/researchvault-ingest.mdc` | `<PKG>/agent/skills/researchvault/SKILL.md` 的**正文** | 只给 `description` |
| `<工程根>/.cursor/rules/researchvault-query.mdc` | `<PKG>/agent/skills/researchvault-query/SKILL.md` 的**正文** | 只给 `description` |
| `<工程根>/.cursor/rules/pass2-notes.mdc` | 手写（§四·3） | `globs` 指向笔记路径 |

**工程根就是 `<VAULT>`**（笔记、Wiki 都在工程内）。若你想把规则做成"所有工程通用"，用 Cursor 的 **User Rules**（设置里粘贴，纯文本、无 frontmatter），做法见 §六。

### 安装命令（bash）

```bash
cd "<VAULT>"
mkdir -p .cursor/rules

# 1) 短契约：自己写（内容见 §三）
# 2) 长规程：把 SKILL.md 的正文搬过来，frontmatter 换成 MDC 的
awk 'f{print} /^---$/{n++; if(n==2) f=1}' "<PKG>/agent/skills/researchvault/SKILL.md" > /tmp/ingest.body.md
awk 'f{print} /^---$/{n++; if(n==2) f=1}' "<PKG>/agent/skills/researchvault-query/SKILL.md" > /tmp/query.body.md
```

（`awk` 那两行只是**去掉 YAML frontmatter、留下正文**；你也可以手工复制正文。）

### 安装命令（PowerShell）

```powershell
Set-Location "<VAULT>"
New-Item -ItemType Directory -Force -Path ".cursor\rules" | Out-Null

# 去 frontmatter、留正文，写成 UTF-8（无 BOM）
function Get-Body($p) {
  $lines = Get-Content -LiteralPath $p -Encoding UTF8
  $dash = 0; $out = @()
  foreach ($l in $lines) {
    if ($l -eq '---') { $dash++; continue }
    if ($dash -ge 2) { $out += $l }
  }
  $out -join "`n"
}
Get-Body "<PKG>\agent\skills\researchvault\SKILL.md"       | Set-Content -Encoding UTF8 ".cursor\rules\researchvault-ingest.mdc.body"
Get-Body "<PKG>\agent\skills\researchvault-query\SKILL.md" | Set-Content -Encoding UTF8 ".cursor\rules\researchvault-query.mdc.body"
```

然后在这两个 `.body` 文件**顶部补上 §四·2 的 frontmatter**，文件名改成 `researchvault-ingest.mdc` / `researchvault-query.mdc`。

---

## 三、短契约：`researchvault-contract.mdc`

**这就是"任何 Agent 进入这套工作流的统一入口"在 Cursor 上的落地**——必须 `alwaysApply: true`，且**保持短**（它每次都在上下文里）。

```markdown
---
description: ResearchVault 工作流的不可协商纪律（三层证据 / 五色批注 / 两步 ingest / Wiki 闸门）
alwaysApply: true
---

# ResearchVault 纪律契约

本工程是 ResearchVault（Obsidian 知识库 + Zotero 不可变源）。执行任何文献任务前：

1. **先读三份事实源**：
   - `<VAULT>/00_System/Config.md` —— 路径、映射、当前状态（**路径一律从这里读，不要凭记忆假设**）
   - `<VAULT>/00_System/AGENTS.md` —— 纪律（冲突时**纪律以它为准**）
   - `<PKG>/agent/AGENTS.md` —— Agent 接入契约（能力映射 + 纪律契约 + 检查清单）
2. **Zotero 只读，且只通过** `<PKG>/tools/zotero/rvzotero.py <子命令>`。
   禁止解析 `zotero.sqlite` / `prefs.js`；禁止把 PDF 复制进 Vault；向 Zotero 写回需研究者明确同意。
3. **三层证据不得混淆**：Paper Evidence（原文 + 精确到页/节/图/表）/ Agent Interpretation (**Provisional**) / Researcher Response（只有研究者本人的话）。
   **不得代研究者作答**；未回答的位置留 `PENDING_RESEARCHER_RESPONSE`。
4. **`🔤…🔤` 区间内是机器词典**（`tool_generated`，**永远不能作 `quote`**）；**区间外才是研究者本人的话**。
   典型形态是「`🔤机器译文🔤` + 换行 + 研究者的话」——**不得因为整条含 `🔤` 就把研究者的话一并丢掉**。
5. **五色批注**（语义唯一事实源：`<VAULT>/00_System/Zotero_Access.md`）：
   🟡`#ffd400` 生词→`03_Vocabulary/`（不进 E 对象、不进 Wiki）；
   🟢`#5fb236` 定义术语→E 对象→`concept` 页；
   🔵`#2ea8e5` 影响/观点/解决方法→E 对象→主张登记表（默认 `+`）；
   🔴`#ff6666` 缺陷/现有问题/挑战→E 对象→`−` 证据、分歧、`gap/`（`gap/` 页的主要来源）；
   🟣`#a28ae5` 与我的研究相关→研究关系字段——**紫是标记，不是回答**，只能作 `R` 候选。
6. **两步 ingest**：ingest 只出 `<VAULT>/01_Papers/pass1/待精读/<zotero_key>_<短标题>.md` 的 5 分钟导读；
   **研究者做完五色批注之后**才出 `01_Papers/pass2/<同名>.md`，并把导读移入 `pass1/已精读/`。
   **`pass1/` 绝不双写**：不得出现 `E` 编号、主张、Wiki 提案、`R` 对象、`PENDING_RESEARCHER_RESPONSE`。
   **位置即状态**（不写状态字段）；两份文件同名配对、互不复制内容。
7. **Wiki 变更需研究者批准**：目录即类型（`topic/` `concept/` `synthesis/` `gap/` `entity/`），
   frontmatter **不写 `type`**；§2 主张登记表 8 列、证据列强制 `[[Paper Note]]E编号 (页码)` 三段式；
   只增行、只改状态，行永不删除；`retired_at` 非空检索期默认过滤；最小 diff，禁止往页尾追加。
8. **回答研究问题先 `02_Wiki/`**，不足再下钻 `01_Papers/pass2/`，最后才回 Zotero 原文；
   回答分四类：established / conflicting / researcher-approved / unresolved。
9. 说明性内容**一律中文**；论文原文摘录保持原语言并附中文翻译。
```

把 `<VAULT>` / `<PKG>` 换成真实绝对路径。

---

## 四、长规程：两个 `.mdc`

### 1. `researchvault-ingest.mdc`

```markdown
---
description: ResearchVault 的 ingest 与 pass2 成稿规程。当用户要求精读/ingest 一篇 Zotero 论文、继续未完成的阅读问答、生成或更新 pass2 精读总结、提出 Wiki 变更、运行 lint、批量处理文献时使用。含完整命令序列与七段导读结构。
alwaysApply: false
---

<!-- 下面粘贴 <PKG>/agent/skills/researchvault/SKILL.md 的正文（不含原 frontmatter） -->
```

### 2. `researchvault-query.mdc`

```markdown
---
description: ResearchVault 的研究问答规程。当用户问"文献中关于 X 的证据/观点/方法"、要跨论文综合、核对某结论来源，或要求 lint 时使用。含 02_Wiki → 01_Papers/pass2 → Zotero 的下钻顺序与四分类回答要求。
alwaysApply: false
---

<!-- 下面粘贴 <PKG>/agent/skills/researchvault-query/SKILL.md 的正文（不含原 frontmatter） -->
```

**只给 `description`** = 让 Cursor 在你问到相关事情时自己把这条拉进上下文，平时不占预算。

### 3. `pass2-notes.mdc`（可选，演示 `globs` 的用法）

```markdown
---
description: 写 pass2 精读总结时的结构与纪律
globs: 01_Papers/pass2/**/*.md
alwaysApply: false
---

- `schema_version: 3`、`type: paper`；13 个固定小节（§0 阅读轮次 … §12 相关论文）。
- **受批注影响的段落用 `==…==` 包住**（一眼看出"这段来自批注"）。
- 批注转成 `E` 对象写入 §8；`source: annotation:绿|蓝|红|紫`。
- 观点/证据/页码缺一不可：`E` 编号 + `quote`（原文原语言）+ `quote_zh` + `location`（页/节/图/表）。
- 提问 1–3 个，**不得编造研究者的回答**；未回答留 `PENDING_RESEARCHER_RESPONSE`。
- 主张影响检查写进 §11；改动实质研究论断前**先请批准**。
- `pass1/` 的任何内容都不得复制进来。
```

只有当你**正在动 `01_Papers/pass2/` 下的文件**时，这条才进上下文。

---

## 五、Zotero 怎么读（终端命令）

Cursor 的 Agent 通过终端跑命令即可；`rvzotero.py` 只用 Python 标准库。

```bash
python "<PKG>/tools/zotero/rvzotero.py" ping                                    # 0 = 通
python "<PKG>/tools/zotero/rvzotero.py" search --query "<题名片段>" --limit 10
python "<PKG>/tools/zotero/rvzotero.py" children   --key <ITEMKEY> --include attachments,notes,annotations
python "<PKG>/tools/zotero/rvzotero.py" annotations --key <ITEMKEY> --split-comment --all
python "<PKG>/tools/zotero/rvzotero.py" retrieve   --key <ITEMKEY> --query "<问题>" --passages 5
python "<PKG>/tools/zotero/rvzotero.py" fulltext   --key <ITEMKEY> --pages 1-30
python "<PKG>/tools/zotero/rvzotero.py" attachment --key <ITEMKEY> --all
```

**注意**：

- Cursor 里默认终端可能是 **PowerShell**（Windows）。**不要**用 `Invoke-RestMethod` 直连 Local API——它回 HTTP/1.0，会在握手阶段失败；要么用脚本，要么切到 `bash` / `curl.exe`。
- 若 Agent 每次跑命令都要你确认，把 `python` 加进 Cursor 的命令白名单（设置里的命令/终端允许列表，**具体项名以你所用版本为准**）。
- `search --limit` 上限 100，翻页用 `--offset`；`annotations` **默认就取全部命中**（自动翻完所有分页并校验总数），`--all` 只是把意图写明白。

---

## 六、不想建文件？两个更省事的替代

1. **`AGENTS.md`**：Cursor 也支持在工程根放 `AGENTS.md`。把 §三的短契约整段粘进 `<VAULT>/AGENTS.md` 即可（**注意**：`<VAULT>` 是**你的**知识库，这个文件由你创建；发布包里 `template/00_System/AGENTS.md` 是**纪律事实源**，两者不是同一个文件，不要混淆）。
2. **User Rules**：Cursor 设置里的 User Rules 是**纯文本**，没有 frontmatter，对所有工程生效。适合放 §三的短契约（把 `<VAULT>` 写成你自己的绝对路径）。**长规程不要放这里**——它会一直占上下文。

---

## 七、这一侧最容易踩的坑

1. **规则写成 `.md`** → 被忽略。必须 `.mdc`。
2. **`globs` 路径基准搞错**：`globs` 相对**工程根**（也就是 `<VAULT>`），所以要写 `01_Papers/pass2/**/*.md`，**不要**写成 `.cursor/...` 或绝对路径。
3. **长规程用了 `alwaysApply: true`** → 每次对话都灌进几百行，把预算吃光。长规程**只给 `description`**。
4. **`--include` 只认复数**：`get` 与 `children` **都**用复数（`notes` / `attachments` / `annotations`）；写单数会报**参数错误**（退出码 `2`），不是静默少返回。**旧版本**的 `children --help` 曾把取值印成单数（只看帮助会被带偏），**已修正**：实现与帮助文本现在都只认复数，并有回归测试锁死。
5. **批注只挂在某一份 PDF 上**：先 `children` 看结构，`annotations --key` 默认聚合全部附件，别只查第一个。
6. **把评论里的机器词典当成研究者的话**（或整条丢掉）：按 `🔤…🔤` 区间切分，用 `--split-comment`。

---

## 八、相关文档

- 通用接入契约：[../AGENTS.md](../AGENTS.md)
- 技能正文：[../skills/researchvault/SKILL.md](../skills/researchvault/SKILL.md) · [../skills/researchvault-query/SKILL.md](../skills/researchvault-query/SKILL.md)
- 其它 harness：[dsh.md](dsh.md) · [claude-code.md](claude-code.md) · [codex.md](codex.md) · [generic.md](generic.md)
- 五色语义与 API 陷阱（唯一事实源）：`<VAULT>/00_System/Zotero_Access.md`
- 完整参数：`python <PKG>/tools/zotero/rvzotero.py <子命令> --help`
