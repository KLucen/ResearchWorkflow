# 接入任意 Agent

> **一句话结论**：这套工作流不绑定任何 Agent 实现。你的 Agent 只要能**读文件、写文件、跑 shell 命令**，就能跑整套流程。
> 三种接入方式任选；Zotero 一律通过 `tools/zotero/rvzotero.py` 访问，不依赖任何专有工具。

## 结论先行

| 接入方式 | 适合谁 | 成本 | 持久性 |
|---|---|---|---|
| **A. 把 `agent/AGENTS.md` 放进项目根** | 所有 Agent | 复制一个文件 | 每次会话自动生效 |
| **B. 装成 skill** | 支持 skill / 斜杠命令的 harness | 复制一个目录 | 按需加载，省 token |
| **C. 直接贴提示词** | 临时试用 / 一次性任务 | 粘贴一段话 | 只对当前会话生效 |

**推荐顺序：A → B → C。** 方式 A 是最小公倍数，先跑通它；用熟了再考虑 B。

---

# 一、Agent 必须具备的三种能力

| 能力 | 用来做什么 | 缺了会怎样 |
|---|---|---|
| **读文件** | 读 `agent/AGENTS.md`、`00_System/*.md` 规范、已有的 Paper Note 与 Wiki 页 | 完全跑不动 |
| **写文件** | 生成导读、Paper Note、Wiki 页、Vocabulary 词条、追加 `log.md` | 只能问答，不能 ingest |
| **跑 shell 命令** | 调 `python tools/zotero/rvzotero.py <子命令>` 读 Zotero | 读不到原文与批注 |

### 不需要什么

- ❌ **不需要联网**（Zotero 是本地 API，工具是纯标准库）
- ❌ **不需要专用 Zotero 插件**——这是本工作流与"插件方案"最大的区别，理由见 [07-faq.md](07-faq.md)
- ❌ **不需要向量库 / 数据库 / 第三方包**（只用 Python 3.8+ 标准库）
- ❌ **不需要 Agent 支持函数调用**——它只要能跑 shell，就能调脚本

### 必须装的东西（就三个）

| 组件 | 作用 |
|---|---|
| **Obsidian** | 人读 Vault 的界面（Agent 不依赖它，但你需要它看 Dataview 视图） |
| **Zotero** | 论文原文 + 批注的**不可变源** |
| **Python 3.8+** | 跑 `tools/zotero/rvzotero.py` |

---

# 二、接入时要给 Agent 两样东西

| 给什么 | 在哪 | 作用 |
|---|---|---|
| **行为契约** | 仓库根的 `agent/AGENTS.md` | 告诉 Agent：它是谁、三层证据纪律、什么绝对不能做、流程怎么走 |
| **项目事实** | 你 Vault 里的 `00_System/`（尤其 `Config.md`） | 告诉 Agent：路径在哪、集合怎么映射、体例参数是什么 |

**契约管"该怎么做"，Config 管"你的环境长什么样"。** 两者都要给——只给契约，Agent 不知道你的路径；只给 Config，Agent 不知道纪律。

最简启动语（方式 A 装好之后）：

```text
请先读 agent/AGENTS.md 和 00_System/Config.md，然后按它们工作。
```

---

# 三、三种接入方式

## 方式 A · 把 `agent/AGENTS.md` 放进项目根（推荐）

**做法**：把仓库里的 `agent/AGENTS.md` 复制到你工作目录的根，或者直接把它所在的目录作为工作目录。

```text
你的工作目录/
├── AGENTS.md          ← 从 agent/AGENTS.md 复制过来
├── MyResearchVault/   ← 从 template/ 复制出来的 Vault
└── tools/
    └── zotero/
        └── rvzotero.py
```

**为什么有效**：多数 Agent 会**自动读取工作目录下的 `AGENTS.md`**（或同名约定文件），无需你每次提醒。

**验证**：开一个新会话，问它：

```text
证据层在哪个目录？pass1 和 pass2 是什么关系？
```

答得出「`01_Papers/pass2/`；pass1 是导读，pass2 是批注之后生成的证据层」，就说明它读到了契约。答不出就手动把文件内容贴给它。

**如果文件名撞了**：有些 harness 用 `CLAUDE.md`、`.cursorrules`、`AGENT.md` 之类的名字。**内容一样，改名即可**——`agent/AGENTS.md` 是纯 Markdown，没有格式耦合。

---

## 方式 B · 装成 skill

**适合**：harness 支持 skill / 斜杠命令 / 按需加载的指令包（只在相关时才把指令塞进上下文，省 token）。

**做法**：把 `agent/skills/` 下的两个目录复制到你的 harness 的技能目录：

| 技能 | 什么时候加载 | 干什么 |
|---|---|---|
| [`agent/skills/researchvault/SKILL.md`](../agent/skills/researchvault/SKILL.md) | 用户要求精读/ingest 论文、继续未完成的阅读问答、提出或批准 Wiki 变更、跑 lint | 走完整 ingest / lint 流程 |
| [`agent/skills/researchvault-query/SKILL.md`](../agent/skills/researchvault-query/SKILL.md) | 用户问「文献里关于 X 的证据/观点/方法」、要跨论文综合、核对某结论来源 | 跨论文问答（四分类回答） |

**两个技能分开是有意的**：读论文是**写**流程（要批注、要批准），问问题是**读**流程（只下钻不动文件）。混在一起会让 Agent 在问答时误改笔记。

**装完还是建议保留方式 A**：skill 负责"什么时候做什么"，`AGENTS.md` 负责"永远不许做什么"（比如不得代答、不得删主张行）。

---

## 方式 C · 直接贴提示词

**适合**：试一下值不值得用；或者你的 Agent 环境不方便放文件。

把下面这段贴进对话（`<VAULT>` 换成你的实际路径）：

```text
你是一个科研文献助手，严格遵守 ResearchVault 工作流。

【先读这些】
- <VAULT>/00_System/AGENTS.md      （纪律：必读，优先于以下所有内容）
- <VAULT>/00_System/Config.md      （配置：路径、集合映射、体例参数）
- <VAULT>/00_System/Workflow.md    （流程：ingest / query / lint）

【铁律】
1. Zotero 是只读的不可变源。读 Zotero 一律通过
   `python tools/zotero/rvzotero.py <子命令>`，不要直接解析 zotero.sqlite。
2. 三层证据不得混淆：论文原文（可引用）、你的推断（必须标为暂定）、
   研究者本人的话（只有他能说）。未回答处保留 PENDING_RESEARCHER_RESPONSE。
3. 你永远不代研究者下结论、不替他批准 Wiki 变更。
4. ingest 分两步：先只出 5 分钟导读（pass1/待精读/），
   等研究者说"批注好了"再生成 pass2/。缺批注就不成稿。
5. `🔤…🔤` 区间内是机器词典，永远不能当论文原文引用；
   区间外才是研究者本人写的话，不得丢弃。
6. Wiki 主张表的行永不删除，只流转状态。变更需研究者批准。

【现在开始】
先读上面三个文件，然后用一句话复述你理解的 ingest 两步流程，等我确认。
```

> 贴提示词的**缺点**：上下文一变长就可能被冲淡；换会话要重贴。所以只建议试用。

---

# 四、各 harness 适配

| Harness | 适配说明 |
|---|---|
| **DSH** | [agent/adapters/dsh.md](../agent/adapters/dsh.md) |
| **Claude Code** | [agent/adapters/claude-code.md](../agent/adapters/claude-code.md) |
| **Cursor** | [agent/adapters/cursor.md](../agent/adapters/cursor.md) |
| **Codex** | [agent/adapters/codex.md](../agent/adapters/codex.md) |
| **其他 / 自建** | [agent/adapters/generic.md](../agent/adapters/generic.md) |

每个适配文件只讲三件事：**契约文件放哪、技能装哪、`rvzotero.py` 怎么调**。

**没有你的 harness？** 读 [agent/adapters/generic.md](../agent/adapters/generic.md)——它就是"任何 Agent"的默认答案，本质只有上一节的三条能力要求。

---

# 五、工具无关性：Zotero 只有一条路径

这是本工作流刻意做的设计。**规范文档里出现的永远是同一句话**：

```bash
python tools/zotero/rvzotero.py <子命令>
```

| 你要做的事 | 子命令 |
|---|---|
| 探活、看库 id | `ping` |
| 检索条目 | `search --query "<词>" [--limit N]` |
| 取条目详情（元数据 / 笔记 / 附件） | `get --key <key> --include notes,attachments,annotations` |
| 列子对象 | `children --key <key>` |
| **取批注（含分页与逐附件）** | `annotations --key <key>`（**默认即全量**；`--limit N` 只用于预览） |
| 找证据片段 | `retrieve --key <key> --query "<问题>"` |
| 解析 PDF 磁盘路径 | `attachment --key <key>` |
| 取附件全文 | `fulltext --key <attachment_key> [--out <file>]` |
| 导出引用 | `export --key <key> --format bibtex` |
| 列集合 / 标签 | `collections` / `tags` |
| 库增量 | `changes [--since <version>]` |

上表里凡是 `<key>`，规范写法都是 `--key <key>`（短写 `-k`），与 `--help` 一致。实测：`get` / `children` / `annotations` / `retrieve` / `attachment` / `fulltext` 这六个子命令**额外容忍**把 key 直接写成位置参数（如 `annotations ABCD1234`），但 **`export` 不接受位置参数**（写法错会直接报参数错、退出码 2）。**统一用 `--key`，少一个坑。**

`--human` 给人类可读表格，默认是 JSON。退出码：`0` 成功 / `2` 参数错 / `3` 连不上 Zotero / `4` Zotero 报错 / `5` 未找到。

完整参数与故障排查见 [05-zotero-access.md](05-zotero-access.md) 与 [tools/zotero/README.md](../tools/zotero/README.md)。**使用前跑一次 `--help` 确认参数**，不要凭记忆写。

### 如果你的 harness 自带 Zotero 工具

可以用，但**必须自己处理三个坑**（否则会静默出错）：

| 坑 | 症状 | 你要做的 |
|---|---|---|
| 列子对象时不带 `itemType=annotation` | **批注静默返回 0 条**，不报错 | 走 `rvzotero.py annotations`，或显式加过滤 |
| 批注结果在 100 条处截断 | 读数比实际少，**不报错不给提示** | 走 `rvzotero.py annotations`（默认翻完全部分页 + 逐附件合并） |
| 批注只挂在某一个 PDF 附件上 | 换个附件就查出 0 条 | 走 `rvzotero.py annotations`（自动扫全部附件） |

> **默认就是全量**：`annotations` 不传 `--limit` 时输出**全部**命中（实测 130 条父条目返回 130 条，`truncated: false`）。`--limit N` 是你主动要预览时才用的上限；`--all` 现在只是把「我要全部」写明白的显式开关（无操作）。Zotero 自己的 100 条静默截断由脚本内部翻页解决，不要试图调大 `--page-size`。

**共同结论**：与其在 Agent 侧重复实现这三个坑的规避逻辑，不如让它调 `rvzotero.py`——坑只在一个地方修。这也是"与 Agent 实现无关"的实际含义。

---

# 六、接完做一次自检

让 Agent 回答下面四个问题。答对三个以上才算接好：

| # | 问题 | 期望答案要点 |
|---|---|---|
| 1 | 证据层在哪个目录？`pass1/` 和 `pass2/` 是什么关系？ | `01_Papers/pass2/`；pass1 是导读、pass2 是批注之后生成的证据层 |
| 2 | 你没回答我的问题之前，笔记里该写什么？ | `PENDING_RESEARCHER_RESPONSE`，**不得代答** |
| 3 | 一段带 `🔤…🔤` 的批注评论，哪些能当论文原文引用？ | 都不能。区间内是机器词典；原文取 `annotationText` |
| 4 | 你想改一条 Wiki 主张，下一步做什么？ | 在 `pass2/` §11 提主张级变更表，**等我批准** |

**第 2 题和第 4 题最常答错**——它们正是这套工作流存在的理由。答错了就把对应规范文件再喂一遍。

---

# 七、建议

1. **一次会话只做一件事**：做完一次 ingest 就收，别在同一会话里同时 ingest + 大规模改 Wiki。
2. **用到哪读到哪**：Agent 不必一次吞下全部规范——`AGENTS.md` + `Config.md` 是底线，写 Paper Note 前读 `Paper_Schema.md`，改 Wiki 前读 `Wiki_Schema.md`。
3. **让 Agent 报缺口，不要报结论**：它能说"索引里没找到这段"，不该说"这篇没讨论这个"。
4. **人工确认点别省**：批准 Wiki 变更、批准 `gap/` 升级、标记 `acquired` —— 这三件事省掉，知识库就退化成 Agent 的读书笔记。
5. **换 Agent 不用迁移**：Vault 是纯 Markdown + frontmatter，换任何 Agent 都是重新接入一次契约，笔记本身不用动。

---

## 相关文档

| 文档 | 内容 |
|---|---|
| [01-design.md](01-design.md) | 为什么这样设计 |
| [02-quickstart.md](02-quickstart.md) | 15 分钟跑通 |
| [03-workflow.md](03-workflow.md) | ingest / query / lint 全流程 |
| [04-schemas.md](04-schemas.md) | 字段速查与写权限 |
| [05-zotero-access.md](05-zotero-access.md) | Zotero 访问层与故障排查 |
| [07-faq.md](07-faq.md) | 常见问题 |
| [agent/AGENTS.md](../agent/AGENTS.md) | 通用接入契约（所有 harness 的共同入口） |
