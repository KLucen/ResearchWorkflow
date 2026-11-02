---
title: Codex 接入
scope: agent/adapters
---

# Codex 接入（`AGENTS.md` 约定）

> 结论先给：Codex 没有 `zotero_*` 工具、也**没有技能系统**，所以接入只有两件事：
> ① 在工程根放一份 **`AGENTS.md`**（Codex 会自动读）；② 让 Codex 在需要时去读发布包里的两份 **`SKILL.md`**。
> Zotero 读取**全部走** `tools/zotero/rvzotero.py`，**不需要任何插件**。
>
> **通用接入契约**：[../AGENTS.md](../AGENTS.md)（先读它）。**五色语义**：`<VAULT>/00_System/Zotero_Access.md`（唯一事实源）。

---

## 一、`AGENTS.md` 放哪

| 位置 | 作用 |
|---|---|
| `<工程根>/AGENTS.md` | **主入口**。Codex 在工作目录下会自动加载 |
| 子目录里的 `AGENTS.md` | 进到该子目录工作时再叠加（本工作流**不建议**用——会把 Vault 弄乱） |
| 用户级（如 `~/.codex/AGENTS.md`） | 所有工程通用；适合放"Zotero 只读 + 中文"这类跨项目习惯 |

**工程根就用 `<VAULT>`**，用 `cd` 或 `--cd` 指定（**具体选项名以你所用版本的 `--help` 为准**）：

```bash
cd "<VAULT>"
codex                      # 或： codex --cd "<VAULT>"
```

`<VAULT>/AGENTS.md` 是**你自己的知识库里的文件**，由你创建；发布包不会替你写它。（发布包里 `template/00_System/AGENTS.md` 是**纪律事实源**，内容不同，别混淆。）

---

## 二、装什么、装到哪

Codex 侧**没有安装步骤**——把下面这段写进 `<VAULT>/AGENTS.md` 就算接好了。两份技能正文留在发布包里，`AGENTS.md` 里写明"什么情况下先读哪一份"。

### `<VAULT>/AGENTS.md`（可直接粘贴，替换 `<VAULT>` / `<PKG>`）

```markdown
# ResearchVault —— Agent 操作规程

本工程是 ResearchVault：Obsidian 知识库（`01_Papers/` `02_Wiki/` `03_Vocabulary/`）+ Zotero 作为**不可变源**。

## 0. 开工前必读（每次任务都读，不要凭记忆）

1. `<VAULT>/00_System/Config.md` —— **路径与环境的事实源**（Vault 根、Zotero 数据目录、API 地址、库 ID、Python 要求）。
2. `<VAULT>/00_System/AGENTS.md` —— **纪律的事实源**；冲突时**纪律以它为准**，路径与环境以 `Config.md` 为准。
3. `<PKG>/agent/AGENTS.md` —— Agent 接入契约：能力映射表、环境变量、已知陷阱、开工检查清单。

## 1. 按任务加载规程（Codex 没有技能系统，请显式读取）

- 任务涉及**精读 / ingest 论文、继续未完成的阅读问答、生成或更新 `pass2/`、提出 Wiki 变更、运行 lint、批量处理文献**
  → 先读 `<PKG>/agent/skills/researchvault/SKILL.md`，**按它的步骤执行**，一次只做一篇论文。
- 任务是**研究问答**（"文献里关于 X 的证据/观点/方法"、跨论文综合、核对某结论来源）
  → 先读 `<PKG>/agent/skills/researchvault-query/SKILL.md`，按它的下钻顺序与四分类作答。
- 两份都是**可执行的规程**，不是背景介绍：里面的命令、文件路径、结构表都要照做。

## 2. Zotero：只读，且只通过访问层脚本

```bash
python "<PKG>/tools/zotero/rvzotero.py" ping        # 退出码 0 才继续
python "<PKG>/tools/zotero/rvzotero.py" search      --query "<题名片段>" --limit 10
python "<PKG>/tools/zotero/rvzotero.py" get         --key <ITEMKEY> --fields all
python "<PKG>/tools/zotero/rvzotero.py" children    --key <ITEMKEY> --include attachments,notes,annotations
python "<PKG>/tools/zotero/rvzotero.py" annotations --key <ITEMKEY> --split-comment --all
python "<PKG>/tools/zotero/rvzotero.py" retrieve    --key <ITEMKEY> --query "<问题>" --passages 5
python "<PKG>/tools/zotero/rvzotero.py" attachment  --key <ITEMKEY> --all
```

- **禁止**解析 `zotero.sqlite` / `prefs.js`；**禁止**把 PDF 复制进 Vault；**禁止**向 Zotero 写回（除非研究者明确同意）。
- 需要更多能力（列集合 / 标签 / 导出引用 / 看库变化）时读 `<PKG>/agent/AGENTS.md` §3 的映射表，或跑
  `python "<PKG>/tools/zotero/rvzotero.py" <子命令> --help`。

## 3. 不可协商的纪律

- **三层证据不得混淆**：Paper Evidence（原文，须精确到页/节/图/表/附录）/ Agent Interpretation (**Provisional**，必须显式标注) /
  Researcher Response（**只有研究者本人写的话**）。**坚决不得代研究者作答**；未回答的位置留 `PENDING_RESEARCHER_RESPONSE`。
- **`🔤…🔤` 区间内是机器词典**（`tool_generated`，**永远不能作 `quote`**，只能进 Vocabulary 的"机器词典"行）；
  **区间外才是研究者本人写的话**。典型形态是「`🔤机器译文🔤` + 换行 + 研究者的话」——
  **不得因为整条含 `🔤` 就把研究者的话一并丢掉**。用 `--split-comment` 拿到切分结果。
- **五色批注语义**（唯一事实源：`<VAULT>/00_System/Zotero_Access.md` §3）：
  🟡`#ffd400` 生词 → `03_Vocabulary/`（**不进** E 对象、**不进** Wiki）；
  🟢`#5fb236` 定义术语/术语解释 → `E` 对象 → `02_Wiki/concept/` 页；
  🔵`#2ea8e5` 影响、观点、解决方法 → `E` 对象 → 主张登记表（默认 `+` 证据）；
  🔴`#ff6666` 缺陷、现有问题、现有挑战 → `E` 对象 → `−` 证据、分歧、`02_Wiki/gap/`（**`gap/` 页的主要来源**）；
  🟣`#a28ae5` 与我的研究相关 → §7 研究关系、`research_position` / `research_relevance` 的**首要依据**。
  **紫是标记，不是回答**——只能作为 `R` 对象的候选，**不得**自动写成 Researcher Response。
- **两步 ingest，两份文件**：ingest 只生成
  `01_Papers/pass1/待精读/<zotero_key>_<短标题>.md`（**5 分钟导读**，固定七段，≈1000 字、1200–1300 中文字封顶，
  **不写实验结果/数字/结论**）；**研究者做完五色批注之后**才生成 `01_Papers/pass2/<同名>.md`（13 节），
  并把导读移入 `01_Papers/pass1/已精读/`。
  **`pass1/` 绝不双写**：不得出现 `E` 编号、主张、Wiki 提案、`R` 对象、`PENDING_RESEARCHER_RESPONSE`。
  **位置即状态**——导读**不写状态字段**。两份文件**同名配对、互不复制内容**。
- **Wiki 变更需研究者批准**：目录即类型（`topic/` `concept/` `synthesis/` `gap/` `entity/`，**硬约束，不要临时新增**），
  frontmatter **不写 `type`**（移动文件就是改类型）；内容页必须在五个目录之一，落在 `02_Wiki/` 根下即违规。
  §2 主张登记表 8 列 `ID | 主张 | 证据 | 状态 | 批准 | 生效 | 失效 | 替代`，证据列强制
  `[[Paper Note]]E编号 (页码)` 三段式；**只增行、只改状态，行永不删除**；`retired_at` 非空即**检索期默认过滤**
  （被问起时标注"此条已废止"）；**最小 diff**，**禁止把新素材追加到页尾**；
  状态不得跳级：`proposed → supported`（≥2 篇**独立**论文）`→ consensus`（研究者批准）；
  出现 `−` 证据转 `contested`。每第 5 篇 ingest 后**建议**（**不自行执行**）一次合并检查。
- **回答研究问题**先查 `02_Wiki/`，不足再下钻 `01_Papers/pass2/`，最后才回 Zotero 原文；
  `pass1/` 的导读**永不作为引用来源**。回答必须分四类：
  established / conflicting / researcher-approved / unresolved。
- **`_` 前缀的文件**（`_WikiIndex.md`、`_Paper_Template.md` 等）是发布包自带的基础设施：
  视图、查询与 lint 一律跳过，**别给真实笔记起 `_` 开头的名字**。

## 4. 语言与引文体例

- 说明性内容（分析、解读、提问、Wiki 正文、回复）**一律中文**；**论文原文摘录保持原语言并附中文翻译**。
- 数字、单位、公式、变量名、模型名、数据集名、指标名、引用键**不译**；frontmatter 的**键与枚举值保持英文**。
- 只摘支撑论断的**短句**，不成段复制原文——全文永远留在 Zotero。

## 5. 交互

- 一次最多提 **1–3 个**问题，问那些会实质改变解读或研究相关性的。
- 证据先行，然后一个问题；不要输出长篇泛泛评论。
- 完成一步就更新 `<VAULT>/log.md`（**只追加，不改写历史**）。
```

---

## 三、让 Codex 能写 Vault、能跑 Python

Codex 默认在受限沙箱里跑。这套工作流需要：

1. **读** `<VAULT>` 与 `<PKG>`；**写** `<VAULT>`（笔记、Wiki、`log.md`）；
2. **执行** `python <PKG>/tools/zotero/rvzotero.py`（网络只到本机 `127.0.0.1`）。

所以要让 Codex 以"可写工程目录 + 可执行命令"的模式运行：

```bash
cd "<VAULT>"
codex            # 首次进入后按提示选择允许写入当前目录 / 允许执行命令的档位
```

**把沙箱放宽到"可写工作目录 + 允许执行命令"就够了**——不需要全盘放开。`<PKG>` 若在工程外，给它**只读**权限即可（脚本不写任何东西，输出都在 stdout）。
具体的档位名称与配置键（`~/.codex/config.toml`）**以你所用版本的文档为准**；目标是上面两条，不要照抄记忆里的字符串。

**验证接好了**：

```bash
python "<PKG>/tools/zotero/rvzotero.py" ping       # 期望退出码 0
```

退出码语义：`0` 正常、`2` 参数用法错、`3` 连不上 Zotero（没开或没开 "Allow other applications…"）、`4` HTTP 非 200（常见是库 ID 不对）、`5` 条目/附件找不到。

---

## 四、为什么不建"技能"、也不用插件

- Codex 的上下文入口就是 `AGENTS.md`；**没有技能目录约定**，硬造一个只会变成"写了没人读"。
  正确做法是 §二 那样在 `AGENTS.md` 里写清**触发条件 → 读哪份 SKILL.md**，让 Agent 显式加载。
- Zotero 侧：Codex 没有 `zotero_*` 工具，也没有插件体系；`rvzotero.py` 覆盖工作流需要的全部读取能力，
  **纯 Python 标准库**，所以"接入"等于"能跑 python"。

---

## 五、这一侧最容易踩的坑

1. **工作目录不是 `<VAULT>`** → `AGENTS.md` 读不到、笔记写到别处。开工第一件事 `pwd`。
2. **只在 `AGENTS.md` 里写"请遵守 ResearchVault 纪律"** → Agent 没有可执行步骤。必须像 §二 §1 那样**点名去哪份 SKILL.md 读规程**。
3. **沙箱没放开写入** → 生成的导读写不进去；但**别为了省事全盘放开**，给 `<VAULT>` 可写 + `<PKG>` 只读即可。
4. **`--include` 只认复数**：`get` 与 `children` **都**用复数（`notes` / `attachments` / `annotations`）；写单数会报**参数错误**（退出码 `2`），不是静默少返回。**旧版本**的 `children --help` 曾把取值印成单数（只看帮助会被带偏），**已修正**：实现与帮助文本现在都只认复数，并有回归测试锁死。
5. **批注可能只挂在某一份 PDF 上**——先 `children` 看结构，`annotations --key` 默认聚合全部附件。
6. **把评论里的机器词典当成研究者的话**（或整条丢掉）：按 `🔤…🔤` 区间切分，用 `--split-comment`。
7. **用 `Invoke-RestMethod` 直连 Local API**（Windows）：Local API 回 HTTP/1.0，会在握手阶段失败。**用脚本**。

---

## 六、相关文档

- 通用接入契约：[../AGENTS.md](../AGENTS.md)（能力映射表、环境变量、检查清单）
- 技能正文：[../skills/researchvault/SKILL.md](../skills/researchvault/SKILL.md) · [../skills/researchvault-query/SKILL.md](../skills/researchvault-query/SKILL.md)
- 其它 harness：[dsh.md](dsh.md) · [claude-code.md](claude-code.md) · [cursor.md](cursor.md) · [generic.md](generic.md)
- 五色语义与 API 陷阱（唯一事实源）：`<VAULT>/00_System/Zotero_Access.md`
- 完整参数：`python <PKG>/tools/zotero/rvzotero.py <子命令> --help`
