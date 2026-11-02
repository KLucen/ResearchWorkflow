# ResearchVault

> 本文件是你的 Vault 入口。**研究坐标**按 `00_System/Research_Profile.md` 填；本页只做导航。
> Agent 的纪律在 `00_System/AGENTS.md`，路径与参数在 `00_System/Config.md`。

## 研究坐标

<!-- 从 Research_Profile.md 抄成一行一条；这四行决定 research_position 的判定方向。 -->

- **核心（Core）**：`<填写>`
- **导师 / 相邻（Mentor）**：`<填写>`
- **交叉（Intersection）**：`<填写>`
- **探索（Exploration）**：有兴趣，但不一定是当前研究

## 工作流（先出导读，批注之后才成稿）

**引入一篇新论文时只生成一份 5 分钟导读**；**只有你读完原文、做完五色批注之后，才生成精读总结**。

```text
Zotero（不可变源：PDF + 元数据 + 批注）
        │
        ▼
   ingest 只出一份
        └──► 01_Papers/pass1/待精读/<zotero_key>_<短标题>.md    5 分钟导览
               一句话 / 要解决的问题 / 架构地图 / 核心观点
               读前概念 / 阅读路线 / 带着问题读
               ≈1000 字；不含证据与主张；此后不再改动
        │
        ▼
   你带导览读原文，做五色批注
        │
   「批注好了」
        ▼
   生成 01_Papers/pass2/<同名>.md    精读总结
       13 节正文 + E 证据对象 + 1–3 个问题 + §11 提案
       受批注影响的段落用 ==高亮== 标出
       同时把导读移入 01_Papers/pass1/已精读/
        │
        ▼
   主张级提案 → 你批准 → 写入 02_Wiki/  → query / lint
```

**两份文件同名配对、互不复制**：导读不进总结，证据不进导读。**`pass1/` 的两个文件夹就是状态**——`待精读/` 还没有 `pass2/`，`已精读/` 已经有了。**Wiki 提案不进 `pass1/`**。

## 批注通道（五色）

| 颜色 | 语义 | 去向 |
|---|---|---|
| 🟡 黄 | 生词 | `03_Vocabulary/` |
| 🟢 绿 | **定义术语或术语解释内容** | 证据 → `concept` 页 |
| 🔵 蓝 | **影响、观点、解决方法** | 证据 → 主张登记表 |
| 🔴 红 | **缺陷、现有问题、现有挑战** | `−` 证据 → 分歧、`gap/`（**`gap/` 的主要来源**） |
| 🟣 紫 | **与我的研究相关** | `research_position` 判定首要依据 |

评论里 `🔤…🔤` 区间内的是翻译插件的机器词典——**不是你的话**，也永远不能当作论文原文；**区间外**的文字是你自己写的，会如实记进笔记。评论归属按区间切分，不按"整条含不含 🔤"。

## Wiki（schema v4 · 目录即类型）

**入口页：[[02_Wiki/_WikiIndex|WikiIndex]]**（主题清单 / 最近变更 / 开放问题 / 验收指标）——投影，不是事实源。

- 五类页面靠**目录**区分（硬约束）：`topic/` 主题地图 · `concept/` X 是什么 · `synthesis/` 文献整体说了什么 · `gap/` 什么还不知道 · `entity/` 专名实体。**frontmatter 不写 `type`**
- 每条页面正文六节：§1 综合与当前理解 / **§2 主张登记表** / §3 共识 / §4 分歧 / §5 未解决问题 / §6 变更记录
- **§2 是唯一事实源（8 列）**：`ID | 主张 | 证据 | 状态 | 批准 | 生效 | 失效 | 替代`
- **证据列三件套** `[[Paper Note]]E编号 (页码)`——**点一下就回到 `pass2/` 原文**，这就是检索的命中依据
- **行只增、状态只改，行永不删除**——推翻也要留痕，否则看不到知识是怎么进化的
- 每次 ingest 必做**主张影响检查**；未解决问题按条件升级为 `gap/` 页
- **会遗忘**：`retired_at` 非空的内容检索期默认过滤；被问起时标注「此条已废止」

## Vocabulary（生词库）

- 一个词元一个文件（如 `unify.md` 收录 `unified / unifies / unifying`）
- 两个"意思"分开记：**词典义**（词本身）+ **本语境义**（这句话里）
- **同一个词再遇到时回到原文件追加一节**，不新建文件；直到你说"这个词我认识了"（`acquired: true`）
- 语言层：不进 Wiki、不进证据对象

## 体例

说明性文字用**中文**；论文**原文摘录保持原语言并附中文翻译**；frontmatter 的键与枚举值保持英文。四条默认体例可在 `00_System/Config.md` §5 改。

## 环境自检

```bash
python tools/zotero/rvzotero.py ping     # 退出码 0 = Zotero Local API 通
```

不通时看 `00_System/Zotero_Access.md`（含四条已知 API 陷阱）。

## 关键页面

<!-- 以下为 Obsidian wiki 链接（不含 .md 后缀），在 Vault 内直接可跳。 -->

- [[00_System/AGENTS|AGENTS]]（纪律）
- [[00_System/Config|Config]]（配置事实源）
- [[00_System/Workflow|Workflow]]（操作手册）
- [[00_System/Paper_Schema|Paper_Schema]]
- [[00_System/Wiki_Schema|Wiki_Schema]]
- [[00_System/Vocabulary_Schema|Vocabulary_Schema]]
- [[00_System/Research_Profile|Research_Profile]]（**待你填写**）
- [[00_System/Zotero_Access|Zotero_Access]]（访问规范 + 五色批注 + API 陷阱）
- [[00_System/Automatic_Archiving_Rules|Automatic_Archiving_Rules]]
- [[00_System/Dataview_Dashboard|Dataview_Dashboard]]
- [[00_System/lint-report|lint-report]]（体检报告）
- [[01_Papers/pass1/_Reading_Guide_Template|导读模板]]
- [[01_Papers/pass2/_Paper_Template|精读总结模板]]
- [[02_Wiki/_WikiIndex|WikiIndex]]（入口页）
- [[02_Wiki/_Wiki_Template|Wiki 模板]]
- [[03_Vocabulary/_Vocabulary_Template|生词模板]]
- [[log|研究日志]]
