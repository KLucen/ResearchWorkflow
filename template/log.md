# 研究日志（Research Log）

> **只追加，不重写历史行。** Agent 每次完成一个动作（ingest / 成稿 / 回答 / Wiki 变更 / lint / 配置变更）后追加一行。
> 列固定：`日期 | 动作 | 对象 | 结果 | 备注`。动作值建议用：`config` / `ingest` / `pass2` / `answers` / `claim` / `wiki` / `gap` / `query` / `lint` / `migrate`。
> 本文件是**操作留痕**，不是知识层——不要在这里写结论。

| Date | Action | Paper / Wiki | Result | Notes |
|---|---|---|---|---|
| `<YYYY-MM-DD>` | config | 全部 | 初始化（从 `template/` 复制，按 `00_System/Config.md` §1 清单填写） | schema_version = 4；访问层自检 `ping` 退出码 0 |
| 2026-01-01 | ingest | `01_Papers/pass1/待精读/<zotero_key>_<短标题>.md` | 生成 5 分钟导览（**示例行，可删**） | 只出导读，未生成 `pass2/`；等研究者五色批注 |
| 2026-01-02 | pass2 | `01_Papers/pass2/<同名>.md` | 批注后成稿（**示例行，可删**） | 转出 `E01`–`E12`；提 2 个问题（待答）；导读移入 `已精读/` |
