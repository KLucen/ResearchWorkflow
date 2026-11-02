# `rvzotero.py` —— 可移植的 Zotero 访问层

一个**只读**、**纯 Python 3.8+ 标准库**、零第三方依赖的命令行工具，用来把本机
Zotero 的资料读出来喂给上层工作流（文献笔记、Wiki、检索问答）。

它存在的理由：Zotero 的 Local API 有几处**会静默骗人**的行为——不报错、不告警，
就是少给你几条数据。这个工具把这些坑全部堵上，并且**凡是有截断、有估算、有
降级，都在输出里明说**。

```
tools/zotero/
├── rvzotero.py            主程序（单文件，可直接拷走）
├── README.md              本文件
└── tests/
    ├── mock_zotero.py     离线 mock Local API（标准库 http.server）
    └── test_rvzotero.py   离线单测，不需要 Zotero 在运行
```

---

## 1. 前置条件

| 要求 | 说明 |
| --- | --- |
| Python | 3.8 或更高（无第三方依赖） |
| Zotero | 桌面版正在运行，且已开启本地 API |
| 网络 | 只访问本机回环地址，不联网 |

**开启本地 API**：Zotero → 设置 → 高级 → 勾选
「Allow other applications on this computer to communicate with Zotero」
（中文界面：允许其他应用与 Zotero 通信）。改完需要重启 Zotero。

---

## 2. 快速开始

```bash
python rvzotero.py ping
```

```json
{
  "ok": true,
  "api_base": "http://127.0.0.1:23119/api",
  "library": "users/0",
  "resolved_library": "users/0000000",
  "zotero_version": "x.y.z",
  "api_version": "3",
  "schema_version": "NN",
  "server_id": "xxxxxxxxxxxxxxxx",
  "last_modified_version": 1234,
  "total_items": 42,
  "library_id": 0,
  "library_name": "My Library"
}
```

上例中的库 id、库名、条目数、版本号**都是占位值**，只用来展示字段结构——真实值
随你自己的 Zotero 库而定（`zotero_version` 随 Zotero 发行版变化，`schema_version`
随 Zotero 数据库 schema 变化）。判据很简单：**不要拿示例里的数字去比对、也不要
把它当成「应该有这么多」的预期**。

`ping` 通过 = 后面所有子命令都能用。连不上时会以**退出码 3** 退出，并在 stderr
打印可照着做的修复步骤，而不是一句「失败了」。

---

## 3. 配置

命令行开关优先于环境变量；环境变量优先于内置默认值。

| 环境变量 | 默认值 | 作用 |
| --- | --- | --- |
| `RV_ZOTERO_API` | `http://127.0.0.1:23119/api` | Local API 基址 |
| `RV_ZOTERO_LIBRARY` | `users/0` | 库；`users/0` 是「当前用户」别名 |
| `RV_ZOTERO_STORAGE` | 见下 | Zotero `storage/` 目录，用于解析附件磁盘路径 |
| `RV_ZOTERO_DATA_DIR` | 见下 | Zotero 数据目录（会自动接 `storage`） |

对应的命令行开关是 `--api` / `--library`；`attachment` 子命令另有 `--storage`。

> **Zotero 数据目录在哪**：Zotero → 设置 → 高级 → 文件和文件夹。
> 附件默认存放在该目录下的 `storage/<附件 key>/<文件名>`。

---

## 4. 退出码

| 码 | 含义 | 你会看到什么 |
| --- | --- | --- |
| `0` | 成功 | 结果正常输出 |
| `2` | 参数错误 | stderr 说明哪个参数不对，能修的直接给改法 |
| `3` | 连不上 Zotero | stderr 打印 5 条可执行的排查步骤 |
| `4` | Zotero 返回非 200 | 带上 HTTP 状态码与响应体片段 |
| `5` | 没找到 | 条目/附件/集合不存在 |

脚本里请判退出码，不要去 grep 输出文本。

---

## 5. 输出格式

**默认 JSON**（UTF-8、`ensure_ascii=False`，中文原样输出，不转成 `\uXXXX`）。
`--human` 切换成人类可读的对齐表格（CJK 宽度已按双宽处理）。

`--json` / `--human` 写在子命令**前面或后面都生效**；两个同时给会得到退出码 2
（自相矛盾的请求，报错比悄悄挑一个诚实）。

```bash
python rvzotero.py --human ping          # 前置有效
python rvzotero.py ping --human          # 后置也有效
python rvzotero.py --human --json ping   # 退出码 2
```

---

## 6. 子命令

| 子命令 | 作用 |
| --- | --- |
| `ping` | 探活，报告 Zotero 版本 / 库 id / 库版本 |
| `search` | 检索条目（标题/作者/年份，或全文） |
| `get` | 取单个条目详情，可选带上笔记 / 附件 / 批注 |
| `children` | 列子对象（attachments / notes / annotations） |
| `annotations` | 取批注：**默认全量**分页、跨全部附件、颜色过滤、评论归属切分 |
| `retrieve` | 在附件全文里做 BM25 排序，返回片段 |
| `attachment` | 解析附件的磁盘路径 |
| `fulltext` | 取附件全文（`--out` 落盘） |
| `export` | 导出引用（bibtex / biblatex / ris / csljson / citation） |
| `collections` | 列集合（含层级） |
| `tags` | 列标签（默认全部） |
| `searches` | 列保存的检索（默认全部） |
| `changes` | 库增量（基线 / 快照差分） |

### 主要参数

| 子命令 | 参数 |
| --- | --- |
| `search` | `--query/-q` `--qmode{titleCreatorYear,everything}` `--item-type` `--tag` `--collection` `--top` `--limit` `--offset` `--sort` `--direction` |
| `get` | `--key/-k` `--include` `--fields` `--color` `--attachment` `--split-comment` |
| `children` | `--key/-k` `--item-type` `--include` `--limit` `--offset` `--split-comment` |
| `annotations` | `--key/-k` `--color` `--attachment` `--first-attachment` `--all` `--limit` `--page-size` `--split-comment` |
| `retrieve` | `--key/-k` `--query/-q` `--passages` `--passage-chars` `--max-chars` |
| `attachment` | `--key/-k` `--all` `--storage` |
| `fulltext` | `--key/-k` `--pages A-B` `--out` |
| `export` | `--key/-k` `--format` `--style` `--out` |
| `tags` | `--limit` `--offset` `--query/-q` |
| `changes` | `--since` `--db` |

**默认值口径（结构性读取一律全量）**：`annotations` / `children` / `collections` /
`tags` / `searches` 不传 `--limit` 时都翻完全部分页、输出全部命中；`--limit N` 是
显式上限，只用于预览。只有检索型子命令（`search` 默认 25 条、`retrieve` 默认
若干片段）保留默认条数上限——那里「少给」是功能，不是丢数据。`annotations --all`
仍然可用，现在是显式无操作。

```bash
# 全量（默认行为，无需 --all）
python rvzotero.py annotations --key ABCD1234

# 只看前 10 条（显式上限，此时 truncated=true 并附 note 说明）
python rvzotero.py annotations --key ABCD1234 --limit 10
```

**`--include` 必须用复数**（`attachments,notes,annotations`），与 Zotero API 口径一致；
写成单数会得到退出码 2，并在报错里直接给出复数写法。

```bash
python rvzotero.py children --key ABCD1234 --include attachments,notes,annotations
```

> 早期版本的 `children --help` 把取值印成单数 `attachment,note,annotation`，与实现相反。
> **这是过去时**，现已修正并有测试锁死（`TestIncludePluralOnly` 会同时校验帮助文本与行为）。

**读批注请用 `annotations --key <KEY>` 作为首选入口**：它给全量、带颜色过滤、带 `🔤`
区间切分、带 Zotero 官方页码标签。`children --include annotations` 在真实 API 上
**同样有效**（条目级过滤会跨附件聚合），但它输出的是每一类子对象的**条数**，没有颜色过滤、
没有评论切分、没有页码标签——适合盘家底，不适合当证据来源。

### 颜色

`--color` 接受颜色名或十六进制值，两者等价：

| 名称 | 十六进制 | 约定含义 |
| --- | --- | --- |
| `yellow` | `#ffd400` | 生词 |
| `green` | `#5fb236` | 定义术语或术语解释 |
| `blue` | `#2ea8e5` | 影响、观点、解决方法 |
| `red` | `#ff6666` | 缺陷、现有问题、现有挑战 |
| `purple` | `#a28ae5` | 与我的研究相关 |

颜色名无法识别时**报退出码 2**，不会静默返回 0 条——「0 条」和「颜色写错了」
必须能分清。

```bash
python rvzotero.py annotations --key ABCD1234 --color purple      # 等价于 --color #a28ae5
```

---

## 7. 必须知道的 7 个坑

这些都是真实 Local API 的行为，工具已经内置处理，但**看输出的人也得知道**。

**① 裸调 `/children` 会静默漏掉全部批注。**
`GET /items/<key>/children` 不带 `?itemType=annotation` 时**不给批注且不报错**：
条目 key → 只回附件与笔记；附件 key → **空数组**。
带 `?itemType=annotation` 时，条目 key 会**跨附件聚合**（真机实测 130 条），
附件 key 只回它自己的批注。

**读批注的首选入口是 `annotations --key <KEY>`**——全量、颜色过滤、`🔤` 区间切分、
Zotero 官方页码标签俱全。`children --include annotations`（**只认复数**）在真实 API 上
**同样有效**，但只给每一类的**条数**，没有颜色过滤 / 评论切分 / 页码标签，适合盘家底。

**② 批注在 100 条处静默截断。**
`?itemType=annotation` 单页最多 100 条，传 `limit=1000` 也没用。唯一可靠的总数是
`Total-Results` 响应头。`annotations` 默认 `start` 翻页取全量；`children` 默认也翻完
全部页，只有你显式传 `--limit` 时才会撞上单页上限并在输出里给出 `warning`。

**③ Local API 回 HTTP/1.0。**
Python `urllib` 正常；PowerShell 的 `Invoke-RestMethod` 会握手失败。别在 PowerShell
里解析这个 API 的 JSON——用本工具，或 `curl.exe -o` 落盘再用 Python 读。

**④ 批注可能只挂在某一个附件上。**
一篇论文常有原文 / 双语 / 译文多个 PDF，批注只落在其中一个（甚至只落在译文那份）。
`annotations` 默认**逐个附件都查**，不会漏。

**⑤ 父条目查询是递归的，会和逐附件查询重复。**
`/items/<父条目>/children?itemType=annotation` 会递归返回其所有附件下的批注。
工具在合并结果后**按 key 去重**。注意 `attachments` 各行是**去重前**的分项读数，
相加会大于总数——输出里的 `dedupeNote` 会说明这一点。

**⑥ `/fulltext` 会静默忽略 `?page=N`。**
传任何页码都返回**整篇**。所以拿不到 PDF 的真实逐页边界，`fulltext --pages A-B`
只是在**本地**按字符偏移切分（页码是估算值）。逐页请求等于把同一篇下载 N 遍，
工具只请求一次。

**⑦ 颜色过滤 × 条数上限会互相干扰。**
如果实现是「数够 N 条就停」，`--color` 就会只扫前几页，报告一个**假的小数字**。
正确顺序是：先全量分页扫完 → 再按颜色过滤 → 最后才截断。工具按此实现。

---

## 8. 一条贯穿全局的原则

> **凡是「返回的比存在的少」，都必须显式说出来。**

Zotero Local API 最危险的地方不是报错，是**不报错地少给**。所有可能隐藏数据的
地方都会在输出里显式报告：

| 字段 | 含义 |
| --- | --- |
| `total` | 本次实际返回的条数 |
| `matchedTotal` | 过滤条件命中、且已扫描到的总条数 |
| `scanned` | 为得到上面的数字，实际扫过了多少条 |
| `truncated` | 是否因为 `--limit` 而少给了 |
| `deduped` | 因父子递归重复而合并掉的条数 |
| `note` | 人类可读的说明（截断原因、改法） |
| `warning` | 需要使用者注意的行为（如 `children` 撞上单页上限） |

```bash
python rvzotero.py annotations --key ABCD1234 --limit 10
```

```json
{
  "key": "ABCD1234",
  "colorFilter": null,
  "total": 10,
  "matchedTotal": 130,
  "scanned": 130,
  "deduped": 130,
  "truncated": true,
  "countsByColor": { "yellow": 26, "green": 26, "blue": 26, "red": 26, "purple": 26 },
  "note": "本条目共命中 130 条，按 --limit=10 只输出前 10 条；去掉 --limit 即输出全部。",
  "dedupeNote": "父条目递归查询与逐附件查询命中同一批批注，已按 key 去重 130 条；`attachments` 各行是**去重前**的分项读数，相加会大于总数。"
}
```

**默认就是全量。** 结构性读取（`annotations` / `children` / `collections` /
`tags` / `searches`）不带 `--limit` 时一律翻完全部分页再输出全部命中——批注就是
证据层本身，把最大的坑留在默认路径上不可接受。`--limit N` 是**显式**上限，只用来
快速预览；只有显式传了它，`truncated` 才可能为 `true`。`annotations --all` 仍然可用，
现在是一个**显式无操作**（保留只为把「我就是要全部」的意图写清楚）。

看到 `truncated: true`，说明是你自己要了上限；去掉 `--limit` 即可拿到全量。

---

## 9. 页码：官方标注 vs 估算

这是最容易被误用的一处，工具在输出里强制区分：

| 来源 | 字段 | 可信度 |
| --- | --- | --- |
| Zotero 批注 | `annotationPageLabel` → `page` | **官方标注**，可引用 |
| 全文片段 | `page` + `pageEstimated: true` + `pageSource: "char_offset_estimate"` | **估算值**，仅供参考 |
| 本地切片 | `pageEstimated: true` + `pageSource: "local_char_offset_slice"` | **估算值**，仅供参考 |

```bash
python rvzotero.py retrieve --key ATT00001 --query "evaluation protocol" --passages 2
```

```json
{
  "key": "ATT00001",
  "attachmentKey": "ATT00001",
  "query": "evaluation protocol",
  "totalPages": 27,
  "indexedPages": 27,
  "chars": 20627,
  "passageCount": 324,
  "rawPassageCount": 324,
  "mergedPassageCount": 324,
  "keptChars": 20304,
  "droppedPassages": 0,
  "droppedChars": 0,
  "fallbackApplied": false,
  "minCharsUsed": 60,
  "cjkMinChars": 20,
  "cjkHeavy": false,
  "matched": 324,
  "returned": 1,
  "truncated": true,
  "results": [
    {
      "id": "10:110",
      "page": 10,
      "pageIndex": 9,
      "pageEstimated": true,
      "pageSource": "char_offset_estimate",
      "charOffset": 6932,
      "score": 0.0015,
      "snippet": "Page 111 line about benchmarks, evaluation and neutral metrics.",
      "chars": 63
    }
  ],
  "note": "页码由「字符偏移 ÷ 每页平均字符数」**估算**得到，不是 PDF 的真实分页——Local API 的 ?page=N 参数被静默忽略，拿不到逐页文本。需要精确页码请改用 `annotations`（批注带 Zotero 官方页码标签）。",
  "passageNote": "片段门槛：拉丁文本 60 字符、CJK 为主的片段 20 字符（本篇非 CJK 为主）；短片段先向后合并再判定，只有整段不含字母/数字/CJK 的排版残留才会被丢弃——丢了多少见 droppedPassages。"
}
```

**片段计数必须能对上账**：`rawPassageCount`（第一层切出多少）→ `mergedPassageCount`
（短片段合并后）→ `passageCount`（最终参与检索）→ `keptChars`；丢了多少在
`droppedPassages` / `droppedChars` 里。**任何非空全文，`keptChars` 必须 > 0**——
「有内容却 0 片段」是不允许出现的结果。

**短片段不是「短了就扔」**：先向后合并（上界 `--passage-chars`，默认 700），合并不掉的
仍然保留。只有整段不含字母/数字/CJK 的排版残留（表格线、分隔符）才丢弃。
CJK 为主的片段门槛降到 **20 字符**（拉丁仍为 60）——中文一个字就是一个词，
拿 60 字符卡中文会把正常段落判成碎片。门槛按**每个片段自己**的脚本判定。

> 这条纪律有真实代价：早期实现在「切出多于 3 段」时把短片段整块丢掉且不报。
> 真机复测那份 245167 字符的中文 PDF：原始 **4526** 段只剩 **1763** 段，
> **2763 段（61%）无声消失**。修正后同一篇文件 **0 段被丢弃**，
> `keptChars` 242973 / 245167（99.1%）。当年漏网的原因是测试样本太小，
> 恰好落在「片段数 ≤ 3」的直通分支上——现在有专门的回归测试锁死「合并 / 过滤」
> 分支必须真的被执行。

**`passageCount == 0` 有三种，输出里分得开**：附件全文为空 → `warning` 说「没有可检索
内容」；全文非空但切分后为空 → `warning` 说「这是切分后为空，不等于全文没有内容」；
有片段但无命中 → `matchNote` 说「确实没有匹配」。三种的下一步动作完全不同。

**引用页码时请用 `annotations` 的 `page`，不要用 `retrieve` 的 `page`。**
估算页码绝不会伪装成官方标注：它永远带着 `pageEstimated: true`。

```bash
python rvzotero.py fulltext --key ATT00001              # 整篇
python rvzotero.py fulltext --key ATT00001 --pages 3-4  # 本地切片（估算页码）
python rvzotero.py fulltext --key ATT00001 --out paper.txt
```

切片时 `contentIsWholeDocument` 为 `false`，而 `fetchedWholeDocument` 始终为 `true`
——因为 Zotero 只肯给整篇，「取回了整篇」不等于「输出的就是整篇」。

---

## 10. 批注评论的归属切分

翻译插件会在**它自己生成的文本**外面套一对 `🔤` 标记。评论的真实形态常见两种：

```
🔤机器译文🔤
```

```
🔤机器译文🔤
研究者自己手写的话
```

第二种形态里，**区间外的话是研究者本人的**，必须保留。切分是**按区间**做的，
不是「整条里含不含 🔤」——后者会把研究者的批注一起丢掉。

```bash
python rvzotero.py annotations --key ABCD1234 --limit 1 --split-comment
```

```json
{
  "key": "ABCD1234",
  "page": "12",
  "pageLabel": "12",
  "color": "#a28ae5",
  "colorName": "purple",
  "text": "Highlighted sentence about the topic.",
  "comment": "🔤机器译文🔤\n研究者自己写的话",
  "commentParts": {
    "raw": "🔤机器译文🔤\n研究者自己写的话",
    "machine_texts": ["机器译文"],
    "researcher_text": "研究者自己写的话",
    "unmarked_text": "",
    "researcher_comment": "研究者自己写的话",
    "has_machine_mark": true,
    "classification": "machine_plus_researcher"
  }
}
```

`classification` 取值：

| 值 | 含义 |
| --- | --- |
| `researcher` | 整条没有 `🔤` 标记 → 研究者自己敲的（空评论也归这里） |
| `tool_generated` | 只有 `🔤…🔤` 区间，区间外无内容 |
| `machine_plus_researcher` | 机器区间 + 区间外还有研究者的话 |
| `mixed` | 未切分时 `unmarked_text` 与 `🔤` 标记同时存在（少见形态） |

**判「有没有研究者的话」要看 `researcher_comment` 是否为空**，不要只看 `classification`
——空评论也会落在 `researcher` 上。

**取研究者本人的话就用 `researcher_comment`**；`machine_texts` 是插件的机器词典，
不是研究者的话，也永远不是论文原文。

---

## 11. 离线测试

单测**不需要 Zotero 在运行**——HTTP 层由 `tests/mock_zotero.py` 用标准库
`http.server` 提供，并刻意复现了上面 7 个坑里的关键几条（HTTP/1.0、
`Total-Results` 头、裸 `children` 返回 0 条批注、100 条截断、`?page=N` 被忽略、
`format=citation` 返回 400、CJK 的 `🔤…🔤` 评论）。

```bash
python tests/test_rvzotero.py
```

想手动拿 mock 玩：

```bash
python tests/mock_zotero.py 23199
# 另一个终端
python rvzotero.py --api http://127.0.0.1:23199/api ping
```

mock 自带一份固定 fixture（虚构 key `ABCD1234` / 附件 `ATT00001`，130 条批注），
所以测试结果稳定、可复现，也不依赖任何真实资料。

**mock 的语义以真实 Zotero 实测为准**，`tests/mock_zotero.py` 顶部写明了这一点。
mock 只能验证「工具在 mock 建模的世界里自洽」，**不能**验证工具与真实 API 一致——
本项目已因此吃过一次亏：mock 曾把「条目级 `?itemType=annotation` 只对附件 key 生效」
钉死，于是离线全绿、真机结论相反。**凡是对真实外部接口的断言，先在真机上跑一遍；
mock 与真机不一致时，先怀疑 mock。**

测试里刻意锁死了几条「反直觉但真实」的行为，改代码时别把它们「修正」掉：

- 裸 `/children` 不给批注；附件 key 的裸 `/children` 回**空数组**；
- **条目 key** 的 `?itemType=annotation` **跨附件聚合**（130 条 / 2 页），附件 key 只回自己的；
- 批注总数是 **130 而不是 100**（分页补齐）；
- `🔤…🔤\n研究者的话` 切出**两段**，研究者的话不能丢；
- 任何非空全文切分后 `keptChars` **> 0**；
- 「合并 / 过滤」分支必须**真的被执行**（小样本会落回直通分支——那正是当年漏网的原因；
  这条断言写进了 `TestPassageSplitterNeverDropsSilently`）；
- 连不上 Zotero 退出码 `3`，stderr 里必须有**可执行**的修复步骤。

---

## 12. 排错

**退出码 3（连不上）** —— 按 stderr 打印的顺序查：Zotero 是否在运行 → 本地 API
是否已开启（改完要重启）→ 端口是否被改过（默认 23119）→ 是否被安全软件拦了回环
端口。想先确认脚本本身没问题，跑 `python tests/test_rvzotero.py`。

**退出码 5（没找到）** —— 条目 key 是 8 位大写字母数字。附件全文必须用**附件 key**
调用；用父条目 key 调 `/fulltext` 会 404（`fulltext` 子命令会替你自动挑最佳附件）。

**退出码 4（Zotero 报错）** —— 常见于导出格式：Local API **不支持
`format=citation`**（返回 400）。`export --format citation` 是本地近似排版；
要严格 CSL 请用 `--format csljson` 交给外部 CSL 处理器。

**中文乱码** —— 工具启动时会显式把 stdout/stderr 切到 UTF-8。若在老旧终端里仍乱码，
设 `PYTHONIOENCODING=utf-8`。

**`attachment` 的 `exists: false`** —— 路径解析出来了但本机没这个文件。常见原因：
`storage` 目录不在默认位置（用 `--storage` 或 `RV_ZOTERO_STORAGE` 指定）、用了自定义
数据目录、或该附件是 `linked_file` 且原文件已被移走。`pathKind` 会告诉你是哪一类
（`stored` / `linked_file` / `linked_url`）；`linked_url` 本来就没有本地文件。

---

## 13. 边界

- **只读**：只发 GET，不写、不改、不删 Zotero 里的任何东西。
- **不联网**：只访问本机回环地址。
- **无依赖**：纯标准库，单文件可直接拷走。
- **不做 CSL 排版**：`citation` 是近似排版，严格引用请走 `csljson` + 外部处理器。
