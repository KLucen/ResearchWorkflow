#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""rvzotero —— 可移植、只读的 Zotero 访问层（纯 Python 3.8+ 标准库）。

设计目标
========
完全替代某一款特定 Agent 的 Zotero 插件：只要机器上装了 Python 3.8+ 和
正在运行的 Zotero（已开启「允许本机其他应用访问」），任何 Agent / 脚本都能通过
本文件读取文献、批注、全文。**只读**，绝不写入 Zotero。

用法概览
========
    python rvzotero.py ping
    python rvzotero.py search --query "survey" --item-type journalArticle --limit 20
    python rvzotero.py get --key ABCD1234 --include notes,attachments,annotations
    python rvzotero.py children --key ABCD1234
    python rvzotero.py annotations --key ABCD1234 --color purple --split-comment
    python rvzotero.py retrieve --key ABCD1234 --query "research question" --passages 5
    python rvzotero.py attachment --key EFGH5678
    python rvzotero.py fulltext --key EFGH5678 --out fulltext.txt
    python rvzotero.py export --key ABCD1234 --format bibtex
    python rvzotero.py collections
    python rvzotero.py tags --limit 50
    python rvzotero.py changes --since 123 --db changes.json

坐标事实源
==========
`<VAULT>/00_System/Zotero_Access.md`（五色批注语义、评论归属规则）。
本工具把「读」做扎实，「判定」交给上层。

═══════════════════════════════════════════════════════════════════════════════
⚠ 六个已经被真实环境验证过的坑（本工具的核心价值，改代码前请先读）
═══════════════════════════════════════════════════════════════════════════════
1. **children 不带 itemType=annotation 会静默返回 0 条批注**（HTTP 200，不报错）。
   这是最危险的失败模式：看起来「这篇论文没有批注」，其实是查询方式错了。
   本工具的 `annotations` / `children --include annotations` 永远显式带上该参数。

2. **批注在 100 条处静默截断**。`/items/<key>/children?itemType=annotation&limit=100`
   只回前 100 条且不报错。必须用 `start` 翻页，并用响应头 `Total-Results`
   判断真实总数。本工具的 `--all` 分页循环会一直取到 Total-Results 为止，
   并对「预期总数 > 实际取到条数」的情况直接抛错，绝不静默少给。

3. **Zotero Local API 回 HTTP/1.0**。Python `urllib` 正常，但
   PowerShell `Invoke-RestMethod` 会在握手阶段失败。
   Windows 上请用本脚本，或 `curl.exe -o file.json`，不要用 `Invoke-RestMethod`。

4. **批注可能只挂在某一个附件上**。一篇论文常见「原文 PDF + 双语 PDF + 译文 PDF」
   多个附件，批注只存在于研究者实际阅读的那一个。只查第一个附件会漏。
   本工具提供 `--attachment` 精确指定，以及在父条目上聚合全部附件的用法。

5. **`/items/<key>/fulltext` 只接受附件 key**，用父条目 key 调用返回 404。
   本工具会自动把父条目 key 解析成它最好的 PDF 附件。

6. **`format=citation` 不被 Local API 支持**（返回 400 Invalid 'format'）。
   `bibtex` / `biblatex` / `ris` / `csljson` 支持。`citation` 由本工具
   在本地按近似 CSL 规则排版（`--style apa|ieee|gb-t-7714`）。

退出码
======
    0 成功
    2 参数错误
    3 连不上 Zotero（附修复指引）
    4 Zotero 返回了非 200/404 的错误
    5 未找到目标条目 / 附件 / 集合
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

__version__ = "1.0.0"

# --------------------------------------------------------------------------- #
# 常量
# --------------------------------------------------------------------------- #

DEFAULT_API_BASE = "http://127.0.0.1:23119/api"
DEFAULT_LIBRARY = "users/0"
DEFAULT_TIMEOUT = 20.0
DEFAULT_PAGE_SIZE = 100
MAX_PAGE_SIZE = 100

#: 批注页大小。Zotero 在 100 条处静默截断，所以这是唯一安全的页大小。
ANNOTATION_PAGE_SIZE = 100

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_CONNECTION = 3
EXIT_HTTP = 4
EXIT_NOT_FOUND = 5

#: 五色批注通道。<VAULT>/00_System/Zotero_Access.md 是语义事实源。
ANNOTATION_COLORS = {
    "yellow": "#ffd400",   # 生词       -> 03_Vocabulary/（不进证据、不进 Wiki）
    "green": "#5fb236",    # 定义/术语  -> E 对象 -> concept 页
    "blue": "#2ea8e5",     # 影响/观点/解决方法 -> E 对象 -> 主张登记表（默认 +）
    "red": "#ff6666",      # 缺陷/问题/挑战     -> E 对象 -> − 证据 / gap/
    "purple": "#a28ae5",   # 与我的研究相关     -> research_position 判定首要依据
}
COLOR_BY_HEX = {v.lower(): k for k, v in ANNOTATION_COLORS.items()}

#: 机器词典区间标记。区间内是翻译插件产物（tool_generated），永不作论文原文。
MACHINE_MARK = "\U0001f524"
#: Zotero 对 `/items/<父条目>/children?itemType=annotation` 会**递归**返回其所有附件下的
#: 批注。这个标签用来如实说明那一行是递归查询的结果，不是「直属父条目的批注」。
PARENT_RECURSIVE_LABEL = "(父条目递归查询：含各附件批注，已按 key 去重)"  # 🔤

#: 默认分页安全上限，防止异常情况下无限翻页。
MAX_PAGES = 500

CONNECTION_HINT = """\
连不上 Zotero Local API。请依次检查：
  1. Zotero 是否正在运行（未运行时 23119 端口无人监听）。
     启动：Windows 直接双击 Zotero；命令行可用
       Start-Process "<ZOTERO_EXE>" -ArgumentList "-no-remote","-profile","<ZOTERO_PROFILE>"
  2. Zotero 里是否已开启本地 API：
     设置 → 高级 → 勾选「Allow other applications on this computer to
     communicate with Zotero」（中文界面：允许其他应用与 Zotero 通信）。
     改完需要重启 Zotero 才生效。
  3. 端口是否被改过：默认 23119，可用环境变量 RV_ZOTERO_API 覆盖，
     形如 http://127.0.0.1:<端口>/api
  4. 是否被安全软件拦截了本机回环端口。
  5. 想先离线验证脚本本身：python tests/test_rvzotero.py（不需要 Zotero 在运行）。
"""


# --------------------------------------------------------------------------- #
# 异常
# --------------------------------------------------------------------------- #

class RvError(Exception):
    """本工具所有可预期错误的基类。"""

    exit_code = EXIT_HTTP


class UsageError(RvError):
    """参数错误。"""

    exit_code = EXIT_USAGE


class ConnectionFailure(RvError):
    """连不上 Zotero。"""

    exit_code = EXIT_CONNECTION

    def __str__(self) -> str:  # pragma: no cover - 简单拼接
        return "%s\n\n%s" % (self.args[0], CONNECTION_HINT)


class ApiError(RvError):
    """Zotero 返回了错误状态码。"""

    exit_code = EXIT_HTTP

    def __init__(self, status, message, url=""):
        super().__init__("HTTP %s from %s: %s" % (status, url or "<api>", message))
        self.status = status
        self.message = message
        self.url = url


class NotFound(RvError):
    """目标不存在。"""

    exit_code = EXIT_NOT_FOUND


# --------------------------------------------------------------------------- #
# HTTP 客户端
# --------------------------------------------------------------------------- #

class Response(object):
    """一次 HTTP 响应的最小封装。"""

    __slots__ = ("status", "headers", "body", "url")

    def __init__(self, status, headers, body, url):
        self.status = status
        self.headers = headers      # 全小写键的 dict
        self.body = body            # str（已按 UTF-8 解码）
        self.url = url

    def header(self, name, default=None):
        return self.headers.get(name.lower(), default)

    @property
    def total_results(self):
        """响应头 Total-Results：不受当前分页影响的真实总数。"""
        raw = self.header("total-results")
        if raw is None:
            return None
        try:
            return int(raw)
        except (TypeError, ValueError):
            return None

    @property
    def last_modified_version(self):
        """响应头 Last-Modified-Version：库版本号，用于 changes 基线。"""
        raw = self.header("last-modified-version")
        if raw is None:
            return None
        try:
            return int(raw)
        except (TypeError, ValueError):
            return None

    def json(self):
        if not self.body.strip():
            return None
        try:
            return json.loads(self.body)
        except ValueError as exc:
            raise ApiError(self.status, "响应不是合法 JSON：%s" % exc, self.url)


class ZoteroClient(object):
    """Zotero Local API 的只读客户端。

    所有网络访问都经过 :meth:`request`，方便测试时替换 / 打桩。
    """

    def __init__(self, api_base=None, library=None, timeout=DEFAULT_TIMEOUT,
                 user_agent=None, retries=2, retry_delay=0.4):
        base = api_base or os.environ.get("RV_ZOTERO_API") or DEFAULT_API_BASE
        self.api_base = base.rstrip("/")
        lib = library or os.environ.get("RV_ZOTERO_LIBRARY") or DEFAULT_LIBRARY
        self.library = lib.strip("/")
        self.timeout = float(timeout)
        self.user_agent = user_agent or ("rvzotero/%s (python-urllib)" % __version__)
        self.retries = int(retries)
        self.retry_delay = float(retry_delay)
        self._item_cache = {}

    # -- 基础 -------------------------------------------------------------- #

    def url(self, path, params=None):
        """拼出完整 URL。path 形如 `/items/KEY/children`。"""
        if not path.startswith("/"):
            path = "/" + path
        url = "%s/%s%s" % (self.api_base, self.library, path)
        if params:
            clean = [(k, v) for k, v in params.items() if v is not None and v != ""]
            if clean:
                url += "?" + urllib.parse.urlencode(clean, doseq=True)
        return url

    def request(self, path, params=None, accept="application/json"):
        """发一次 GET，返回 :class:`Response`。连不上时抛 ConnectionFailure。"""
        url = self.url(path, params)
        last_exc = None
        for attempt in range(self.retries + 1):
            req = urllib.request.Request(url, method="GET")
            req.add_header("Accept", accept)
            req.add_header("User-Agent", self.user_agent)
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    raw = resp.read()
                    return Response(
                        resp.status,
                        {k.lower(): v for k, v in resp.getheaders()},
                        raw.decode("utf-8", "replace"),
                        url,
                    )
            except urllib.error.HTTPError as exc:
                # HTTPError 本身是个可读的文件对象；不关会漏 socket（还会触发
                # ResourceWarning）。读干净后必须显式 close。
                try:
                    body = exc.read().decode("utf-8", "replace")
                    headers = {k.lower(): v for k, v in (exc.headers or {}).items()}
                    code = exc.code
                finally:
                    exc.close()
                if code == 404:
                    return Response(404, headers, body, url)
                # 5xx 值得重试一次；4xx 是确定性错误，直接抛。
                if 500 <= code < 600 and attempt < self.retries:
                    last_exc = "HTTP %d" % code
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                raise ApiError(code, body.strip()[:500], url)
            except urllib.error.URLError as exc:
                last_exc = exc
                if attempt < self.retries:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
            except OSError as exc:  # 连接被拒 / 超时 / 端口不通
                last_exc = exc
                if attempt < self.retries:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
        raise ConnectionFailure(
            "无法访问 %s（%s）" % (self.api_base, last_exc)
        )

    def get_json(self, path, params=None):
        """GET 并解析 JSON；404 时抛 NotFound。"""
        resp = self.request(path, params)
        if resp.status == 404:
            raise NotFound("未找到：%s" % resp.url)
        if resp.status != 200:
            raise ApiError(resp.status, resp.body.strip()[:500], resp.url)
        return resp.json()

    def get_text(self, path, params=None, accept="text/plain"):
        """GET 并返回原始文本（用于 format=bibtex 等导出）。"""
        resp = self.request(path, params, accept=accept)
        if resp.status == 404:
            raise NotFound("未找到：%s" % resp.url)
        if resp.status != 200:
            raise ApiError(resp.status, resp.body.strip()[:500], resp.url)
        return resp.body

    # -- 发现 -------------------------------------------------------------- #

    def ping(self):
        """探活。返回 dict；连不上会抛 ConnectionFailure。"""
        info = {
            "ok": True,
            "api_base": self.api_base,
            "library": self.library,
            "zotero_version": None,
            "api_version": None,
            "schema_version": None,
            "server_id": None,
            "last_modified_version": None,
            "total_items": None,
            "library_id": None,
            "library_name": None,
        }
        resp = self.request("/items/top", {"limit": 1})
        if resp.status == 404:
            resp = self.request("/items", {"limit": 1})
        if resp.status != 200:
            raise ApiError(resp.status, resp.body.strip()[:500], resp.url)
        info["zotero_version"] = resp.header("x-zotero-version")
        info["api_version"] = resp.header("zotero-api-version")
        info["schema_version"] = resp.header("zotero-schema-version")
        info["server_id"] = resp.header("zotero-server-id")
        info["last_modified_version"] = resp.last_modified_version
        info["total_items"] = resp.total_results
        data = resp.json() or []
        if data:
            lib = data[0].get("library") or {}
            info["library_id"] = lib.get("id")
            info["library_name"] = lib.get("name")
            if info["library"] == "users/0" and lib.get("id"):
                info["resolved_library"] = "users/%s" % lib["id"]
        return info

    def list_items(self, query=None, qmode=None, item_type=None, tag=None,
                   sort=None, direction=None, limit=25, start=0, top=False):
        """列举 / 检索条目（不含批注等子条目）。"""
        path = "/items/top" if top else "/items"
        params = {
            "q": query or None,
            "qmode": qmode or None,
            "itemType": item_type or None,
            "tag": tag or None,
            "sort": sort or None,
            "direction": direction or None,
            "limit": limit,
            "start": start,
        }
        resp = self.request(path, params)
        if resp.status == 404 and path == "/items/top":
            # 旧版 Zotero 可能没有 /items/top
            resp = self.request("/items", params)
        if resp.status != 200:
            raise ApiError(resp.status, resp.body.strip()[:500], resp.url)
        return resp.json() or [], resp

    def list_collection_items(self, collection_key, query=None, limit=25, start=0,
                              sort=None, direction=None, top=False):
        path = "/collections/%s/items%s" % (collection_key, "/top" if top else "")
        params = {
            "q": query or None,
            "sort": sort or None,
            "direction": direction or None,
            "limit": limit,
            "start": start,
        }
        resp = self.request(path, params)
        if resp.status == 404:
            raise NotFound("未找到集合 %s（用 `collections` 子命令查可用集合）" % collection_key)
        if resp.status != 200:
            raise ApiError(resp.status, resp.body.strip()[:500], resp.url)
        return resp.json() or [], resp

    def get_item(self, key):
        """按 key 取单个对象（父条目 / 子条目 / 附件 / 批注都可）。"""
        if key in self._item_cache:
            return self._item_cache[key]
        resp = self.request("/items/%s" % key)
        if resp.status == 404:
            raise NotFound(
                "未找到条目 %s。可能原因：key 写错 / 属于别的库（当前库 %s）/ "
                "条目已被删除。用 `search` 或 `collections` 确认 key。" % (key, self.library)
            )
        if resp.status != 200:
            raise ApiError(resp.status, resp.body.strip()[:500], resp.url)
        obj = resp.json()
        self._item_cache[key] = obj
        return obj

    def try_get_item(self, key):
        """按 key 取对象；不存在返回 None（不抛异常）。"""
        try:
            return self.get_item(key)
        except NotFound:
            return None

    # -- 子对象：批注 / 附件 / 笔记 ---------------------------------------- #

    def list_children(self, key, item_type=None, limit=MAX_PAGE_SIZE, start=0):
        """列子对象。

        .. warning::
           **不传 item_type 时，Zotero 不会返回批注**（静默 0 条，HTTP 仍 200）。
           要拿批注必须显式传 ``item_type="annotation"``。这是本工具最想帮你避开的坑。
        """
        params = {"limit": limit, "start": start}
        if item_type:
            params["itemType"] = item_type
        resp = self.request("/items/%s/children" % key, params)
        if resp.status == 404:
            raise NotFound("未找到条目 %s 的子对象（父 key 是否存在？）" % key)
        if resp.status != 200:
            raise ApiError(resp.status, resp.body.strip()[:500], resp.url)
        return resp.json() or [], resp

    def list_children_all(self, key, item_type=None, page_size=MAX_PAGE_SIZE):
        """把某一类子对象**全部**翻完，返回 ``(items, total, pages)``。

        结构性读取默认就该是全量：子对象数超一页时，只取首页会**静默**少给。
        """
        out = []
        cursor = 0
        pages = 0
        total = None
        while True:
            batch, resp = self.list_children(key, item_type=item_type,
                                             limit=page_size, start=cursor)
            pages += 1
            if resp.total_results is not None:
                total = resp.total_results
            out.extend(batch)
            cursor += len(batch)
            if not batch or len(batch) < page_size or \
                    (total is not None and cursor >= total):
                break
            if pages >= MAX_PAGES:
                raise ApiError(
                    200, "子对象分页未走完（已取 %d 页 / %d 条，服务端报 %s 条）"
                         % (pages, len(out), total),
                    self.url("/items/%s/children" % key))
        return out, total, pages

    def list_annotations(self, key, color=None, all_pages=True,
                         page_size=ANNOTATION_PAGE_SIZE, max_items=None):
        """取某个条目（父条目或附件）下的批注，**自动分页突破 100 条截断**。

        分页正确性由「扫描是否走完」保证：要么服务端报的总数被判明已经取完，
        要么返回了不满一页的批次（说明到底了）。如果分页中途停下而两条件都不满足，
        直接抛错——**绝不静默少给批注**。

        ``color`` 只是**客户端过滤**：过滤在整套分页之上进行，所以即使只看紫色，
        也会把 130 条全扫一遍再筛，不会因为「这一页没有紫色」就提前结束。
        """
        page_size = max(1, min(int(page_size), MAX_PAGE_SIZE))
        wanted = normalize_color(color)
        collected = []
        scanned = 0
        start = 0
        expected = None
        pages = 0
        truncated = False
        while True:
            batch, resp = self.list_children(key, item_type="annotation",
                                             limit=page_size, start=start)
            pages += 1
            total = resp.total_results
            if expected is None:
                expected = total
            scanned += len(batch)
            for item in batch:
                ann = Annotation.from_api(item)
                if wanted and ann.color_name != wanted:
                    continue
                collected.append(ann)
            # 终止条件：服务端总数已取完，或返回了不满一页的批次。
            done = (not batch) or len(batch) < page_size or \
                   (expected is not None and scanned >= expected)
            if done or not all_pages or pages >= MAX_PAGES:
                break
            start += len(batch)

        if not all_pages and max_items is None:
            max_items = page_size
        if max_items is not None and len(collected) > max_items:
            truncated = True
            collected = collected[:max_items]
        if expected is not None and scanned < expected and pages >= MAX_PAGES:
            raise ApiError(
                200,
                "批注分页不完整：Total-Results=%s 只扫到 %s 条（%s），已达页数上限 %s"
                % (expected, scanned, key, MAX_PAGES),
                self.url("/items/%s/children" % key),
            )
        return collected, {"total": expected, "scanned": scanned,
                           "returned": len(collected), "pages": pages,
                           "truncated": truncated}

    def annotations_for_item(self, key, color=None, attachment=None,
                             all_attachments=True, page_size=ANNOTATION_PAGE_SIZE):
        """为一个条目取批注，自动处理「批注只挂在某一个附件上」。

        返回 ``(annotations, meta)``；meta 里有每个附件的命中数与扫描进度，便于诊断。
        **总是取全量**——颜色过滤在整套分页之上进行，截断交给调用方，
        这样「第 3 个附件上才有紫色批注」这类情况不会被页大小骗过去。
        """
        obj = self.get_item(key)
        data = obj.get("data") or {}
        item_type = data.get("itemType")

        targets = []          # [(attachment_key, 显示名)]
        if item_type == "attachment":
            targets.append((key, data.get("filename") or key))
        elif attachment:
            targets.append((attachment, attachment))
        else:
            children, _ = self.list_children(key, item_type="attachment", limit=MAX_PAGE_SIZE)
            pdfs = []
            others = []
            for child in children:
                cdata = child.get("data") or {}
                if cdata.get("contentType") == "application/pdf":
                    pdfs.append((child["key"], cdata.get("filename") or child["key"]))
                else:
                    others.append((child["key"], cdata.get("filename") or child["key"]))
            targets = pdfs + others if all_attachments else pdfs[:1]

        all_anns = []
        per_attachment = []
        scan_total = 0
        for att_key, name in targets:
            try:
                one, meta = self.list_annotations(att_key, color=color, page_size=page_size)
            except NotFound:
                one, meta = [], {"total": 0, "scanned": 0, "returned": 0,
                                 "pages": 0, "truncated": False}
            for ann in one:
                ann.attachment_key = att_key
                ann.attachment_name = name
            per_attachment.append({"attachment": att_key, "name": name,
                                   "count": len(one),
                                   "total": meta.get("total"),
                                   "scanned": meta.get("scanned"),
                                   "pages": meta.get("pages")})
            scan_total += meta.get("scanned") or 0
            all_anns.extend(one)

        # 也接受直接挂在父条目上的批注（少见，但存在）。
        # 注意：Zotero 对 `/items/<父条目>/children?itemType=annotation` 会**递归**返回
        # 其所有附件下的批注，所以这里极可能把上面已经取到的批注再拿一遍。
        # 后面的按 key 去重就是为此——不去重会让 `annotations` 的条数直接翻倍。
        if item_type != "attachment" and not attachment:
            try:
                direct, dmeta = self.list_annotations(key, color=color, page_size=page_size)
                fresh = []
                for ann in direct:
                    ann.attachment_key = key
                    ann.attachment_name = PARENT_RECURSIVE_LABEL
                    fresh.append(ann)
                if fresh:
                    per_attachment.append({"attachment": key,
                                           "name": PARENT_RECURSIVE_LABEL,
                                           "count": len(fresh), "total": dmeta.get("total"),
                                           "scanned": dmeta.get("scanned"),
                                           "pages": dmeta.get("pages"),
                                           "duplicateOfAttachments": True})
                    all_anns.extend(fresh)
            except NotFound:
                pass

        # 按批注 key 去重：父条目递归查询与逐附件查询会命中同一批批注。
        unique = []
        seen_keys = set()
        for ann in all_anns:
            if ann.key and ann.key in seen_keys:
                continue
            if ann.key:
                seen_keys.add(ann.key)
            unique.append(ann)

        unique.sort(key=lambda a: (a.sort_index or "", a.key))
        return unique, {"attachments": per_attachment, "returned": len(unique),
                        "scanned": scan_total, "colorFilter": normalize_color(color),
                        "deduped": len(all_anns) - len(unique)}

    def list_attachments(self, key):
        """取条目的附件子对象（只回附件，不含批注/笔记）。"""
        children, _ = self.list_children(key, item_type="attachment", limit=MAX_PAGE_SIZE)
        return [c for c in children if (c.get("data") or {}).get("itemType") == "attachment"]

    def list_notes(self, key):
        children, _ = self.list_children(key, item_type="note", limit=MAX_PAGE_SIZE)
        return [c for c in children if (c.get("data") or {}).get("itemType") == "note"]

    def best_attachment(self, key):
        """把父条目 key 解析为「最适合取全文」的附件。

        优先级：显式给定的附件 key > PDF > 其他带全文的附件。
        """
        obj = self.get_item(key)
        data = obj.get("data") or {}
        if data.get("itemType") == "attachment":
            return obj
        attachments = self.list_attachments(key)
        if not attachments:
            raise NotFound("条目 %s 下没有任何附件，无法取全文。" % key)
        pdfs = [a for a in attachments
                if (a.get("data") or {}).get("contentType") == "application/pdf"]
        return (pdfs or attachments)[0]

    # -- 全文 -------------------------------------------------------------- #

    def fulltext(self, key, page=None):
        """取附件全文；key 可以是父条目（自动解析为附件）。

        返回 ``{"content", "indexedPages", "totalPages", "attachment_key", ...}``。

        .. warning::
           **``page`` 参数在 Local API 上是被静默忽略的**（实测：传 page=1/2/27/28
           返回的 content 完全一致，md5 相同，都是整篇）。所以本工具不去按页取，
           而是取一次全文 + 用字符偏移估算页码（见 :func:`estimate_page`）。
           传 ``page`` 只是为了让调用方显式表达意图；返回值里 ``page`` 字段会标明。
        """
        obj = self.get_item(key)
        if (obj.get("data") or {}).get("itemType") != "attachment":
            att = self.best_attachment(key)
            att_key = att["key"]
        else:
            att_key = key
        resp = self.request("/items/%s/fulltext" % att_key)
        if resp.status == 404:
            raise NotFound(
                "附件 %s 没有全文（Zotero 未索引，或不是可索引的 PDF）。"
                "可先在该附件上右键「重新索引」；或确认它确实是 PDF。" % att_key
            )
        if resp.status != 200:
            raise ApiError(resp.status, resp.body.strip()[:500], resp.url)
        payload = resp.json() or {}
        payload["attachment_key"] = att_key
        payload["pageParamIgnored"] = page is not None
        return payload

    def fulltext_index(self, key):
        """取一次全文并切成带**字符偏移**的片段。

        返回 ``(passages, meta)``，passages 为 ``[(pid, text, offset), ...]``。
        只发一次请求——Local API 不支持按页取，逐页请求只会把同一篇全文下载 N 遍。
        """
        payload = self.fulltext(key)
        content = payload.get("content") or ""
        total_pages = payload.get("totalPages") or 1
        per_page = (len(content) / float(total_pages)) if total_pages else 0.0
        raw, stats = split_passages_report(content)
        passages = []
        for idx, (offset, text) in enumerate(raw):
            page = int(offset // per_page) + 1 if per_page > 0 else None
            passages.append(("%s:%s" % (page if page else 1, idx), text, offset))
        meta = {
            "attachment_key": payload.get("attachment_key"),
            "total_pages": total_pages,
            "indexed_pages": payload.get("indexedPages"),
            "chars": len(content),
            "chars_per_page_estimate": round(per_page, 1),
            "passage_count": len(passages),
            # 「返回的比存在的少」必须能一路报到 CLI 输出里，不能停在内部。
            "raw_passage_count": stats["rawPassages"],
            "merged_passage_count": stats["mergedPassages"],
            "kept_chars": stats["keptChars"],
            "dropped_passages": stats["droppedPassages"],
            "dropped_chars": stats["droppedChars"],
            "fallback_applied": stats["fallbackApplied"],
            "min_chars_used": stats["minCharsUsed"],
            "cjk_min_chars": stats["cjkMinChars"],
            "cjk_heavy": stats["cjkHeavy"],
            "passage_stats": stats,
        }
        return passages, meta

    # -- 集合 / 标签 -------------------------------------------------------- #

    def list_collections(self, limit=None, start=0):
        """列集合；默认取全量（自动分页）。"""
        if limit is None:
            out = []
            cursor = 0
            while True:
                resp = self.request("/collections", {"limit": MAX_PAGE_SIZE, "start": cursor})
                if resp.status != 200:
                    raise ApiError(resp.status, resp.body.strip()[:500], resp.url)
                batch = resp.json() or []
                out.extend(batch)
                total = resp.total_results
                cursor += len(batch)
                if not batch or (total is not None and cursor >= total) or \
                        len(batch) < MAX_PAGE_SIZE:
                    break
            return out
        resp = self.request("/collections", {"limit": limit, "start": start})
        if resp.status != 200:
            raise ApiError(resp.status, resp.body.strip()[:500], resp.url)
        return resp.json() or []

    def resolve_collection(self, ref):
        """把集合名或 key 解析为集合对象。"""
        if not ref:
            raise UsageError("集合引用为空")
        collections = self.list_collections()
        if not collections:
            raise NotFound("当前库里没有任何集合。")
        # 1) 精确 key
        for col in collections:
            if col.get("key") == ref:
                return col
        # 2) 精确名
        for col in collections:
            if (col.get("data") or {}).get("name") == ref:
                return col
        # 3) 大小写不敏感
        low = ref.lower()
        for col in collections:
            if ((col.get("data") or {}).get("name") or "").lower() == low:
                return col
        names = ", ".join(sorted(((c.get("data") or {}).get("name") or "?") for c in collections))
        raise NotFound("未找到集合「%s」。可用集合：%s" % (ref, names))

    def list_tags(self, limit=MAX_PAGE_SIZE, start=0, query=None):
        params = {"limit": limit, "start": start}
        resp = self.request("/tags", params)
        if resp.status != 200:
            raise ApiError(resp.status, resp.body.strip()[:500], resp.url)
        tags = resp.json() or []
        out = []
        for entry in tags:
            if isinstance(entry, dict):
                name = entry.get("tag")
            else:
                name = entry
            if query and query.lower() not in (name or "").lower():
                continue
            out.append(name)
        return out, resp

    def list_tags_all(self, page_size=MAX_PAGE_SIZE):
        """把标签**全部**翻完，返回 ``(names, total, pages)``。

        结构性读取默认就该是全量：标签数超一页时，只取首页会**静默**少给。
        """
        out = []
        cursor = 0
        pages = 0
        total = None
        while True:
            batch, resp = self.list_tags(limit=page_size, start=cursor)
            pages += 1
            if resp.total_results is not None:
                total = resp.total_results
            out.extend(batch)
            cursor += len(batch)
            if not batch or len(batch) < page_size or \
                    (total is not None and cursor >= total):
                break
            if pages >= MAX_PAGES:
                raise ApiError(
                    200, "标签分页未走完（已取 %d 页 / %d 条，服务端报 %s 条）"
                         % (pages, len(out), total),
                    self.url("/tags"))
        return out, total, pages

    def list_searches(self):
        """列保存的检索；**默认取全量**（自动分页）。"""
        out = []
        cursor = 0
        total = None
        while True:
            resp = self.request("/searches",
                                {"limit": MAX_PAGE_SIZE, "start": cursor})
            if resp.status != 200:
                raise ApiError(resp.status, resp.body.strip()[:500], resp.url)
            batch = resp.json() or []
            if resp.total_results is not None:
                total = resp.total_results
            out.extend(batch)
            cursor += len(batch)
            if not batch or len(batch) < MAX_PAGE_SIZE or \
                    (total is not None and cursor >= total):
                break
        return out

    # -- 导出 -------------------------------------------------------------- #

    def export_raw(self, key, fmt):
        """用 Zotero 自带的导出器导出单条（bibtex/biblatex/ris/csljson）。"""
        return self.get_text("/items/%s" % key, {"format": fmt})

    def export_batch_raw(self, keys, fmt):
        """批量导出：一次请求拿列表，再按 key 切分。"""
        text = self.get_text("/items", {"format": fmt, "limit": len(keys) or 1,
                                        "itemKey": ",".join(keys)})
        return text


# --------------------------------------------------------------------------- #
# 批注与评论归属
# --------------------------------------------------------------------------- #

class CommentSplit(object):
    """一条 ``annotationComment`` 的归属切分结果。

    规则（<VAULT>/00_System/Zotero_Access.md）：**按 ``🔤…🔤`` 区间切分**，
    不是按「整条含不含 🔤」。

    - ``machine_texts``：区间内的机器词典文本（``tool_generated``，永不作 paper quote）
    - ``researcher_text``：区间外的非空文字（研究者本人的话）
    - ``unmarked_text``：完全没有 ``🔤`` 标记时的整条评论

    典型形态 ``🔤机器译文🔤\\n研究者手写的话``：
    区间内是机器词典，换行之后是研究者的话——**不得因为整条含 🔤 就把研究者的话丢掉**。
    """

    __slots__ = ("raw", "machine_texts", "researcher_text", "unmarked_text",
                 "has_machine_mark")

    def __init__(self, raw, machine_texts, researcher_text, unmarked_text, has_machine_mark):
        self.raw = raw
        self.machine_texts = machine_texts
        self.researcher_text = researcher_text
        self.unmarked_text = unmarked_text
        self.has_machine_mark = has_machine_mark

    @property
    def researcher_comment(self):
        """研究者本人写的话（可能是空串）。"""
        return self.researcher_text or self.unmarked_text or ""

    @property
    def classification(self):
        """这条评论的归属。

        - ``researcher``：通篇没有 ``🔤`` 标记 —— 是研究者自己敲的话。
          翻译插件只会给**它自己生成的文本**加 ``🔤``，所以没有标记就等于人写的。
        - ``tool_generated``：只有 ``🔤…🔤`` 区间，区间外没有别的字。
        - ``machine_plus_researcher``：既有机器区间，区间外也有研究者的话。
        - ``mixed``：还没切分过（``unmarked_text`` 与标记同时存在）的少见形态。
        """
        if self.unmarked_text:
            # 没有 🔤 标记 → 研究者手写；不能当成机器产物丢掉。
            return "researcher" if not self.has_machine_mark else "mixed"
        if self.has_machine_mark and self.researcher_text:
            return "machine_plus_researcher"
        if self.has_machine_mark:
            return "tool_generated"
        return "researcher"

    def to_dict(self):
        return {
            "raw": self.raw,
            "classification": self.classification,
            "machine_texts": self.machine_texts,
            "researcher_text": self.researcher_text,
            "unmarked_text": self.unmarked_text,
            "researcher_comment": self.researcher_comment,
            "has_machine_mark": self.has_machine_mark,
        }


def split_comment(comment):
    """按 ``🔤…🔤`` 区间切分评论。区间内 = 机器词典，区间外 = 研究者的话。"""
    raw = comment or ""
    machine, outside_parts = [], []
    cursor = 0
    idx = raw.find(MACHINE_MARK)
    while idx != -1:
        outside_parts.append(raw[cursor:idx])
        end = raw.find(MACHINE_MARK, idx + 1)
        if end == -1:
            # 只有一个 🔤：从它到结尾都算机器区间
            machine.append(raw[idx + 1:])
            cursor = len(raw)
            idx = -1
            break
        machine.append(raw[idx + 1:end])
        cursor = end + 1
        idx = raw.find(MACHINE_MARK, cursor)
    outside_parts.append(raw[cursor:])
    outside = "\n".join(part.strip() for part in outside_parts if part.strip())
    machine_clean = [m.strip() for m in machine if m.strip()]
    has_mark = MACHINE_MARK in raw
    unmarked = raw.strip() if not has_mark else ""
    return CommentSplit(raw=raw, machine_texts=machine_clean,
                        researcher_text=outside, unmarked_text=unmarked,
                        has_machine_mark=has_mark)


def normalize_color(value, strict=False):
    """把颜色（名字或 hex）规范化成五色通道名。

    ``strict=True`` 时，无法识别的颜色**直接报参数错退出码 2**——因为静默返回
    「一个谁也匹配不上的名字」会让 ``--color`` 悄悄筛出 0 条，用户还以为这篇没有
    紫色批注。宁可直接报错。
    """
    if not value:
        return None
    low = str(value).strip().lower()
    if low in ANNOTATION_COLORS:
        return low
    hexed = low if low.startswith("#") else "#" + low
    if hexed in COLOR_BY_HEX:
        return COLOR_BY_HEX[hexed]
    if strict:
        raise UsageError(
            "无法识别的颜色 %r。可用名字：%s；也可直接给 hex（如 #ffd400）。"
            % (value, " / ".join(sorted(ANNOTATION_COLORS)))
        )
    return str(value).strip()


class Annotation(object):
    """一条批注的规范化视图。

    字段名与 Zotero API 保持一致，另加 ``color_name``（五色通道名）、
    ``position``（解析后的 annotationPosition）、``attachment_key`` / ``attachment_name``。
    """

    __slots__ = ("key", "version", "item_type", "parent_item", "annotation_type",
                 "text", "comment", "color", "color_name", "page_label", "sort_index",
                 "position", "tags", "date_added", "date_modified",
                 "attachment_key", "attachment_name", "raw")

    def __init__(self, **kw):
        for slot in self.__slots__:
            setattr(self, slot, kw.get(slot))

    @classmethod
    def from_api(cls, item):
        data = item.get("data") or {}
        position = data.get("annotationPosition")
        if isinstance(position, str):
            try:
                position = json.loads(position)
            except ValueError:
                pass
        color = data.get("annotationColor")
        return cls(
            key=item.get("key") or data.get("key"),
            version=item.get("version") or data.get("version"),
            item_type=data.get("itemType"),
            parent_item=data.get("parentItem"),
            annotation_type=data.get("annotationType"),
            text=data.get("annotationText"),
            comment=data.get("annotationComment"),
            color=color,
            color_name=COLOR_BY_HEX.get((color or "").lower()),
            page_label=data.get("annotationPageLabel"),
            sort_index=data.get("annotationSortIndex"),
            position=position,
            tags=[t.get("tag") if isinstance(t, dict) else t for t in (data.get("tags") or [])],
            date_added=data.get("dateAdded"),
            date_modified=data.get("dateModified"),
            attachment_key=None,
            attachment_name=None,
            raw=item,
        )

    #: 五色语义（与 Zotero_Access.md 一致）
    COLOR_MEANING = {
        "yellow": "生词（-> 03_Vocabulary/，不进证据、不进 Wiki）",
        "green": "定义术语或术语解释（-> E 对象 -> concept 页）",
        "blue": "影响、观点、解决方法（-> E 对象 -> 主张登记表，默认 +）",
        "red": "缺陷、现有问题、现有挑战（-> E 对象 -> − 证据 / gap/）",
        "purple": "与我的研究相关（-> §7 研究关系；research_position 判定首要依据）",
    }

    @property
    def page_index(self):
        if isinstance(self.position, dict):
            return self.position.get("pageIndex")
        return None

    @property
    def page(self):
        """首选官方页码标签，其次用 pageIndex+1 兜底。"""
        if self.page_label:
            return self.page_label
        if self.page_index is not None:
            return str(int(self.page_index) + 1)
        return None

    @property
    def comments(self):
        return split_comment(self.comment)

    def to_dict(self, split=False, include_raw=False):
        out = {
            "key": self.key,
            "version": self.version,
            "itemType": self.item_type,
            "parentItem": self.parent_item,
            "attachmentKey": self.attachment_key,
            "attachmentName": self.attachment_name,
            "annotationType": self.annotation_type,
            "annotationText": self.text,
            "annotationComment": self.comment,
            "annotationColor": self.color,
            "colorName": self.color_name,
            "colorMeaning": self.COLOR_MEANING.get(self.color_name),
            "annotationPageLabel": self.page_label,
            "page": self.page,
            "pageIndex": self.page_index,
            "annotationSortIndex": self.sort_index,
            "annotationPosition": self.position,
            "tags": self.tags,
            "dateAdded": self.date_added,
            "dateModified": self.date_modified,
        }
        if split:
            out["commentParts"] = self.comments.to_dict()
        if include_raw:
            out["raw"] = self.raw
        return out


# --------------------------------------------------------------------------- #
# 全文检索（BM25）
# --------------------------------------------------------------------------- #

_TOKEN_RE = re.compile(r"[0-9A-Za-z_]+|[\u4e00-\u9fff]")


def tokenize(text):
    """轻量分词：英文/数字按词，CJK 逐字（无需第三方分词库）。"""
    if not text:
        return []
    return [t.lower() for t in _TOKEN_RE.findall(text)]


def estimate_page(char_offset, meta):
    """由字符偏移**估算**页码（从 1 开始）。

    .. warning::
       这是估算值，**不是** Zotero 的官方分页。Local API 静默忽略 ``?page=N``，
       所以拿不到真实分页边界。凡是把它的结果交给下游，都必须同时带上
       ``page_estimated: true``——绝不能让估算页码长得像
       ``annotationPageLabel``（那才是 Zotero 官方标注）一样权威。
    """
    per_page = meta.get("chars_per_page_estimate") or 0
    if not per_page or char_offset is None:
        return None
    total = meta.get("total_pages") or 0
    page = int(char_offset // per_page) + 1
    if total:
        page = min(page, int(total))
    return max(1, page)


def parse_page_range(spec, total_pages=None):
    """解析 ``"3"`` / ``"3-7"`` 形式的页码范围，返回 ``(start, end)``（含端点）。"""
    text = str(spec).strip()
    match = re.match(r"^(\d+)\s*(?:-\s*(\d+))?$", text)
    if not match:
        raise UsageError("页码范围要写成 3 或 3-7，收到的是 %r" % spec)
    start = int(match.group(1))
    end = int(match.group(2)) if match.group(2) else start
    if start < 1:
        raise UsageError("页码从 1 开始，收到 %s" % start)
    if end < start:
        start, end = end, start
    if total_pages:
        end = min(end, int(total_pages))
    return start, end


def slice_by_page(content, chars_per_page, start, end):
    """在**本地**按字符偏移切出第 ``start..end`` 页。

    因为每页字符数只能取平均值，这只是近似切分——调用方必须标注 ``page_estimated``。
    """
    if not content or not chars_per_page:
        return content or ""
    begin = int((start - 1) * chars_per_page)
    stop = int(end * chars_per_page)
    return content[begin:stop]


PASSAGE_MAX_CHARS = 700        # 单个片段的字符上限
PASSAGE_MIN_CHARS = 60         # 拉丁文本的片段长度门槛
PASSAGE_CJK_MIN_CHARS = 20     # CJK 文本按**字符**算，门槛降到 20
CJK_HEAVY_RATIO = 0.30         # CJK 占比达到这个比例就按 CJK 口径

# 判断脚本用：CJK 汉字（含扩展 A 与兼容区）。计数用。
_CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
# 「有内容」的判据：至少含一个字母 / 数字 / CJK。整段全是排版符号的算垃圾。
_CONTENT_RE = re.compile(r"[0-9A-Za-z\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")


def cjk_ratio(text):
    """CJK 字符数 ÷ 非空白字符数（0.0–1.0）。"""
    if not text:
        return 0.0
    significant = sum(1 for ch in text if not ch.isspace())
    if not significant:
        return 0.0
    return len(_CJK_RE.findall(text)) / float(significant)


def is_cjk_heavy(text, ratio=CJK_HEAVY_RATIO):
    """文本是否以 CJK 为主——是的话长度门槛按**字符数**算，不能用拉丁词数口径。"""
    return cjk_ratio(text) >= ratio


def passage_min_chars(chunk, min_chars=PASSAGE_MIN_CHARS,
                      cjk_min_chars=PASSAGE_CJK_MIN_CHARS):
    """这一段适用的长度门槛。

    中文一个字就是一个词，拿 60 字符的门槛去卡中文等于把正常段落判成碎片，
    所以 CJK 为主的片段门槛降到 20 字符。
    """
    return cjk_min_chars if is_cjk_heavy(chunk) else min_chars


def _raw_segments(text, max_chars):
    """第一层切分：按空行分段，超长段再按句读切，仍超长则硬切。"""
    out = []

    def push(chunk, offset):
        stripped = chunk.strip()
        if not stripped:
            return
        # 把开头被 strip 掉的空白算进去，否则 offset 指向的位置会和 chunk 对不上。
        lead = len(chunk) - len(chunk.lstrip())
        out.append((offset + lead, stripped))

    for match in re.finditer(r"[^\n]*(?:\n(?!\s*\n)[^\n]*)*", text):
        block = match.group(0)
        if not block.strip():
            continue
        base = match.start()
        if len(block) <= max_chars:
            push(block, base)
            continue
        for sentence_match in re.finditer(
                r"[^\u3002\uff01\uff1f.!?;\uff1b]*(?:[\u3002\uff01\uff1f.!?;\uff1b]+|$)",
                block):
            sentence = sentence_match.group(0)
            if not sentence:
                continue
            cursor = base + sentence_match.start()
            while len(sentence) > max_chars:
                push(sentence[:max_chars], cursor)
                cursor += max_chars
                sentence = sentence[max_chars:]
            push(sentence, cursor)
    return out


def _merge_short_segments(text, raw, max_chars, min_chars, cjk_min_chars):
    """把**前后相邻的短片段**并成一段，合并上界是 ``max_chars``。

    这是替代旧实现那条静默丢弃路径的核心：旧代码在切出 >3 段时把所有短于门槛的
    片段整块扔掉、一个字都不报。现在先合并；合并不掉的（例如长片段夹着的小尾巴）
    仍然**保留**，交给调用方如实报告，绝不悄悄消失。

    合并方式是**扩展源区间**而不是拼接字符串——合并后的片段仍是 ``text`` 上
    一段连续的切片，``text[offset:offset+len(chunk)] == chunk`` 这个不变量在
    合并前后都成立，页码估算的偏移因此始终可核对。
    """
    spans = []
    pending = None          # [start, end]
    for offset, chunk in raw:
        end = offset + len(chunk)
        if pending is None:
            pending = [offset, end]
            continue
        current = text[pending[0]:pending[1]]
        short = len(current) < passage_min_chars(current, min_chars, cjk_min_chars)
        if short and (end - pending[0]) <= max_chars and pending[1] <= offset:
            pending[1] = end
        else:
            spans.append((pending[0], pending[1]))
            pending = [offset, end]
    if pending is not None:
        spans.append((pending[0], pending[1]))
    return [(start, text[start:end]) for start, end in spans]


def split_passages_report(text, max_chars=PASSAGE_MAX_CHARS,
                          min_chars=PASSAGE_MIN_CHARS,
                          cjk_min_chars=PASSAGE_CJK_MIN_CHARS):
    """切分全文，返回 ``(passages, stats)``。

    ``passages`` 为 ``[(char_offset, chunk), ...]``；字符偏移用于**估算页码**——
    Zotero 的 ``?page=N`` 被静默忽略，拿不到真实分页，只能按「偏移 ÷ 每页平均
    字符数」估算，并在输出里标注为估算值。

    ``stats`` 里的每一项都是给调用方**如实报告**用的：``rawPassages`` →
    ``mergedPassages`` → ``passages`` 逐级收敛，中间少了多少、为什么少，
    必须能说清楚。**不变量：``text`` 非空时 ``keptChars`` 必须 > 0。**
    """
    stats = {
        "sourceChars": len(text or ""),
        "rawPassages": 0,
        "mergedPassages": 0,
        "passages": 0,
        "keptChars": 0,
        "droppedPassages": 0,
        "droppedChars": 0,
        "fallbackApplied": False,
        "cjkHeavy": False,
        "minCharsUsed": min_chars,
        "cjkMinChars": cjk_min_chars,
    }
    if not text:
        return [], stats

    raw = _raw_segments(text, max_chars)
    stats["rawPassages"] = len(raw)
    stats["cjkHeavy"] = is_cjk_heavy(text)
    stats["minCharsUsed"] = cjk_min_chars if stats["cjkHeavy"] else min_chars

    merged = _merge_short_segments(text, raw, max_chars, min_chars, cjk_min_chars)
    stats["mergedPassages"] = len(merged)

    # 唯一允许丢弃的情况：整段不含任何字母 / 数字 / CJK（纯排版符号）。
    # 丢掉多少必须记账，调用方会把它写进输出。
    kept = []
    dropped_p = 0
    dropped_c = 0
    for offset, chunk in merged:
        if _CONTENT_RE.search(chunk):
            kept.append((offset, chunk))
        else:
            dropped_p += 1
            dropped_c += len(chunk)
    if not kept and merged:
        # 兜底：整篇都挤不出「内容字符」时，宁可回退到不丢弃，
        # 也绝不给出「有内容却 0 片段」这种没法向下游解释的结果。
        kept = merged
        dropped_p = 0
        dropped_c = 0
        stats["fallbackApplied"] = True

    stats["droppedPassages"] = dropped_p
    stats["droppedChars"] = dropped_c
    stats["passages"] = len(kept)
    stats["keptChars"] = sum(len(chunk) for _, chunk in kept)
    return kept, stats


def split_passages_with_offsets(text, max_chars=PASSAGE_MAX_CHARS,
                                min_chars=PASSAGE_MIN_CHARS):
    """把全文切成 ``[(char_offset, chunk), ...]``（见 :func:`split_passages_report`）。"""
    return split_passages_report(text, max_chars, min_chars)[0]


def split_passages(text, max_chars=PASSAGE_MAX_CHARS, min_chars=PASSAGE_MIN_CHARS):
    """把全文切成段落块（只返回文本，见 :func:`split_passages_report`）。"""
    return [chunk for _, chunk in split_passages_with_offsets(text, max_chars, min_chars)]


def bm25_rank(query, passages, k1=1.5, b=0.75):
    """对 passages 按 BM25 排序。

    ``passages`` 可以是 ``[(id, text), ...]`` 或 ``[(id, text, offset), ...]``。
    返回 ``[(id, text, score), ...]``，按分数降序，score 为 0 的不返回。
    内容完全相同的片段（PDF 里重复的页眉/脚注）只保留第一次出现。
    """
    import math

    normalized = []
    for row in passages:
        if len(row) >= 3:
            normalized.append((row[0], row[1]))
        else:
            normalized.append((row[0], row[1]))
    deduped = []
    seen = set()
    for pid, text in normalized:
        fingerprint = hashlib.md5(text.encode("utf-8", "replace")).hexdigest()
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        deduped.append((pid, text))

    docs = [(pid, tokenize(text)) for pid, text in deduped]
    if not docs:
        return []
    n = len(docs)
    avgdl = sum(len(toks) for _, toks in docs) / float(n) or 1.0

    df = {}
    for _, toks in docs:
        for term in set(toks):
            df[term] = df.get(term, 0) + 1

    q_terms = tokenize(query)
    if not q_terms:
        return []
    q_counts = {}
    for term in q_terms:
        q_counts[term] = q_counts.get(term, 0) + 1

    text_by_id = dict(deduped)
    scored = []
    for pid, toks in docs:
        if not toks:
            continue
        length = len(toks)
        tf = {}
        for term in toks:
            tf[term] = tf.get(term, 0) + 1
        score = 0.0
        for term, qtf in q_counts.items():
            freq = tf.get(term)
            if not freq:
                continue
            idf = math.log(1.0 + (n - df.get(term, 0) + 0.5) / (df.get(term, 0) + 0.5))
            denom = freq + k1 * (1.0 - b + b * length / avgdl)
            score += idf * (freq * (k1 + 1.0) / denom) * (1.0 + 0.25 * (qtf - 1))
        if score > 0:
            scored.append((pid, score))
    scored.sort(key=lambda row: (-row[1], str(row[0])))
    return [(pid, text_by_id.get(pid, ""), round(score, 4)) for pid, score in scored]


# --------------------------------------------------------------------------- #
# 附件路径解析
# --------------------------------------------------------------------------- #

def default_storage_dir():
    """Zotero ``storage/`` 目录的常见位置。

    覆盖顺序：``RV_ZOTERO_STORAGE``（直接给 storage 目录）→
    ``RV_ZOTERO_DATA_DIR``（给 Zotero 数据目录，自动接 ``storage``）→
    各平台默认位置里第一个真实存在的。
    """
    env = os.environ.get("RV_ZOTERO_STORAGE")
    if env:
        return env
    data_dir = os.environ.get("RV_ZOTERO_DATA_DIR")
    if data_dir:
        return os.path.join(data_dir, "storage")
    home = os.path.expanduser("~")
    candidates = [
        os.path.join(home, "Zotero", "storage"),
        os.path.join(home, ".zotero", "zotero", "storage"),
        os.path.join(home, "Library", "Application Support", "Zotero", "storage"),
        os.path.join(os.environ.get("LOCALAPPDATA") or "", "Zotero", "Zotero", "storage"),
        os.path.join(os.environ.get("APPDATA") or "", "Zotero", "Zotero", "storage"),
    ]
    for path in candidates:
        if path and os.path.isdir(path):
            return path
    return candidates[0]


def resolve_attachment_path(data, storage_dir=None):
    """把附件条目解析为磁盘路径。

    参数可以是附件条目的 ``data`` 字典，也可以是整个条目对象（含 ``data`` 键）——
    两种都能吃，省得调用方记。

    - ``linkMode`` 为 ``linked_url``：**没有本地文件**，返回 ``(None, "linked_url")``。
    - ``linkMode`` 为 ``linked_file``：用 ``data.path``；``attachments:xxx`` 形式
      相对 data 目录下的 ``attachments/`` 解析。
    - 其余（``imported_file`` 等）：``<storage>/<attachmentKey>/<filename>``。

    返回 ``(path, kind)``；无法解析时 path 为 None。
    """
    if isinstance(data, dict) and "data" in data and isinstance(data["data"], dict):
        data = data["data"]
    data = data or {}
    storage_dir = storage_dir or default_storage_dir()
    link_mode = data.get("linkMode")
    path = data.get("path")
    key = data.get("key")
    filename = data.get("filename") or data.get("title")

    if link_mode == "linked_url":
        # 网页快照/链接附件在磁盘上没有对应文件，不能编一个路径出来。
        return None, "linked_url"

    if link_mode == "linked_file":
        if not path:
            return None, "linked_file"
        if path.startswith("attachments:"):
            base = os.path.join(os.path.dirname(storage_dir.rstrip("\\/")), "attachments")
            return os.path.normpath(os.path.join(base, path[len("attachments:"):])), "linked_file"
        return os.path.normpath(path), "linked_file"

    if filename:
        return os.path.normpath(os.path.join(storage_dir, key or "", filename)), "stored"
    return None, "stored"


# --------------------------------------------------------------------------- #
# citation 近似排版（Local API 不支持 format=citation）
# --------------------------------------------------------------------------- #

def _split_name(name):
    name = (name or "").strip()
    if not name:
        return "", ""
    if "," in name:
        last, _, first = name.partition(",")
        return last.strip(), first.strip()
    parts = name.split()
    if len(parts) == 1:
        return parts[0], ""
    return parts[-1], " ".join(parts[:-1])


def _initials(given):
    out = []
    for chunk in re.split(r"[\s.\-]+", given or ""):
        if chunk:
            out.append(chunk[0].upper() + ".")
    return " ".join(out)


def format_creators(data, style="apa"):
    creators = data.get("creators") or []
    names = []
    for creator in creators:
        if creator.get("creatorType") == "editor" and creator.get("name"):
            last, first = _split_name(creator.get("name"))
        else:
            last = creator.get("lastName") or ""
            first = creator.get("firstName") or ""
            if not last and creator.get("name"):
                last, first = _split_name(creator.get("name"))
        if not last:
            continue
        if style == "ieee":
            # 注意括号：`.strip()` 必须作用在 % 格式化**之后**的字符串上。
            # 写成 `"%s %s" % (a, b).strip()` 会先对元组取 strip → AttributeError。
            names.append(("%s %s" % (_initials(first), last)).strip())
        elif style == "gb-t-7714":
            names.append(("%s %s" % (last.upper(), _initials(first))).strip())
        else:
            names.append("%s, %s" % (last, _initials(first)) if first else last)
    if not names:
        return ""
    if style == "ieee":
        if len(names) > 6:
            return names[0] + " et al."
        if len(names) > 1:
            return ", ".join(names[:-1]) + ", and " + names[-1]
        return names[0]
    if len(names) == 1:
        return names[0]
    if len(names) > 20:
        return ", ".join(names[:19]) + ", ... " + names[-1]
    return ", ".join(names[:-1]) + ", & " + names[-1]


def _period(text):
    """给句子补句点，但**已经以句点结尾的就不再补**。

    专治 ``n.d.`` 这类自带句点的取值：``"%s." % "n.d."`` 会排出 ``"n.d.."``。
    """
    text = (text or "").strip()
    if not text or text.endswith("."):
        return text
    return text + "."


def _year(data):
    """取年份。取不到时返回 ``"n.d."``（**不带括号**——括号由各体例自己加，
    否则 APA 的 ``(%s)`` 会排出 ``((n.d.))``）。"""
    date = data.get("date") or ""
    match = re.search(r"\d{4}", date)
    return match.group(0) if match else "n.d."


def format_citation(obj, style="apa"):
    """把一条 Zotero 条目排成引用字符串。

    这是**近似**排版（Local API 不提供 CSL 引擎），覆盖常见类型：
    journalArticle / conferencePaper / book / bookSection / thesis / report /
    webpage / preprint / manuscript。复杂类型请用 ``--format csljson`` 交给
    外部 CSL 处理器。
    """
    data = obj.get("data") or obj
    item_type = data.get("itemType") or ""
    title = (data.get("title") or "").strip()
    creators = format_creators(data, style)
    year = _year(data)

    container = (data.get("publicationTitle") or data.get("bookTitle")
                 or data.get("proceedingsTitle") or data.get("university")
                 or data.get("institution") or data.get("websiteTitle")
                 or data.get("publisher") or "").strip()
    volume = data.get("volume")
    issue = data.get("issue")
    pages = data.get("pages")
    doi = data.get("DOI")
    url = data.get("url")

    if style == "ieee":
        bits = [creators] if creators else []
        if title:
            bits.append('"%s,"' % title if item_type in ("journalArticle", "conferencePaper") else title)
        if container:
            bits.append("*%s*" % container if item_type in ("book", "report", "thesis") else container)
        if volume:
            tail = "vol. %s" % volume
            if issue:
                tail += ", no. %s" % issue
            if pages:
                tail += ", pp. %s" % pages
            bits.append(tail)
        elif pages:
            bits.append("pp. %s" % pages)
        bits.append(year)
        if doi:
            bits.append("doi: %s" % doi)
        elif url:
            bits.append(url)
        return _period(", ".join(b for b in bits if b))

    # APA / GB-T-7714 近似
    bits = []
    if creators:
        # APA 要求作者串以句点收尾，但姓名缩写本身自带句点
        # （"Lovelace, A."），别再补一个，否则排出 "A.."。
        suffix = "." if (style == "apa" and not creators.endswith(".")) else ""
        bits.append(creators + suffix)
    if style == "apa":
        bits.append("(%s)." % year)
    else:
        bits.append(_period(year))
    if title:
        bits.append(_period(title))
    if container:
        tail = container
        if volume:
            tail += ", %s" % volume
        if issue:
            tail += "(%s)" % issue
        if pages:
            tail += ", %s" % pages
        bits.append(_period(tail))
    if doi:
        bits.append("https://doi.org/%s" % doi)
    elif url:
        bits.append(url)
    return " ".join(b for b in bits if b).strip()


# --------------------------------------------------------------------------- #
# 输出
# --------------------------------------------------------------------------- #

def force_utf8_stdout(stream=None):
    """Windows 下把 stdout/stderr 显式切到 UTF-8，否则中文必然乱码。"""
    stream = stream or sys.stdout
    for target, kwargs in ((sys.stdout, {"errors": "replace"}),
                           (sys.stderr, {"errors": "replace"})):
        reconfigure = getattr(target, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8", **kwargs)
                continue
            except (ValueError, OSError):  # pragma: no cover
                pass
        if hasattr(target, "buffer"):  # pragma: no cover - 老环境兜底
            try:
                wrapper = io.TextIOWrapper(target.buffer, encoding="utf-8",
                                           errors="replace", line_buffering=True)
                if target is sys.stdout:
                    sys.stdout = wrapper
                else:
                    sys.stderr = wrapper
            except (ValueError, OSError):
                pass
    return stream


def emit(payload, as_json=True, human=None, stream=None):
    """输出结果。默认 JSON（ensure_ascii=False），`--human` 时走人类可读表格。"""
    stream = stream or sys.stdout
    if as_json:
        text = json.dumps(payload, ensure_ascii=False, indent=2, default=str)
    else:
        text = human if isinstance(human, str) else json.dumps(payload, ensure_ascii=False,
                                                               indent=2, default=str)
    stream.write(text)
    if not text.endswith("\n"):
        stream.write("\n")
    return text


def display_width(text):
    """粗略显示宽度：CJK 全角算 2 列。"""
    width = 0
    for char in text:
        width += 2 if unicodedata.east_asian_width(char) in ("W", "F") else 1
    return width


def pad(text, width):
    text = text or ""
    return text + " " * max(0, width - display_width(text))


def table(rows, headers):
    """等宽表格（CJK 对齐）。"""
    if not rows:
        return "(空)"
    widths = [display_width(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], display_width(str(cell)))
    lines = ["  ".join(pad(h, widths[i]) for i, h in enumerate(headers))]
    lines.append("  ".join("-" * widths[i] for i in range(len(headers))))
    for row in rows:
        lines.append("  ".join(pad(str(c), widths[i]) for i, c in enumerate(row)))
    return "\n".join(lines)


def truncate(text, limit=60):
    text = (text or "").replace("\n", " ").strip()
    return text if len(text) <= limit else text[:limit - 1] + "…"


def item_row(item):
    data = item.get("data") or {}
    creators = data.get("creators") or []
    first = ""
    if creators:
        person = creators[0]
        first = person.get("lastName") or person.get("name") or ""
    return [item.get("key", ""), data.get("itemType", ""), truncate(data.get("title", ""), 52),
            _year(data), truncate(first, 14)]


ITEM_HEADERS = ["KEY", "TYPE", "TITLE", "YEAR", "FIRST AUTHOR"]


# --------------------------------------------------------------------------- #
# 子命令实现
# --------------------------------------------------------------------------- #

def cmd_ping(client, args):
    info = client.ping()
    if args.json:
        emit(info, True)
    else:
        lines = [
            "Zotero 可达 ✓",
            "  API 基址      : %s" % info["api_base"],
            "  library       : %s" % info["library"],
            "  库 id         : %s" % info["library_id"],
            "  库名          : %s" % info["library_name"],
            "  Zotero 版本   : %s" % info["zotero_version"],
            "  API 版本      : %s（schema %s）" % (info["api_version"], info["schema_version"]),
            "  库版本        : %s（changes --since 用这个做基线）" % info["last_modified_version"],
            "  顶层条目数    : %s" % info["total_items"],
        ]
        emit(info, False, "\n".join(lines))
    return EXIT_OK


def cmd_search(client, args):
    limit = args.limit
    if args.collection:
        col = client.resolve_collection(args.collection)
        items, resp = client.list_collection_items(
            col["key"], query=args.query, limit=limit, start=args.offset,
            sort=args.sort, direction=args.direction, top=args.top)
        scope = {"collection": col["key"],
                 "collectionName": (col.get("data") or {}).get("name")}
    else:
        items, resp = client.list_items(
            query=args.query, qmode=args.qmode, item_type=args.item_type,
            tag=args.tag, sort=args.sort, direction=args.direction,
            limit=limit, start=args.offset, top=args.top)
        scope = {"library": client.library}
    payload = {
        "query": args.query,
        "qmode": args.qmode,
        "itemType": args.item_type,
        "tag": args.tag,
        "total": resp.total_results,
        "limit": limit,
        "offset": args.offset,
        "count": len(items),
        "scope": scope,
        "items": items,
    }
    if args.json:
        emit(payload, True)
    else:
        head = "命中 %s 条（本次返回 %s 条，offset=%s）" % (
            resp.total_results, len(items), args.offset)
        emit(payload, False, head + "\n\n" + table([item_row(i) for i in items], ITEM_HEADERS))
    return EXIT_OK


def cmd_get(client, args):
    key = args.key
    include = parse_include(args.include)
    # 允许用 key 直接取；也允许 `--key <key>` 省略
    if not key:
        raise UsageError("get 需要 --key <ITEMKEY>（用 search / collections 查 key）")
    obj = client.get_item(key)
    data = obj.get("data") or {}
    payload = {
        "key": obj.get("key"),
        "version": obj.get("version"),
        "library": obj.get("library"),
        "meta": obj.get("meta"),
        "links": obj.get("links"),
        "data": data,
    }
    if args.fields == "all":
        payload["data"] = dict(data)
        payload["extraFields"] = {k: v for k, v in data.items()
                                  if k not in STANDARD_FIELDS}
    if include:
        if "notes" in include:
            payload["notes"] = client.list_notes(key)
        if "attachments" in include:
            payload["attachments"] = client.list_attachments(key)
        if "annotations" in include:
            anns, meta = client.annotations_for_item(key, color=args.color,
                                                     attachment=args.attachment)
            payload["annotations"] = [a.to_dict(split=args.split_comment) for a in anns]
            payload["annotationMeta"] = meta
    if args.json:
        emit(payload, True)
    else:
        lines = [
            "[%s] %s" % (data.get("itemType"), data.get("title")),
            "  key      : %s" % obj.get("key"),
            "  version  : %s" % obj.get("version"),
            "  作者     : %s" % format_creators(data, "apa"),
            "  年份     : %s" % _year(data),
            "  出版物   : %s" % (data.get("publicationTitle") or data.get("bookTitle") or "-"),
            "  DOI      : %s" % (data.get("DOI") or "-"),
            "  引用     : %s" % format_citation(obj, "apa"),
        ]
        for field in ("notes", "attachments"):
            if field in payload:
                lines.append("  %-8s : %s 条" % (field, len(payload[field] or [])))
        if "annotations" in payload:
            meta = payload.get("annotationMeta") or {}
            lines.append("  批注     : %s 条" % len(payload["annotations"]))
            for row in meta.get("attachments") or []:
                lines.append("      └ %s  %s 条" % (truncate(row["name"], 40), row["count"]))
        emit(payload, False, "\n".join(lines))
    return EXIT_OK


STANDARD_FIELDS = {
    "abstractNote", "accessDate", "archive", "archiveLocation", "callNumber",
    "citationKey", "collections", "creators", "date", "dateAdded", "dateModified",
    "DOI", "extra", "itemType", "key", "language", "libraryCatalog", "pages",
    "publicationTitle", "relations", "rights", "shortTitle", "tags", "title",
    "url", "version", "volume", "issue", "series", "seriesTitle", "edition",
    "place", "publisher", "bookTitle", "proceedingsTitle", "conferenceName",
    "institution", "university", "websiteTitle", "genre", "medium", "note",
    "numPages", "number", "ISSN", "ISBN", "PMID", "PMCID",
}


def parse_include(value):
    if not value:
        return set()
    allowed = {"notes", "attachments", "annotations"}
    parts = {p.strip().lower() for p in str(value).split(",") if p.strip()}
    bad = parts - allowed
    if bad:
        message = ("--include 只接受 %s，收到：%s"
                   % ("/".join(sorted(allowed)), ",".join(sorted(bad))))
        # 最常见的错法就是写成单数（--item-type 用单数，--include 用复数），
        # 直接把改法说出来，别让人对着报错猜。
        singular_fix = sorted(p + "s" for p in bad if p + "s" in allowed)
        if singular_fix:
            message += "；是否想写 %s？" % ",".join(singular_fix)
        raise UsageError(message)
    return parts


def cmd_children(client, args):
    """列子对象。

    ⚠ 默认就会带上 ``itemType=annotation``——因为不带时 Zotero 静默返回 0 条批注。
    """
    key = args.key
    if not key:
        raise UsageError("children 需要 --key <ITEMKEY>")
    include = parse_include(args.include) if args.include else set()
    explicit = args.item_type
    payload = {"key": key, "total": None, "children": {}}
    if explicit:
        targets = [explicit]
    else:
        targets = []
        if not include or "attachments" in include:
            targets.append("attachment")
        if not include or "notes" in include:
            targets.append("note")
        if not include or "annotations" in include:
            targets.append("annotation")
    grand_total = 0
    capped = []
    for target in targets:
        if args.limit is None:
            # 默认全量：结构性读取不该有隐式上限。
            items, total, pages = client.list_children_all(key, item_type=target)
        else:
            items, resp = client.list_children(key, item_type=target,
                                               limit=args.limit, start=args.offset)
            total = resp.total_results
            pages = 1
        if target == "annotation":
            normalized = [Annotation.from_api(i).to_dict(split=args.split_comment)
                          for i in items]
        else:
            normalized = items
        payload["children"][target] = {
            "total": total,
            "count": len(items),
            "pages": pages,
            "items": normalized,
        }
        grand_total += total or 0
        if args.limit is not None and (total or 0) > len(items):
            capped.append("%s（取了 %s / 共 %s）" % (target, len(items), total))
    payload["total"] = grand_total
    payload["note"] = ("children 不带 itemType 时 Zotero 会静默漏掉批注；"
                       "本命令默认显式查询 attachment/note/annotation 三类，"
                       "且默认翻完全部分页（每类都带 pages 字段）。")
    if capped:
        warning = ("以下类别按 --limit=%s 只取了前若干条，实际更多：%s。"
                   "去掉 --limit 即取全部。" % (args.limit, "；".join(capped)))
        if any(c.startswith("annotation") for c in capped):
            warning += ("批注建议改用 annotations 子命令：它是批注的正规入口，"
                        "按 key 去重、可叠加颜色过滤，并带 matchedTotal/scanned 如实读数。")
        payload["warning"] = warning
    if args.json:
        emit(payload, True)
    else:
        lines = ["条目 %s 的子对象：" % key]
        if payload.get("warning"):
            lines.append("  ⚠ " + payload["warning"])
        for target in targets:
            block = payload["children"][target]
            lines.append("  %-11s total=%s 本次=%s" % (target, block["total"], block["count"]))
            if target == "annotation":
                for ann in block["items"]:
                    lines.append("      [%s] %s p.%s  %s" % (
                        ann.get("colorName") or "-", ann.get("annotationType"),
                        ann.get("page"), truncate(ann.get("annotationText"), 46)))
            else:
                for child in block["items"]:
                    cdata = child.get("data") or {}
                    lines.append("      [%s] %s  %s" % (
                        cdata.get("itemType"), child.get("key"),
                        truncate(cdata.get("title") or cdata.get("filename"), 46)))
        emit(payload, False, "\n".join(lines))
    return EXIT_OK


def cmd_annotations(client, args):
    key = args.key
    if not key:
        raise UsageError("annotations 需要 --key <ITEMKEY|ATTACHMENTKEY>")
    color = normalize_color(args.color, strict=True)
    anns, meta = client.annotations_for_item(
        key, color=args.color, attachment=args.attachment,
        all_attachments=not args.first_attachment, page_size=args.page_size)
    # 全部命中数（用于如实报告），再按 --limit 截断输出。
    # **默认不截断**：批注就是证据层本身，默认路径上不该有隐式上限。
    matched_total = len(anns)
    truncated = False
    limit = args.limit
    if args.all:
        limit = None
    if limit is not None and matched_total > limit:
        anns = anns[:limit]
        truncated = True
    counts = {}
    for ann in anns:
        name = ann.color_name or "unknown"
        counts[name] = counts.get(name, 0) + 1
    payload = {
        "key": key,
        "colorFilter": color,
        "total": len(anns),
        "matchedTotal": matched_total,
        "scanned": meta.get("scanned"),
        "deduped": meta.get("deduped"),
        "truncated": truncated,
        "countsByColor": counts,
        "attachments": meta.get("attachments"),
        "annotations": [a.to_dict(split=args.split_comment) for a in anns],
        "colorLegend": Annotation.COLOR_MEANING,
    }
    if truncated:
        payload["note"] = ("本条目共命中 %s 条，按 --limit=%s 只输出前 %s 条；"
                           "去掉 --limit 即输出全部。" % (matched_total, args.limit, len(anns)))
    if meta.get("deduped"):
        payload["dedupeNote"] = (
            "父条目递归查询与逐附件查询命中同一批批注，已按 key 去重 %s 条；"
            "`attachments` 各行是**去重前**的分项读数，相加会大于总数。"
            % meta["deduped"])
    if args.json:
        emit(payload, True)
    else:
        lines = ["条目 %s 的批注：命中 %s 条 / 扫描 %s 条（按颜色：%s）" % (
            key, matched_total, meta.get("scanned"),
            ", ".join("%s=%s" % (k, v) for k, v in sorted(counts.items())) or "无")]
        if truncated:
            lines.append("  ⚠ 按 --limit=%s 只输出前 %s 条（去掉 --limit 取全量）"
                         % (args.limit, len(anns)))
        for row in meta.get("attachments") or []:
            lines.append("  附件 %s : 命中 %s / 扫描 %s（总 %s）%s" % (
                truncate(row["name"], 44), row["count"], row.get("scanned"), row.get("total"),
                "  ← 递归查询，已去重" if row.get("duplicateOfAttachments") else ""))
        if meta.get("deduped"):
            lines.append("  ⓘ 上面分项是去重前读数，相加会大于总数 %s（已去重 %s 条）"
                         % (matched_total, meta["deduped"]))
        lines.append("")
        rows = []
        for ann in anns:
            parts = ann.comments
            rows.append([ann.color_name or "-", ann.page or "-",
                         ann.annotation_type or "-",
                         truncate(ann.text, 34),
                         truncate(parts.researcher_comment, 30)])
        lines.append(table(rows, ["COLOR", "PAGE", "TYPE", "QUOTE", "RESEARCHER COMMENT"]))
        emit(payload, False, "\n".join(lines))
    return EXIT_OK


def cmd_retrieve(client, args):
    key = args.key
    if not key:
        raise UsageError("retrieve 需要 --key <ITEMKEY|ATTACHMENTKEY>")
    if not args.query:
        raise UsageError("retrieve 需要 --query <检索词>")
    # 只取一次全文：Local API 的 ?page=N 被忽略，逐页请求等于把同一篇全文下载 N 遍。
    passages, meta = client.fulltext_index(key)
    passage_offsets = {}
    trimmed = []
    for pid, text, offset in passages:
        if len(text) > args.passage_chars:
            text = text[:args.passage_chars]
        passage_offsets[pid] = offset
        trimmed.append((pid, text))
    ranked = bm25_rank(args.query, trimmed)
    limit = args.passages
    top = ranked[:limit]
    results = []
    for pid, text, score in top:
        offset = passage_offsets.get(pid, 0)
        page = estimate_page(offset, meta)
        snippet = text if len(text) <= args.max_chars else text[:args.max_chars] + "…"
        results.append({
            "id": pid,
            "page": page,
            "pageIndex": (page - 1) if page else None,
            # 估算页码必须显式自曝身份，绝不与 Zotero 官方 annotationPageLabel 混淆。
            "pageEstimated": True,
            "pageSource": "char_offset_estimate",
            "charOffset": offset,
            "score": score,
            "passage": text,
            "snippet": snippet,
            "chars": len(text),
        })
    payload = {
        "key": key,
        "attachmentKey": meta.get("attachment_key"),
        "query": args.query,
        "totalPages": meta.get("total_pages"),
        "indexedPages": meta.get("indexed_pages"),
        "chars": meta.get("chars"),
        "passageCount": meta.get("passage_count"),
        "rawPassageCount": meta.get("raw_passage_count"),
        "mergedPassageCount": meta.get("merged_passage_count"),
        "keptChars": meta.get("kept_chars"),
        "droppedPassages": meta.get("dropped_passages"),
        "droppedChars": meta.get("dropped_chars"),
        "fallbackApplied": meta.get("fallback_applied"),
        "minCharsUsed": meta.get("min_chars_used"),
        "cjkMinChars": meta.get("cjk_min_chars"),
        "cjkHeavy": meta.get("cjk_heavy"),
        "matched": len(ranked),
        "returned": len(results),
        "truncated": len(ranked) > len(results),
        "results": results,
        "note": ("页码由「字符偏移 ÷ 每页平均字符数」**估算**得到，不是 PDF 的真实分页——"
                 "Local API 的 ?page=N 参数被静默忽略，拿不到逐页文本。"
                 "需要精确页码请改用 `annotations`（批注带 Zotero 官方页码标签）。"),
        "passageNote": ("片段门槛：拉丁文本 %s 字符、CJK 为主的片段 %s 字符"
                        "（本篇%s）；短片段先向后合并再判定，只有整段不含字母/数字/CJK "
                        "的排版残留才会被丢弃——丢了多少见 droppedPassages。"
                        % (meta.get("min_chars_used"), meta.get("cjk_min_chars"),
                           "CJK 为主" if meta.get("cjk_heavy") else "非 CJK 为主")),
    }
    # 「少给了」必须显式说出来：0 片段有两种完全不同的成因，绝不能含混过去。
    full_chars = meta.get("chars") or 0
    passage_count = meta.get("passage_count") or 0
    dropped_p = meta.get("dropped_passages") or 0
    dropped_c = meta.get("dropped_chars") or 0
    warnings = []
    if not full_chars:
        warnings.append(
            "Zotero 返回的全文是**空**的（0 字符）——该附件可能尚未被索引。"
            "这是「没有可检索内容」，不是检索词的问题。")
    elif not passage_count:
        warnings.append(
            "该附件全文 %s 字符，但切分/过滤后得到 0 个片段"
            "（丢弃 %s 段 / %s 字符）——这是**切分后为空**，"
            "不等于全文里没有内容。" % (full_chars, dropped_p, dropped_c))
    if dropped_p:
        warnings.append(
            "为保证片段可读性丢弃了 %s 段（共 %s 字符）：这些片段整段不含字母/数字/CJK，"
            "多为表格线与排版残留。" % (dropped_p, dropped_c))
    if meta.get("fallback_applied"):
        warnings.append(
            "本篇几乎全是排版符号，已回退为「不丢弃任何片段」——"
            "宁可给出噪声段落，也不给出「有内容却 0 片段」这种没法解释的结果。")
    if warnings:
        payload["warning"] = " ".join(warnings)
    if passage_count and not ranked:
        payload["matchNote"] = (
            "已检索 %s 个片段（共 %s 字符），全文里**确实没有**匹配「%s」的内容——"
            "这是「确实没有」，不是「没检索到」。"
            % (passage_count, meta.get("kept_chars"), args.query))
    if args.json:
        emit(payload, True)
    else:
        lines = ["条目 %s 中检索「%s」：命中 %s / %s 个片段，返回 %s 条"
                 % (key, args.query, len(ranked), meta.get("passage_count"), len(results))]
        lines.append("  ⓘ 页码为**估算值**（全文 %s 字符 / %s 页，抽样 %s 字符每页）；"
                     "精确页码请看批注标签。"
                     % (meta.get("chars"), meta.get("total_pages"),
                        meta.get("chars_per_page_estimate")))
        if payload.get("warning"):
            lines.append("  ⚠ " + payload["warning"])
        if payload.get("matchNote"):
            lines.append("  ⓘ " + payload["matchNote"])
        for row in results:
            lines.append("")
            lines.append("  ── p.≈%s  score=%s  @%s  [%s]"
                         % (row["page"], row["score"], row["charOffset"], row["id"]))
            lines.append("     " + truncate(row["passage"], args.max_chars))
        emit(payload, False, "\n".join(lines))
    return EXIT_OK


def cmd_attachment(client, args):
    key = args.key
    if not key:
        raise UsageError("attachment 需要 --key <ITEMKEY|ATTACHMENTKEY>")
    obj = client.get_item(key)
    data = obj.get("data") or {}
    if data.get("itemType") != "attachment":
        attachments = client.list_attachments(key)
        if not attachments:
            raise NotFound("条目 %s 下没有附件。" % key)
        if args.all:
            resolved = []
            for att in attachments:
                resolved.append(_attachment_info(att, args))
            payload = {"key": key, "itemType": data.get("itemType"),
                       "attachmentCount": len(resolved), "attachments": resolved}
            return _emit_attachments(payload, args)
        obj = attachments[0]
        data = obj.get("data") or {}
    payload = _attachment_info(obj, args)
    return _emit_attachments(payload, args)


def _attachment_info(obj, args):
    data = obj.get("data") or {}
    path, kind = resolve_attachment_path(data, args.storage)
    exists = os.path.isfile(path) if path else False
    return {
        "key": obj.get("key"),
        "parentItem": data.get("parentItem"),
        "itemType": data.get("itemType"),
        "title": data.get("title"),
        "filename": data.get("filename"),
        "contentType": data.get("contentType"),
        "linkMode": data.get("linkMode"),
        "path": path,
        "pathKind": kind,
        "exists": exists,
        "storageDir": args.storage or default_storage_dir(),
        "note": ("exists=false 说明路径解析出来了但本机没有这个文件——常见原因："
                 "storage 目录不在默认位置（用 --storage 指定）、Zotero 用了自定义数据目录"
                 "（设置 → 高级 → 文件和文件夹）、或该附件是 linked_file 且原文件已被移动。"),
    }


def _emit_attachments(payload, args):
    if args.json:
        emit(payload, True)
    else:
        blocks = payload.get("attachments") or [payload]
        lines = []
        for block in blocks:
            lines.append("附件 %s  %s" % (block.get("key"), block.get("filename") or ""))
            lines.append("  路径模式 : %s" % block.get("linkMode"))
            lines.append("  类型     : %s" % block.get("contentType"))
            lines.append("  磁盘路径 : %s" % block.get("path"))
            lines.append("  存在     : %s" % ("是" if block.get("exists") else "否"))
            lines.append("")
        emit(payload, False, "\n".join(lines))
    return EXIT_OK


def cmd_fulltext(client, args):
    key = args.key
    if not key:
        raise UsageError("fulltext 需要 --key <ITEMKEY|ATTACHMENTKEY>")
    data = client.fulltext(key)
    content = data.get("content") or ""
    total_pages = data.get("totalPages") or 1
    per_page = (len(content) / float(total_pages)) if total_pages else 0.0

    payload = {
        "key": key,
        "attachmentKey": data.get("attachment_key"),
        "totalPages": total_pages,
        "indexedPages": data.get("indexedPages"),
        "chars": len(content),
        "charsPerPageEstimate": round(per_page, 1),
        # 名字要说清楚「取回的是整篇」而不是「输出的是整篇」——切片时它依然是
        # True（Zotero 只肯给整篇），但 content 已经不是整篇了。
        "fetchedWholeDocument": True,
        "contentIsWholeDocument": True,
        "content": content,
    }

    if args.pages:
        start, end = parse_page_range(args.pages, total_pages)
        sliced = slice_by_page(content, per_page, start, end)
        payload["requestedPages"] = "%s-%s" % (start, end)
        payload["content"] = sliced
        payload["chars"] = len(sliced)
        payload["contentIsWholeDocument"] = False
        # 关键：切片页码是**本地估算**，必须与 Zotero 官方页码标签区分开。
        payload["pageEstimated"] = True
        payload["pageSource"] = "local_char_offset_slice"
        payload["note"] = (
            "第 %s-%s 页是在**本地**按「字符偏移 ÷ 每页平均字符数(%.1f)」切出来的，"
            "页码为**估算值**，不是 Zotero 的官方分页。"
            "Zotero Local API 会静默忽略 ?page=N，无法按页取。"
            "需要**权威页码**请用 `annotations` 子命令——批注的 annotationPageLabel "
            "才是 Zotero 官方标注。整篇仍被完整取回一次（%s 字符）。"
            % (start, end, per_page, len(content))
        )
    else:
        payload["pageEstimated"] = False
        payload["pageSource"] = "zotero_fulltext_index"
        payload["note"] = "已返回整篇全文（Zotero 全文索引原文，未做任何切分）。"

    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(payload["content"])
        payload["out"] = os.path.abspath(args.out)

    if args.json:
        emit(payload, True)
    else:
        lines = ["附件 %s：indexedPages=%s totalPages=%s chars=%s"
                 % (payload.get("attachmentKey"), payload.get("indexedPages"),
                    payload.get("totalPages"), payload.get("chars"))]
        if args.pages:
            lines.append("  ⓘ 第 %s 页为**本地估算切分**（page_estimated=true），"
                         "非 Zotero 官方页码" % payload["requestedPages"])
        if args.out:
            lines.append("  已写入 %s" % payload["out"])
        else:
            lines.append("")
            lines.append(truncate(payload["content"], 1200))
        emit(payload, False, "\n".join(lines))
    return EXIT_OK


def cmd_export(client, args):
    keys = list(args.key or [])
    fmt = (args.format or "bibtex").lower()
    if not keys:
        raise UsageError("export 需要至少一个 --key <ITEMKEY>（可重复）")
    objects = [client.get_item(k) for k in keys]

    if fmt == "citation":
        style = (args.style or "apa").lower()
        citations = [{"key": k, "citation": format_citation(o, style),
                      "html": "<div class=\"csl-entry\">%s</div>" % format_citation(o, style)}
                     for k, o in zip(keys, objects)]
        payload = {"format": "citation", "style": style, "count": len(citations),
                   "citations": citations,
                   "note": ("Local API 不支持 format=citation（会返回 400），"
                            "这里是本地近似排版；要求严格 CSL 请用 --format csljson "
                            "交给外部 CSL 处理器。")}
        if args.json:
            emit(payload, True)
        else:
            emit(payload, False, "\n\n".join(c["citation"] for c in citations))
        return EXIT_OK

    if fmt not in ("bibtex", "biblatex", "ris", "csljson"):
        raise UsageError("--format 只接受 bibtex/biblatex/ris/csljson/citation，收到 %s" % fmt)

    blocks = []
    for obj in objects:
        try:
            text = client.export_raw(obj["key"], fmt)
        except ApiError as exc:
            if exc.status == 400:
                raise UsageError(
                    "Zotero 拒绝了 format=%s（HTTP 400）。老版本 Zotero 的本地 API 不支持"
                    "该导出格式，可改用 bibtex 或 csljson。" % fmt)
            raise
        blocks.append({"key": obj["key"],
                       "title": (obj.get("data") or {}).get("title"),
                       "text": text})
    payload = {"format": fmt, "count": len(blocks), "items": blocks}
    if len(blocks) == 1:
        payload["text"] = blocks[0]["text"]
    if args.out:
        joined = "\n\n".join(b["text"].strip() for b in blocks)
        with open(args.out, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(joined + "\n")
        payload["out"] = os.path.abspath(args.out)
    if args.json:
        emit(payload, True)
    else:
        emit(payload, False, "\n\n".join(b["text"].strip() for b in blocks))
    return EXIT_OK


def cmd_collections(client, args):
    collections = client.list_collections()
    by_key = {}
    for col in collections:
        by_key[col.get("key")] = col
    rows = []
    for col in collections:
        data = col.get("data") or {}
        name = data.get("name") or ""
        depth = 0
        parent = data.get("parentCollection")
        seen = set()
        while parent and parent in by_key and parent not in seen:
            seen.add(parent)
            depth += 1
            parent = (by_key[parent].get("data") or {}).get("parentCollection")
        rows.append({
            "key": col.get("key"),
            "name": name,
            "indent": depth,
            "display": "  " * depth + ("└ " if depth else "") + name,
            "parentCollection": data.get("parentCollection"),
            "numItems": (col.get("meta") or {}).get("numItems"),
            "version": col.get("version"),
        })
    rows.sort(key=lambda r: (r["display"].strip().lower()))
    payload = {"total": len(rows), "collections": rows,
               "note": "--collection 既可以传 key，也可以传集合名（名字唯一时）。"}
    if args.json:
        emit(payload, True)
    else:
        emit(payload, False, table(
            [[r["display"], r["key"], r["numItems"] if r["numItems"] is not None else "-"]
             for r in rows], ["COLLECTION", "KEY", "ITEMS"]))
    return EXIT_OK


def cmd_tags(client, args):
    all_tags, total, pages = client.list_tags_all()
    # 过滤在**整套分页之上**进行，最后才截断输出 —— 否则 `-q` 只会在首页里找。
    matched = [t for t in all_tags
               if not args.query or args.query.lower() in (t or "").lower()]
    matched_total = len(matched)
    offset = args.offset or 0
    selected = matched[offset:]
    truncated = False
    if args.limit is not None and len(selected) > args.limit:
        selected = selected[:args.limit]
        truncated = True
    payload = {"total": total, "scanned": len(all_tags), "pages": pages,
               "matchedTotal": matched_total, "count": len(selected),
               "limit": args.limit, "offset": offset, "truncated": truncated,
               "query": args.query, "tags": selected}
    if truncated:
        payload["note"] = ("共命中 %s 个标签，按 --limit=%s 只输出 %s 个；"
                           "去掉 --limit 即输出全部。"
                           % (matched_total, args.limit, len(selected)))
    if args.json:
        emit(payload, True)
    else:
        lines = ["标签：库内 %s 个 / 命中 %s 个 / 本次输出 %s 个%s" % (
            total, matched_total, len(selected), "（已截断）" if truncated else "")]
        if truncated:
            lines.append("  ⚠ " + payload["note"])
        lines.extend(selected or ["(无标签)"])
        emit(payload, False, "\n".join(lines))
    return EXIT_OK


def cmd_searches(client, args):
    searches = client.list_searches()
    payload = {"total": len(searches), "searches": searches}
    if args.json:
        emit(payload, True)
    else:
        rows = []
        for entry in searches:
            data = entry.get("data") or {}
            conds = data.get("conditions") or []
            rows.append([entry.get("key"), truncate(data.get("name"), 30),
                         "; ".join("%s %s %s" % (c.get("condition"), c.get("operator"),
                                                 c.get("value")) for c in conds)])
        emit(payload, False, table(rows, ["KEY", "NAME", "CONDITIONS"]))
    return EXIT_OK


def cmd_changes(client, args):
    """库增量。

    本地 API **没有** ``/changes`` 端点（也没有 deleted 列表），所以这里的做法是：
    用响应头 ``Last-Modified-Version`` 做基线，把每个条目的 ``version`` 与基线比较，
    给出「新增 / 修改」；删除只能靠与上一次快照（``--db``）对比推断。
    **这是快照差分，不是服务端 delta**——不要期望它像云端 API 那样完整。
    """
    items = []
    start = 0
    while True:
        resp = client.request("/items", {"limit": MAX_PAGE_SIZE, "start": start})
        if resp.status != 200:
            raise ApiError(resp.status, resp.body.strip()[:500], resp.url)
        batch = resp.json() or []
        total = resp.total_results
        base_version = resp.last_modified_version
        items.extend(batch)
        start += len(batch)
        if not batch or len(batch) < MAX_PAGE_SIZE or (total is not None and start >= total):
            break
    snapshot = {}
    for item in items:
        snapshot[item.get("key")] = {
            "version": item.get("version"),
            "itemType": (item.get("data") or {}).get("itemType"),
            "title": (item.get("data") or {}).get("title"),
            "parentItem": (item.get("data") or {}).get("parentItem"),
            "dateModified": (item.get("data") or {}).get("dateModified"),
        }
    db_path = args.db
    previous = None
    if db_path and os.path.isfile(db_path):
        try:
            with open(db_path, "r", encoding="utf-8") as handle:
                previous = json.load(handle)
        except ValueError:
            previous = None

    if previous is None:
        payload = {
            "mode": "baseline",
            "libraryVersion": base_version,
            "itemCount": len(items),
            "message": ("首次运行：只给出基线。把 libraryVersion 记下来，"
                        "下次用 `changes --since <version>` 查增量；"
                        "加 --db <文件> 可保存快照、让下次能报出删除。"),
        }
        if db_path:
            with open(db_path, "w", encoding="utf-8", newline="\n") as handle:
                json.dump({"libraryVersion": base_version, "items": snapshot}, handle,
                          ensure_ascii=False)
            payload["db"] = os.path.abspath(db_path)
        if args.json:
            emit(payload, True)
        else:
            emit(payload, False, "%s\n库版本=%s，条目数=%s"
                 % (payload["message"], base_version, len(items)))
        return EXIT_OK

    since = args.since
    if since is None:
        since = previous.get("libraryVersion")
    changed, new = [], []
    old_items = previous.get("items") or {}
    for key, info in snapshot.items():
        old = old_items.get(key)
        if old is None:
            new.append({"key": key, **info})
        elif old.get("version") != info.get("version"):
            changed.append({"key": key, "from": old.get("version"),
                            "to": info.get("version"), **info})
    deleted = [{"key": key, "title": (old_items[key] or {}).get("title")}
               for key in old_items if key not in snapshot]
    payload = {
        "mode": "diff",
        "since": since,
        "libraryVersion": base_version,
        "previousVersion": previous.get("libraryVersion"),
        "newCount": len(new), "changedCount": len(changed), "deletedCount": len(deleted),
        "new": new, "changed": changed, "deleted": deleted,
        "note": ("本地 API 无 /changes 端点：这是客户端快照差分（round-trip）。"
                 "库版本号来自响应头 Last-Modified-Version。"),
    }
    if db_path:
        with open(db_path, "w", encoding="utf-8", newline="\n") as handle:
            json.dump({"libraryVersion": base_version, "items": snapshot}, handle,
                      ensure_ascii=False)
        payload["db"] = os.path.abspath(db_path)
    if args.json:
        emit(payload, True)
    else:
        lines = ["自 %s 以来（当前库版本 %s）：新增 %s / 修改 %s / 删除 %s"
                 % (since, base_version, len(new), len(changed), len(deleted))]
        for row in new:
            lines.append("  + %s  %s" % (row["key"], truncate(row.get("title"), 50)))
        for row in changed:
            lines.append("  ~ %s  v%s→v%s  %s" % (row["key"], row["from"], row["to"],
                                                  truncate(row.get("title"), 50)))
        for row in deleted:
            lines.append("  - %s  %s" % (row["key"], truncate(row.get("title"), 50)))
        emit(payload, False, "\n".join(lines))
    return EXIT_OK


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def build_parser():
    parser = argparse.ArgumentParser(
        prog="rvzotero",
        description="可移植、只读的 Zotero 访问层（纯标准库）。默认输出 JSON。",
        epilog="退出码：0 成功 / 2 参数错 / 3 连不上 Zotero / 4 Zotero 报错 / 5 未找到",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version="rvzotero %s" % __version__)
    parser.add_argument("--api", dest="api_base", default=None,
                        help="Local API 基址（默认 $RV_ZOTERO_API 或 http://127.0.0.1:23119/api）")
    parser.add_argument("--library", dest="library", default=None,
                        help="库（默认 $RV_ZOTERO_LIBRARY 或 users/0）")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="HTTP 超时秒数")
    parser.add_argument("--human", action="store_true",
                        help="人类可读输出（默认 JSON）")
    parser.add_argument("--json", action="store_true",
                        help="强制 JSON 输出（默认行为，便于显式书写）")

    sub = parser.add_subparsers(dest="command")

    def add(name, help_text):
        sp = sub.add_parser(name, help=help_text)
        # default=SUPPRESS 是关键：argparse 会把子命令解析出的 namespace
        # **整体覆盖**回父 namespace，若这里给 False 默认值，写在子命令
        # **前面**的 `--human` 会被悄悄抹掉（`rvzotero --human ping`
        # 曾照样输出 JSON）。SUPPRESS 让未显式给出时压根不进 namespace，
        # 父级的值才保得住。
        sp.add_argument("--json", action="store_true", default=argparse.SUPPRESS,
                        help="JSON 输出（默认）")
        sp.add_argument("--human", action="store_true", default=argparse.SUPPRESS,
                        help="人类可读输出")
        return sp

    add("ping", "探活：报告 Zotero 版本 / 库 id / 库版本")

    p = add("search", "检索条目（对应通用 Zotero 读取能力：条目检索）")
    p.add_argument("--query", "-q", default=None, help="检索词")
    p.add_argument("--qmode", default=None, choices=["titleCreatorYear", "everything"],
                   help="everything = 含全文（默认 Zotero 行为：titleCreatorYear）")
    p.add_argument("--item-type", dest="item_type", default=None,
                   help="条目类型，如 journalArticle / conferencePaper / book")
    p.add_argument("--tag", default=None, help="按标签过滤")
    p.add_argument("--collection", default=None, help="集合名或集合 key")
    p.add_argument("--top", action="store_true", help="只要顶层条目（/items/top）")
    p.add_argument("--limit", type=int, default=25, help="返回条数（默认 25，上限 100）")
    p.add_argument("--offset", type=int, default=0, help="起始偏移（分页用）")
    p.add_argument("--sort", default=None,
                   help="排序字段：dateModified/dateAdded/date/title/creator")
    p.add_argument("--direction", default=None, choices=["asc", "desc"], help="排序方向")

    p = add("get", "取单个条目详情（对应：条目读取）")
    p.add_argument("--key", "-k", required=False, help="条目 key（8 位）")
    p.add_argument("--include", default=None, help="notes,attachments,annotations 逗号分隔")
    p.add_argument("--fields", default="standard", choices=["standard", "all"],
                   help="all 时额外给出 extraFields")
    p.add_argument("--color", default=None, help="配合 --include annotations：按颜色过滤")
    p.add_argument("--attachment", default=None, help="只查指定附件 key 的批注")
    p.add_argument("--split-comment", action="store_true",
                   help="按 🔤…🔤 区间切分评论归属")

    p = add("children", "列子对象（默认显式查询 attachments/notes/annotations）")
    p.add_argument("--key", "-k", required=False, help="父条目 key")
    p.add_argument("--item-type", dest="item_type", default=None,
                   help="只查某一类：attachment / note / annotation / ...（单数，直接透传给 Zotero）")
    p.add_argument("--include", default=None,
                   help="子对象类别，逗号分隔，**必须用复数**："
                        "attachments,notes,annotations（与 Zotero API 口径一致；"
                        "单数会报参数错误）")
    p.add_argument("--limit", type=int, default=None,
                   help="每类最多返回多少条（默认不传 = 翻完全部分页取全量；"
                        "传了就是显式上限，超出时 warning 会如实报出实际总数）")
    p.add_argument("--offset", type=int, default=0,
                   help="起始偏移（只在传了 --limit 时有意义）")
    p.add_argument("--split-comment", action="store_true", help="切分批注评论归属")

    p = add("annotations", "取批注（自动分页突破 100 条截断、自动扫全部附件）")
    p.add_argument("--key", "-k", required=False, help="父条目 key 或附件 key")
    p.add_argument("--color", default=None,
                   help="yellow/green/blue/red/purple 或 #rrggbb")
    p.add_argument("--attachment", default=None, help="只查指定附件")
    p.add_argument("--first-attachment", action="store_true", help="只查第一个 PDF 附件")
    p.add_argument("--all", action="store_true",
                   help="显式表达「取全部」。**默认就是全部**，此开关是无操作，"
                        "保留只为把意图写清楚")
    p.add_argument("--limit", type=int, default=None,
                   help="最多输出多少条（默认不传 = 输出全部命中；用于快速预览）")
    p.add_argument("--page-size", type=int, default=ANNOTATION_PAGE_SIZE,
                   help="分页大小（Zotero 在 100 处静默截断，勿调大）")
    p.add_argument("--split-comment", action="store_true",
                   help="按 🔤…🔤 区间切分评论归属")

    p = add("retrieve", "在附件全文里做 BM25 排序，返回带**估算页码**的片段")
    p.add_argument("--key", "-k", required=False, help="父条目 key 或附件 key")
    p.add_argument("--query", "-q", required=False, help="检索词")
    p.add_argument("--passages", type=int, default=4, help="返回片段数（默认 4）")
    p.add_argument("--passage-chars", dest="passage_chars", type=int, default=700,
                   help="片段切分的目标长度")
    p.add_argument("--max-chars", dest="max_chars", type=int, default=1000,
                   help="单片段输出上限")

    p = add("attachment", "解析附件的磁盘路径")
    p.add_argument("--key", "-k", required=False, help="条目 key 或附件 key")
    p.add_argument("--all", action="store_true", help="父条目下所有附件")
    p.add_argument("--storage", default=None,
                   help="Zotero storage 目录（默认自动探测，或 $RV_ZOTERO_STORAGE）")

    p = add("fulltext", "取附件全文（--out 落盘；--pages 只是本地切分，不是向 Zotero 按页取）")
    p.add_argument("--key", "-k", required=False, help="条目 key 或附件 key")
    p.add_argument("--pages", default=None, metavar="A-B",
                   help="本地切出第 A-B 页（如 3-7 或单页 5）。"
                        "Zotero 不支持按页取，整篇仍会被取回一次")
    p.add_argument("--out", default=None, help="写入文件（UTF-8）")

    p = add("export", "导出引用（bibtex/biblatex/ris/csljson/citation）")
    p.add_argument("--key", "-k", action="append", default=None, help="条目 key（可重复）")
    p.add_argument("--format", default="bibtex",
                   choices=["bibtex", "biblatex", "ris", "csljson", "citation"])
    p.add_argument("--style", default="apa", choices=["apa", "ieee", "gb-t-7714"],
                   help="配合 --format citation 的样式")
    p.add_argument("--out", default=None, help="写入文件")

    add("collections", "列集合（含层级）")

    p = add("tags", "列标签（默认全部）")
    p.add_argument("--limit", type=int, default=None,
                   help="最多输出多少个（默认不传 = 输出全部命中，用于预览）")
    p.add_argument("--offset", type=int, default=0,
                   help="从第几个命中开始输出（默认 0）")
    p.add_argument("--query", "-q", default=None,
                   help="子串过滤（在**全量**标签上过滤，不是只在首页里找）")

    add("searches", "列保存的检索")

    p = add("changes", "库增量（基线 / 快照差分）")
    p.add_argument("--since", type=int, default=None, help="上次的库版本号")
    p.add_argument("--db", default=None, help="快照文件（可报删除）")

    return parser


COMMANDS = {
    "ping": cmd_ping,
    "search": cmd_search,
    "get": cmd_get,
    "children": cmd_children,
    "annotations": cmd_annotations,
    "retrieve": cmd_retrieve,
    "attachment": cmd_attachment,
    "fulltext": cmd_fulltext,
    "export": cmd_export,
    "collections": cmd_collections,
    "tags": cmd_tags,
    "searches": cmd_searches,
    "changes": cmd_changes,
}


def _subparsers(parser):
    """取出顶层 parser 的子命令表（``{名字: 子 parser}``）。"""
    for action in getattr(parser, "_actions", ()):
        if isinstance(action, argparse._SubParsersAction):
            return action.choices
    return {}


def _split_argv(parser, argv):
    """定位子命令，**跳过顶层选项的值**。

    天真地取「第一个不以 - 开头的 token」是错的：``--api http://… ping`` 里第一个
    自由 token 是 ``--api`` 的**值**，不是子命令。找不到子命令就会让下面所有容错
    静默失效。
    """
    choices = _subparsers(parser)
    value_opts = set()
    for action in getattr(parser, "_actions", ()):
        if isinstance(action, argparse._SubParsersAction):
            continue
        if action.option_strings and action.nargs != 0:
            value_opts.update(action.option_strings)
    index = 0
    while index < len(argv):
        token = argv[index]
        if token in choices:
            return token, index
        option = token.split("=", 1)[0]
        if token.startswith("-") and len(token) > 1 and "=" not in token \
                and option in value_opts:
            index += 2
        else:
            index += 1
    return None, None


def normalize_argv(argv, parser=None):
    """容错：允许把 `--key` 写成位置参数（`annotations ABCD1234`）。

    对**任何定义了 ``--key`` 的子命令**生效（列表从 parser 现取，避免硬编码漂移，
    例如漏掉 `export`）。插入位置与选项顺序无关：把那个自由 token 摘出来，改成
    ``--key <token>`` 追加到末尾。
    """
    if not argv:
        return argv
    parser = parser if parser is not None else build_parser()
    command, index = _split_argv(parser, argv)
    if command is None:
        return argv
    sub = _subparsers(parser).get(command)
    if sub is None:
        return argv
    value_opts = set()
    has_key = False
    for action in getattr(sub, "_actions", ()):
        if action.dest == "key":
            has_key = True
        if action.option_strings and action.nargs != 0:
            value_opts.update(action.option_strings)
    if not has_key:
        return argv
    for token in argv:
        if token in ("--key", "-k") or token.startswith("--key="):
            return argv
    cursor = index + 1
    while cursor < len(argv):
        token = argv[cursor]
        if token == "--":
            cursor += 1
            break
        if token.startswith("-") and len(token) > 1:
            option = token.split("=", 1)[0]
            cursor += 2 if ("=" not in token and option in value_opts) else 1
            continue
        break
    if cursor >= len(argv) or argv[cursor].startswith("-"):
        return argv
    return argv[:cursor] + argv[cursor + 1:] + ["--key", argv[cursor]]


def main(argv=None):
    force_utf8_stdout()
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    argv = normalize_argv(argv, parser)
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return EXIT_USAGE
    # `--json` 是默认行为：只有显式 `--human` 才切人类可读输出。
    # 两个都显式给出是自相矛盾的请求，报参数错比悄悄挑一个更诚实。
    human = bool(getattr(args, "human", False))
    as_json = bool(getattr(args, "json", False))
    if human and as_json:
        sys.stderr.write("参数错误：--human 与 --json 不能同时使用\n")
        return EXIT_USAGE
    if not human:
        args.json = True
    args.human = human
    handler = COMMANDS.get(args.command)
    if handler is None:  # pragma: no cover - argparse 已挡住
        parser.print_help()
        return EXIT_USAGE
    client = ZoteroClient(api_base=args.api_base, library=args.library,
                          timeout=args.timeout)
    try:
        return handler(client, args)
    except UsageError as exc:
        sys.stderr.write("参数错误：%s\n" % exc)
        return EXIT_USAGE
    except ConnectionFailure as exc:
        sys.stderr.write("%s\n" % exc)
        return EXIT_CONNECTION
    except NotFound as exc:
        sys.stderr.write("%s\n" % exc)
        return EXIT_NOT_FOUND
    except ApiError as exc:
        sys.stderr.write("%s\n" % exc)
        return EXIT_HTTP
    except BrokenPipeError:  # pragma: no cover - 管道提前关闭
        return EXIT_OK
    except KeyboardInterrupt:  # pragma: no cover
        return 130


if __name__ == "__main__":
    sys.exit(main())
