# ResearchWorkflow

**一套让 AI Agent 帮你精读论文、且不会替你下结论的工作流。**

用 Zotero 存文献，用 Obsidian 存笔记。Agent 负责把论文变成结构化的导读与证据笔记，
你只负责做高亮批注和回答它问你的问题。

[English README](README.en.md) · [15 分钟快速开始](docs/02-quickstart.md) · [设计原理](docs/01-design.md) · [常见问题](docs/07-faq.md)

---

## 它解决什么问题

让 LLM 读论文，通常有三种坏结局：

| 坏结局 | 具体表现 | 本工作流的对策 |
|---|---|---|
| **它替你下结论** | 笔记里分不清哪句是论文说的、哪句是模型猜的，回头自己都不敢引用 | **三层证据纪律**：论文原文 / Agent 推断（显式标为暂定）/ 你的回答，三者物理隔离 |
| **它抓不住重点** | 洋洋洒洒总结了一堆，全是你不在意的部分 | **五色批注通道**：你只管在 Zotero 里画高亮，颜色就是语义，Agent 据此分流 |
| **知识不积累** | 读完 50 篇，脑子里还是一盘散沙，同一个问题每次都要重新翻 | **主张账本**：跨论文的主张有稳定 ID、有证据回链、有状态流转，随时可查可推翻 |

一句话概括这套工作流的核心主张：

> **Agent 不做判断，Agent 做结构和检索。判断留给你的批注。**

---

## 它是怎么运转的

```
                    ┌─────────────────────────────────────────┐
                    │  Zotero（不可变事实源）                  │
                    │  论文 PDF · 书目元数据 · 你的五色批注     │
                    └────────────────┬────────────────────────┘
                                     │  只读
                        ┌────────────▼────────────┐
                        │  rvzotero.py            │  ← 替代各种 Zotero 插件
                        │  Local API 访问层        │     纯标准库，任何 Agent 可调
                        └────────────┬────────────┘
                                     │
        ┌────────────────────────────┼────────────────────────────┐
        │                            │                            │
   ┌────▼─────┐              ┌───────▼────────┐          ┌────────▼────────┐
   │  ingest  │              │     query      │          │      lint       │
   │ 把论文    │              │ 回答研究问题    │          │ 检查一致性与     │
   │ 变成笔记  │              │ 四分类证据      │          │ 断链            │
   └────┬─────┘              └───────┬────────┘          └────────┬────────┘
        │                            │                            │
        └────────────────────────────┼────────────────────────────┘
                                     │  写入
                    ┌────────────────▼────────────────────────┐
                    │  Obsidian Vault                         │
                    │  pass1/ 导读（阅读辅助，非证据）          │
                    │  pass2/ 精读笔记（证据层）                │
                    │  02_Wiki/ 持久知识（主张层）              │
                    │  03_Vocabulary/ 生词（语言层）            │
                    └─────────────────────────────────────────┘
```

### 两个关键设计

**一、先导读，后成稿 —— 两步 ingest**

引入一篇新论文时，Agent **只生成一份 5 分钟导读**（一页，约 1000 字：它要解决什么问题、
章节地图、作者声称了什么、读之前该知道什么、带着哪几个问题读）。

然后你去读原文、画高亮。**只有在你画完批注之后**，Agent 才生成第二份文件——精读总结。
总结里受你批注影响的段落会用 `==高亮==` 标出来，让你一眼看出哪些是"你带出来的"。

为什么要有这一步？因为**没有批注就生成的"总结"，是一个没人确认过、却长得像证据的东西**。
这是最危险的失败模式。

**二、五色批注 —— 用颜色告诉 Agent 你在想什么**

| 颜色 | 语义 | 去向 |
|---|---|---|
| 🟡 黄 | 生词 | 进生词库，不进知识层 |
| 🟢 绿 | 定义术语 / 术语解释 | 概念页 |
| 🔵 蓝 | 影响、观点、解决方法 | 主张账本（默认记为支持） |
| 🔴 红 | 缺陷、现有问题、挑战 | 反对证据、分歧、研究空白 |
| 🟣 紫 | 与我的研究相关 | 判断这篇论文对你的价值 |

紫色是唯一 Agent 无法从文本推断出来的信号——所以只有你知道。

> **一个实测出来的坑**：很多人用翻译插件读论文，批注评论里会同时出现
> `🔤机器译文🔤` 和「我自己写的话」。本工作流按 `🔤…🔤` **区间**切分，
> 区间内是机器词典（永不作论文原文），区间外才是你说的话。
> 按「整条含不含 🔤」判断会把你的话全部丢掉。

---

## 怎么用

### 你需要准备

- **Obsidian**（免费）—— 存笔记
- **Zotero**（免费）—— 存文献和批注
- **Python 3.8+** —— 只有标准库依赖，不用 pip install 任何东西
- **任意一个能读文件、能跑命令的 Agent** —— Claude Code / Cursor / Codex / DSH / 你自己写的都行

### 五步跑通

```bash
# 1. 拿到本仓库
git clone https://github.com/KLucen/ResearchWorkflow.git
cd ResearchWorkflow

# 2. 复制空白 Vault 骨架
cp -r template/ ~/MyResearchVault

# 3. 打开 Zotero → 设置 → 高级 → 勾选 "Allow other applications on this computer"

# 4. 验证 Agent 能读到你的 Zotero
python tools/zotero/rvzotero.py ping
# → {"ok": true, "library": "users/0", ...}   看到 ok 就成了

# 5. 让 Agent 开始工作
#    把 agent/AGENTS.md 的内容交给你的 Agent，然后说：
#    「读 agent/AGENTS.md 和 <VAULT>/00_System/Config.md，然后 ingest 我 Zotero 里
#      <集合名> 这个集合的第一篇论文」
```

**别忘了先填 `<VAULT>/00_System/Config.md`** —— 那是配置事实源，Agent 每次工作前都会读它。

详细版：[docs/02-quickstart.md](docs/02-quickstart.md)

### 日常循环

```
                  ┌──────────────────────────────────────────┐
                  │                                          │
   ① 丢论文进      ② Agent 出导读     ③ 你读原文 + 画五色批注
   Zotero    ──→   pass1/待精读/  ──→  （在 Zotero 里做，不在 Obsidian）
                                             │
                                             ▼
   ⑥ 回答它的问题  ←──  ⑤ Agent 出精读总结  ←──  ④ 告诉 Agent「读完了」
   （问题写回笔记）      pass2/ + 导读移入已精读/
        │
        └──→ ⑦ 攒够几篇，让 Agent 更新 02_Wiki/ 的主张账本（需你批准）
```

每一步的输入、产出、人工确认点：[docs/03-workflow.md](docs/03-workflow.md)

---

## 仓库结构

```
ResearchWorkflow/
├─ README.md              你在这里
├─ README.en.md           英文版
├─ docs/                  人读的说明文档
│   ├─ 01-design.md           为什么要这么设计
│   ├─ 02-quickstart.md       15 分钟跑通
│   ├─ 03-workflow.md         ingest / query / lint 全流程
│   ├─ 04-schemas.md          字段速查
│   ├─ 05-zotero-access.md    Zotero 访问层与故障排查
│   ├─ 06-agent-integration.md 接入你自己的 Agent
│   └─ 07-faq.md              常见问题
├─ template/              ★ 复制这个 → 你的 Vault
│   ├─ 00_System/             Agent 宪法、配置、schema、仪表盘
│   ├─ 01_Papers/             导读 + 精读笔记
│   ├─ 02_Wiki/               持久知识
│   └─ 03_Vocabulary/         生词库
├─ tools/zotero/          ★ 可移植 Zotero 访问层（替代各类插件）
│   ├─ rvzotero.py            纯标准库 CLI
│   ├─ README.md              命令参考
│   └─ tests/                 离线单测 + mock 服务器
└─ agent/                 ★ 让任意 Agent 接入
    ├─ AGENTS.md              通用接入契约
    ├─ skills/                两个可安装的 skill
    └─ adapters/              各 harness 的安装说明
```

---

## 关于 Zotero 访问层

**不需要安装任何 Zotero 插件。** 本仓库自带 `tools/zotero/rvzotero.py`，
直接调 Zotero 的 Local API，纯 Python 标准库实现：

```bash
python tools/zotero/rvzotero.py ping                            # 探活
python tools/zotero/rvzotero.py collections                     # 列集合
python tools/zotero/rvzotero.py search --query "diffusion" --limit 5
python tools/zotero/rvzotero.py annotations --key <item-key>    # 读五色批注（默认全量）
python tools/zotero/rvzotero.py retrieve --key <item-key> --query "evaluation"   # 全文检索
python tools/zotero/rvzotero.py attachment --key <item-key>     # 拿到 PDF 磁盘路径
```

它内置了几个**真实踩过的坑**的修复，这些坑不修会静默出错：

- `/children` **不带参数时静默返回 0 条批注**（不报错）—— 最危险，你以为论文没批注
- 列表接口在 **100 条处静默截断** —— 需要按 `Total-Results` 响应头翻完全部分页
- `fulltext?page=N` 的 **`page` 参数被 Zotero 完全忽略**，永远返回整篇 —— 工具改为本地切分，并把页码显式标注为「估算」
- 一篇论文常有多个 PDF 附件，**批注只挂在其中一个上**
- Zotero Local API 回 **HTTP/1.0**，Windows 上用 PowerShell 的 `Invoke-RestMethod` 会握手失败

贯穿整层的一条原则：**凡是返回的比存在的少，都必须显式说出来。**
所以任何截断、估算或降级都会在输出里带 `truncated` / `note` 之类的字段，绝不静默。

命令参考：[tools/zotero/README.md](tools/zotero/README.md)
原理与排错：[docs/05-zotero-access.md](docs/05-zotero-access.md)

---

## 支持哪些 Agent

这套工作流**不绑定任何 Agent 实现**。它需要的能力只有三样：读文件、写文件、跑命令。

| Harness | 接入方式 | 说明 |
|---|---|---|
| **Claude Code** | `CLAUDE.md` + `.claude/skills/` | [adapter](agent/adapters/claude-code.md) |
| **Cursor** | `.cursor/rules/*.mdc` | [adapter](agent/adapters/cursor.md) |
| **Codex** | 仓库根 `AGENTS.md` | [adapter](agent/adapters/codex.md) |
| **DSH** | `~/.dsh/skills/<name>/SKILL.md` | [adapter](agent/adapters/dsh.md)（含插件替代对照表） |
| **其他 / 自研** | 把契约贴进系统提示 | [adapter](agent/adapters/generic.md) |

统一入口是 [agent/AGENTS.md](agent/AGENTS.md) —— 无论用什么 Agent，先让它读这个。

---

## 这套东西的边界

**它不会做的**：

- ❌ 替你判断一篇论文好不好、值不值得跟
- ❌ 在你没批注之前就生成"结论"
- ❌ 把机器翻译当成论文原文
- ❌ 未经你批准就把某个判断升级成 Wiki 里的持久结论
- ❌ 向你的 Zotero 写入任何东西（整个访问层是只读的）

**它需要你做的**：

- ✅ 在 Zotero 里老实画高亮（这是唯一的"信号输入"）
- ✅ 回答 Agent 问你的问题（它宁可留着 `PENDING_RESEARCHER_RESPONSE` 也不会替你答）
- ✅ 批准或否决 Wiki 变更

---

## 许可

[MIT](LICENSE)
