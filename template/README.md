# ResearchWorkflow · template 使用说明

这个目录是**空白 Vault 骨架**。复制它 → 改个名字 → 就是你的研究工作区。

## 复制方法

```bash
# 方式一：命令行
cp -r template/ /path/to/MyResearchVault

# 方式二：直接在你的文件管理器里复制粘贴整个 template 文件夹并重命名
```

复制完在 Obsidian 里 **Open folder as vault** 选中它。

## 复制后第一件事

打开 `00_System/Config.md`，把里面的占位符换成你自己的值。这份文件是**配置事实源**——
Agent 每次工作前都会先读它，没填之前不要开始 ingest。

## 需要的 Obsidian 插件

`.obsidian/community-plugins.json` 已经声明了三个必需插件，Obsidian 打开时会提示你安装：

| 插件 | 用途 | 是否必需 |
|---|---|---|
| **Dataview** | `index.md`、`_WikiIndex.md`、`00_System/Dataview_Dashboard.md` 里的所有查询 | **必需** |
| **Templater** | 用 `_*_Template.md` 快速新建规范文件 | 推荐 |
| **Tasks** | 仪表盘里的待办汇总 | 推荐 |

如果你复制到的是一个**已有**的 Vault 而不是新建，注意别用这个文件覆盖你自己已有的
`.obsidian/community-plugins.json`。

## 目录结构

```
00_System/      规范与配置：Agent 读这里才知道怎么做（宪法在 AGENTS.md）
01_Papers/
  pass1/待精读/  第一步产物：5 分钟阅读导览（还不是证据）
  pass1/已精读/  导读的位置就是状态：成稿后导读挪到这里
  pass2/        第二步产物：精读总结（唯一的证据层）
02_Wiki/        持久知识：topic/ concept/ synthesis/ gap/ entity/ 目录即类型
03_Vocabulary/  生词库（语言层，不参与知识层）
index.md        Vault 入口
log.md          操作日志
```

**注意**：`01_Papers/pass1/` 与 `01_Papers/pass2/` 是两步流程，不是两个深度。
先只出导读（`pass1/待精读/`），研究者在 Zotero 里读原文并做完五色批注之后，
才生成 `pass2/` 精读总结。详见 `00_System/Workflow.md`。

## 下一步

- 想让 Agent 开始工作 → 把仓库根目录的 `agent/AGENTS.md` 交给你的 Agent
- 想知道每一步具体做什么 → `00_System/Workflow.md`
- 完整上手流程 → 仓库的 `docs/02-quickstart.md`
