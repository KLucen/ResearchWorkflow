# 15 分钟跑通

> 前置：Obsidian、Zotero、Python 3.8+。
> 本文每一步都给**验证方法**——你不用猜自己有没有做对，照着敲就会看到「成功长什么样」。
> 卡在某一步不动了：先看 [07-faq.md](07-faq.md)，Zotero 相关的问题看 [05-zotero-access.md](05-zotero-access.md)。

## 时间预算

| 步骤 | 内容 | 约需 |
|---|---|---|
| 0 | 检查前置条件 | 1 min |
| 1 | 打开 Zotero 的本地 API 开关 | 1 min |
| 2 | 验证 Zotero 访问层 | 2 min |
| 3 | 复制 `template/` 得到你的 Vault | 1 min |
| 4 | 用 Obsidian 打开并装插件 | 3 min |
| 5 | 填 `Config.md` 与 `Research_Profile.md` | 5 min |
| 6 | 接入你的 Agent | 2 min |
| 7 | 跑第一次 ingest | 视论文长度 |

**第 0–6 步是搭建，第 7 步才是使用。** 搭建一次，之后每天只重复第 7 步的循环。

---

## 第 0 步 · 检查前置条件

需要三样东西：

| 依赖 | 版本 | 为什么需要 |
|---|---|---|
| **Zotero** | 6 或 7 | 论文原文、书目元数据、你的五色批注的唯一来源（不可变源） |
| **Python** | 3.8+ | 跑 Zotero 访问层 `tools/zotero/rvzotero.py`（**只用标准库，不用装任何包**） |
| **Obsidian** | 任意近期版本 | 打开 Vault、看 Dataview 仪表盘 |

在终端里验证：

```bash
python --version     # 或 python3 --version，应输出 3.8 以上
```

> **Windows 提示**：如果 `python --version` 打开了 Microsoft Store 或没反应，说明 Python 没装好或没进 PATH。装一个 python.org 的官方版本，安装时勾选 *Add python.exe to PATH*。

**怎么知道成功了**：上面这条命令打印出 `Python 3.8.x` 或更高版本号。

> 还需要一个 Agent（Claude Code / Cursor / Codex / 或任何能读文件、写文件、跑 shell 的 Agent）。第 6 步才需要，现在可以先不装。

---

## 第 1 步 · 打开 Zotero 的本地 API 开关

**启动 Zotero**，然后：

```text
Zotero → Settings / 编辑 → Advanced → General
  ✅ Allow other applications on this computer to communicate with Zotero
```

**必须重启 Zotero**，这个开关才生效。

**怎么知道成功了**：重启 Zotero 后，用浏览器打开下面的地址，能看到一段 JSON（不是「无法连接」）：

```text
http://127.0.0.1:23119/api/users/0/items?limit=1
```

> **Windows 特别注意**：如果你的浏览器能打开但 PowerShell 脚本连不上，那不是 Zotero 的问题——Zotero 本地 API 回的是 `HTTP/1.0`，PowerShell 的 `Invoke-RestMethod` 会握手失败。用 `curl.exe` 或本仓库的 `rvzotero.py`，**不要用 `Invoke-RestMethod`**。原因见 [05-zotero-access.md](05-zotero-access.md)。

---

## 第 2 步 · 验证 Zotero 访问层

进入你克隆下来的仓库根目录，跑探活：

```bash
python tools/zotero/rvzotero.py ping
```

**怎么知道成功了**：它报告 Zotero 版本、库 id 和条目总数，类似：

```json
{
  "ok": true,
  "api_base": "http://127.0.0.1:23119/api",
  "library": "users/0",
  "zotero_version": "10.0.7",
  "total_items": 44,
  "library_id": 123456789,
  "library_name": "My Library"
}
```

**判据只有一个：`"ok": true`。** `zotero_version` 是你自己的 Zotero 版本，跟这里不一样很正常；`total_items` 是你库里有多少条目，空库会是 0。

再看一眼你有哪些集合：

```bash
python tools/zotero/rvzotero.py collections
```

输出含 `total` 与 `collections` 数组，每项有 `key` / `name` / `indent` / `numItems`。

做一次检索冒烟测试：

```bash
python tools/zotero/rvzotero.py search --query "survey" --limit 5
```

输出含 `total`（命中总数）与 `items` 数组，每项有 `key` / `version` / `data`。把 `survey` 换成你库里确实存在的词，`total` 应该大于 0。

**连不上的时候**：`ping` 的退出码是 **3**，并且会打印可执行的修复指引（Zotero 没开 / 开关没打开 / 端口被占）。逐条照做即可。

| 退出码 | 含义 |
|---|---|
| `0` | 成功 |
| `2` | 参数写错了 |
| `3` | **连不上 Zotero**（附修复指引） |
| `4` | Zotero 返回了非 200 |
| `5` | 没找到 |

完整用法与故障排查见 [05-zotero-access.md](05-zotero-access.md) 与 [tools/zotero/README.md](../tools/zotero/README.md)。

---

## 第 3 步 · 复制 `template/` 得到你的 Vault

`template/` 是**空白 Vault 骨架**。复制它、改个名字，就是你的研究工作区：

```bash
cp -r template/ /path/to/MyResearchVault
```

（Windows 上也可以直接在文件管理器里复制粘贴整个 `template` 文件夹并重命名。）

**复制方法、复制后第一件事、目录结构速览，都写在 [template/README.md](../template/README.md) —— 照着它做即可。**

本文只补充三件它没展开的事：

1. **只有 Dataview 是必需插件。** `index.md`、`02_Wiki/_WikiIndex.md`、`00_System/Dataview_Dashboard.md` 里的所有查询都依赖它。Templater 与 Tasks 只是推荐。
2. **别覆盖你已有的插件清单。** 如果你是把 `template/` 复制进一个**已有**的 Vault，`template/.obsidian/community-plugins.json` 会覆盖你自己的插件配置——这种情况请手动合并，不要直接覆盖。
3. **Vault 里不放 PDF。** 论文原文永远留在 Zotero。

**怎么知道成功了**：新目录里有 `00_System/`、`01_Papers/`、`02_Wiki/`、`03_Vocabulary/`、`index.md`、`log.md` 这几项。

---

## 第 4 步 · 用 Obsidian 打开，装插件

Obsidian → **Open folder as vault** → 选中你刚复制的目录。

**打开时 Obsidian 会检测到 `.obsidian/community-plugins.json` 里声明的插件并弹出安装提示——点一下确认即可**，不需要你自己去社区插件市场里搜。

三个插件：

| 插件 | 用途 | 是否必需 |
|---|---|---|
| **Dataview** | `index.md`、`_WikiIndex.md`、`Dataview_Dashboard.md` 里的全部查询 | **必需** |
| **Templater** | 用 `_*_Template.md` 快速新建规范文件 | 推荐 |
| **Tasks** | 仪表盘里的待办汇总 | 推荐 |

装完后**启用**它们（Settings → Community plugins → 打开开关）。

**怎么知道成功了**：打开 `00_System/Dataview_Dashboard.md`，查询块渲染成**表格**而不是一段代码。如果显示的是代码原文或 `Dataview: Query failed`，说明插件没装好或没启用。

---

## 第 5 步 · 填 `Config.md` 与 `Research_Profile.md`

这两份是你必须亲手填的文件。**在你填完之前，不要开始 ingest。**

### 5.1 `00_System/Config.md` —— 配置事实源

Agent 每次工作前都会先读它。把占位符换成你自己的值，至少要改这几项：

| 要填什么 | 说明 |
|---|---|
| **Vault 路径** | 你刚复制的目录的绝对路径 |
| **Zotero 数据目录** | 你的 Zotero 数据文件夹（PDF 在 `storage/<attachment_key>/` 下） |
| **Zotero Local API 地址** | 默认 `http://127.0.0.1:23119/api`，没改过端口就不用动 |
| **语言体例** | 默认是「说明性内容用中文，论文原文摘录保持原语言并附中文翻译」。**不想用中文体例就改这里**（见 [07-faq.md](07-faq.md)） |
| **Zotero 集合 → `research_position` 映射** | 模板里给的是一组**示例**集合名，**请按你自己的集合改名** |

### 5.2 `00_System/Research_Profile.md` —— 研究坐标

这是 `research_position` 判定的依据，也是 Agent 判断「什么和你的研究相关」的唯一来源。填四件事：

- **主领域**（Primary Domain）
- **核心兴趣**（Core Interests）
- **导师 / 相邻领域**（Mentor / Adjacent Domain）
- **特别关注的交叉**（Intersection）

> **为什么必须你填**：🟣 紫色批注是 `research_position` 判定的首要依据，而「紫色意味着什么」只有你的研究坐标能解释。Agent 猜不出来。

**怎么知道成功了**：两份文件里**不再有 `<...>` 形式的占位符**。

---

## 第 6 步 · 接入你的 Agent

**结论：任何能「读文件、写文件、跑 shell」的 Agent 都能用**，不需要任何专有工具或插件。

最快的方式是把接入契约交给它：

```text
请先读 agent/AGENTS.md，然后按它工作。
```

再把 Vault 路径告诉它（或写进你这个项目根目录的 `AGENTS.md` / `CLAUDE.md` / `.cursor/rules`，取决于你用什么 harness）。

**三种接入方式（项目根契约 / 装成 skill / 直接贴提示词）与各 harness 的具体路径**，见 [06-agent-integration.md](06-agent-integration.md)。

**怎么知道成功了**：让 Agent 回答一个问题——

```text
问它：这个工作流的证据层在哪个目录？pass1 和 pass2 是什么关系？
```

它能答出「证据层是 `01_Papers/pass2/`；`pass1/` 是导读、是阅读辅助不是证据；`pass2/` 要等批注之后才生成」——说明它真的读了契约，而不是在编。

---

## 第 7 步 · 跑第一次 ingest

### 7.1 挑一篇论文

在 Zotero 里挑一篇**你确实打算读**的论文（第一次别挑最难的），然后对 Agent 说：

```text
帮我 ingest 这篇论文：<论文标题，或 Zotero 里那条目的链接>
```

### 7.2 预期产物

Agent 应该只产出**一份**文件：

```text
<VAULT>/01_Papers/pass1/待精读/<zotero_key>_<短标题>.md
```

一份 **5 分钟导读**，七段固定结构：页码基准 + 一句话 / 要解决的问题 / 论文架构地图 / 核心观点 / 读前必备的概念与记号 / 阅读路线 / 带着这几个问题读。约 1000 字。

**此刻 `01_Papers/pass2/` 下什么都不该有。这是正确的，不是漏做。**

### 7.3 验收清单

| 检查项 | 应该看到 |
|---|---|
| 文件位置 | 在 `01_Papers/pass1/待精读/` 下（**不在** `pass1/` 根下，也**不在** `pass2/`） |
| 文件名 | `<zotero_key>_<短标题>.md` |
| 篇幅 | 约 1000 字，**不超过 1200–1300 中文字** |
| 内容 | 有「论文架构地图」「核心观点」等七段 |
| **不该有** | 任何 `E01` 形式的编号、主张、Wiki 提案、`R01`、`PENDING_RESEARCHER_RESPONSE` |
| **不该有** | 实验结果、具体数字、作者的最终结论（导读只写作者**声称**什么） |
| `log.md` | 追加了一行记录 |
| `01_Papers/pass2/` | **空的** |

> 出现 `E` 编号 / 主张 / `PENDING_...` 就是违规——`pass1/` 一旦带上这些，你就有了第二个证据源。见 [01-design.md](01-design.md) 第四节。

### 7.4 然后是你的时间

1. **带着导读去 Zotero 读原文**，用五种颜色做高亮（🟡 生词 / 🟢 定义 / 🔵 主张与解决方法 / 🔴 缺陷与挑战 / 🟣 与我的研究相关）。
2. 读完对 Agent 说：「**批注好了**」。
3. Agent 这时才生成 `01_Papers/pass2/<同名>.md`，并把导读移入 `01_Papers/pass1/已精读/`。

**为什么不能跳过第 1 步**：`pass2/` 是证据层，它的证据基础是「你的批注 + Agent 的通读」。缺了批注，它只会产出**一个未经你确认、却长得像结论的东西**——而那比没有文件危险得多。

---

## 跑通之后

| 你想做的事 | 去看 |
|---|---|
| 搞清 ingest / query / lint 每一步做什么、人工确认点在哪些 | [03-workflow.md](03-workflow.md) |
| 查某个字段能不能写、谁能写 | [04-schemas.md](04-schemas.md) |
| Zotero 连不上 / 批注读出 0 条 / 只有 100 条 | [05-zotero-access.md](05-zotero-access.md) |
| 接别的 Agent、写项目根契约 | [06-agent-integration.md](06-agent-integration.md) |
| 其他问题 | [07-faq.md](07-faq.md) |

日常循环只有三步：**ingest 新论文 → 读 + 批注 → 说「批注好了」**。其余时间用 `query` 问问题、定期跑 `lint` 体检。
