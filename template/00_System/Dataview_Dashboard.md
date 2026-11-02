# Research Dashboard（研究仪表盘）

> **需要 Obsidian 的 Dataview 插件**（必需）。下面的查询块只有装了 Dataview 才会渲染；没装时它们只是普通代码块。
> frontmatter 的键与枚举值保持英文，因此查询语句本身也是英文；表头已改为中文。
> 查询里的路径（`01_Papers` / `02_Wiki` / `03_Vocabulary`）与占位符无关，**不要把目录改名**，否则所有视图都会变空。
> **所有查询都用 `!startswith(file.name, "_")` 排除模板与入口页**：`_` 前缀是本发布包里「基础设施文件」的保留约定（`_Paper_Template.md`、`_WikiIndex.md`、`_Vocabulary_Template.md` …），**给真实笔记起名时不要用 `_` 开头**。

## 在读论文

```dataview
TABLE research_position AS "定位", interest_level AS "兴趣", research_relevance AS "相关性", reading_status AS "状态"
FROM "01_Papers"
WHERE type = "paper" AND !startswith(file.name, "_")
  AND reading_status != "completed" AND reading_status != "archived"
SORT interest_level DESC, research_relevance DESC
```

## 四轴分布（core / mentor / intersection / exploration）

```dataview
TABLE research_position AS "定位", interest_level AS "兴趣", research_relevance AS "相关性"
FROM "01_Papers"
WHERE type = "paper" AND !startswith(file.name, "_")
GROUP BY research_position
```

## Wiki 页（按目录 = 按类型）

```dataview
TABLE file.folder AS "类型", status AS "状态", confidence AS "置信度", length(source_papers) AS "来源数", updated AS "更新"
FROM "02_Wiki"
WHERE !startswith(file.name, "_")
SORT file.folder ASC, updated DESC
```

> **「目录即类型」**：`file.folder` 就是类型（`02_Wiki/concept` 等），frontmatter **没有**类型字段，所以查询一律用 `file.folder`。
> 这里**不排除** `02_Wiki` 根目录：内容页一旦落在根下，`类型` 列就会显示成 `02_Wiki` 本身——**那就是违规状态，要的就是让它显形**（根下只应有 `_WikiIndex.md` 与 `_Wiki_Template.md`，两者已被 `_` 前缀排除）。
> 「来源数 = 1」的页面，其主张状态最多只能是 `proposed`——这是判断该页是否已具备跨论文价值的最快指标。

## 待复核的 Wiki 页

```dataview
TABLE file.folder AS "类型", status AS "状态", confidence AS "置信度", last_reviewed AS "上次复核"
FROM "02_Wiki"
WHERE !startswith(file.name, "_")
  AND (status = "draft" OR last_reviewed < date(today) - dur(90 days))
SORT last_reviewed ASC
```

## 已下线的 Wiki 页（`retired_at` 非空）

```dataview
TABLE file.folder AS "类型", effective_from AS "生效", retired_at AS "下线", superseded_by AS "被取代"
FROM "02_Wiki"
WHERE !startswith(file.name, "_") AND retired_at != null AND retired_at != ""
SORT retired_at DESC
```

> **检索期默认过滤这些页**——它们只用于回答「这条为什么变了」。被问起时应标注「此条已废止」。

## 有未答问题的论文

```dataview
TABLE reading_status AS "状态", research_position AS "定位", interest_level AS "兴趣", research_relevance AS "相关性", last_reviewed AS "最近复核"
FROM "01_Papers"
WHERE type = "paper" AND !startswith(file.name, "_")
  AND contains(file.content, "PENDING_RESEARCHER_RESPONSE")
SORT interest_level DESC
```

> 这些就是**等你回答**的位置。Agent 不得代答——回答后该处应被替换为 `Researcher Response`。

## 导读 ↔ 精读总结 配对检查

> **需要 Dataview 的 JavaScript 查询**（Obsidian → 设置 → Dataview → 打开 **Enable JavaScript Queries**）。没打开时此块不会渲染。
> 它把「位置即状态」这条纪律变成可见的红灯——lint 里最容易漏掉的一类结构性错误。

```dataviewjs
const notes = new Set(
  dv.pages('"01_Papers/pass2"')
    .where(p => !p.file.name.startsWith("_"))
    .file.name.array()
);
const rows = [];
for (const p of dv.pages('"01_Papers/pass1"')) {
  const name = p.file.name;
  if (name.startsWith("_")) continue;               // 跳过模板
  const folder = p.file.folder || "";
  const inTodo = folder.endsWith("待精读");
  const inDone = folder.endsWith("已精读");
  if (!inTodo && !inDone) {
    rows.push([p.file.link, "导览不在 待精读/ 也不在 已精读/", "移入正确的子目录（根下只放模板）"]);
  } else if (notes.has(name) && inTodo) {
    rows.push([p.file.link, "已有 pass2/<同名>.md，导览却仍在 待精读/", "移入 已精读/"]);
  } else if (!notes.has(name) && inDone) {
    rows.push([p.file.link, "没有 pass2/<同名>.md，导览却在 已精读/", "移回 待精读/ 或补生成精读笔记"]);
  }
}
if (rows.length === 0) {
  dv.paragraph("✅ 配对一致：全部导览的位置与 `pass2/` 的存在性相符。");
} else {
  dv.table(["导览", "问题", "应做"], rows);
}
```

## 待精读（导读已出、尚未成稿）

```dataview
TABLE zotero_key AS "Zotero", title AS "标题", created AS "生成日期"
FROM "01_Papers/pass1/待精读"
WHERE type = "reading-guide"
SORT created DESC
```

> 本视图 = 「**导读已出，但还没读完 / 还没批注**」的论文。说一声「批注好了」生成 `pass2/` 之后，导读就应移入 `已精读/`。

## 已精读（导读 + 精读笔记）

```dataview
TABLE zotero_key AS "Zotero", title AS "标题", last_reviewed AS "最近复核"
FROM "01_Papers/pass1/已精读"
WHERE type = "reading-guide"
SORT last_reviewed DESC
```

> **导览的位置就是状态**：`待精读/` ⇒ 尚无 `pass2/<同名>.md`；`已精读/` ⇒ 已有。两者与精读笔记**按文件名配对**，不写状态字段。

## 生词库：仍在学

```dataview
TABLE lemma AS "词元", dictionary AS "词典义", encounters AS "遇见次数", last_seen AS "最近遇见"
FROM "03_Vocabulary"
WHERE type = "vocabulary" AND !startswith(file.name, "_") AND acquired = false
SORT encounters DESC, last_seen DESC
```

## 生词库：已掌握

```dataview
TABLE lemma AS "词元", dictionary AS "词典义", encounters AS "遇见次数"
FROM "03_Vocabulary"
WHERE type = "vocabulary" AND !startswith(file.name, "_") AND acquired = true
SORT last_seen DESC
```

> 「遇见次数 ≥ 3 且仍未掌握」的词值得单独复习一遍——同一个词在不同语境反复卡住，通常不是词汇量问题而是它在你的领域里有专门含义。
> `acquired` **只能由研究者本人标记**，Agent 不得自行改成 `true`。

---

## 附录：可选 Tasks 视图

> **需要 Tasks 插件**（可选）。论文笔记里的 `- [ ]` 待办会汇总到这里。没装插件时下面的块只是普通代码块。

```tasks
not done
path includes 01_Papers
sort by description
```
