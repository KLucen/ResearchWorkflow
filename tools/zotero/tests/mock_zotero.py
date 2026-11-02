# -*- coding: utf-8 -*-
"""离线 mock Zotero Local API —— 让单测**不依赖 Zotero 是否在运行**。

.. important::

   **本 mock 的语义以真实 Zotero 10.0.7 的实测结果为准，改动前请先在真机复核。**

   mock 只能验证「工具在 mock 建模的世界里自洽」，**不能**验证工具与真实 API 一致。
   一旦 mock 与真机不符，整个离线套件会在一个错误的世界里给人虚假信心——本项目
   已经踩过一次：mock 曾把「条目级 ``itemType=annotation`` 过滤只对附件 key 生效」
   钉死，而真实 API 在条目 key 上会**跨附件聚合**，于是离线全绿、真机结论相反。
   凡是对真实接口语义的断言，**先在真机上复核，再回来改这里**。

它刻意复现了真实 Local API 那些会咬人的行为（都是实测出来的，不是猜的）：

1. **HTTP/1.0**：真实 Local API 回 ``HTTP/1.0 200 OK``。单测因此能覆盖
   「只认 HTTP/1.1 的客户端会握手失败」这条坑。
2. **``Total-Results`` 响应头**：分页总数的**唯一**可靠来源。
3. **``/items/<key>/children`` 不带 ``itemType`` 时静默漏掉批注**，且**不报错**。
   条目 key → 只回附件与笔记（0 条批注）；附件 key → **什么都不回**（空数组）。
   真机实测两者都不给批注，批注只能靠 ``?itemType=annotation`` 拿。
4. **条目级 ``itemType=annotation`` 会跨附件聚合**：``/items/<条目KEY>/children?
   itemType=annotation`` 返回该条目**所有附件**上的批注（真机实测：条目 130 条 =
   两个附件的 130 + 0 条）。附件 key 上调用则只回它自己的批注。两者都保留。
5. **100 条静默截断**：``?itemType=annotation`` 时无论 ``limit`` 传多大，
   服务端最多给 100 条；``/tags`` 与 ``/searches`` 同样截。
6. **``?page=N`` 被静默忽略**：``/fulltext`` 传任何页码都返回整篇。
7. **``?format=citation`` 不被支持**：真实 API 回 HTTP 400
   ``Invalid 'format' value 'citation'``。
8. **``/itemTypes`` 是 404**。
9. **CJK 评论带 ``🔤…🔤`` 机器词典区间**，且常见
   ``🔤机器译文🔤\\n研究者手写的话`` 这种「区间外还有研究者的话」的形态。
10. **批注只挂在某一个附件上**：一篇论文常有原文/双语/译文多个附件，
    只有其中一个带批注，另外的是 0 条。

用法::

    from mock_zotero import MockZotero, make_fixture
    with MockZotero() as server:          # 起在 127.0.0.1 的随机端口
        cli.main(["--api", server.api_base, "annotations", "--key", "ABCD1234"])
"""

from __future__ import annotations

import json
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

#: 真实 Local API 的单页硬上限——传更大的 limit 也没用。
REAL_PAGE_CAP = 100

#: 只支持这些导出格式；``citation`` 真实 API 会回 400。
SUPPORTED_EXPORT_FORMATS = ("bibtex", "biblatex", "ris", "csljson")

MACHINE_MARK = "\U0001f524"


def _annotation(key, parent, color, text, comment, page, sort_index=None):
    return {
        "key": key,
        "version": 100,
        "library": {"type": "user", "id": 0, "name": "mock"},
        "links": {"self": "http://localhost/items/%s" % key},
        "meta": {"numChildren": 0},
        "data": {
            "key": key,
            "version": 100,
            "itemType": "annotation",
            "parentItem": parent,
            "annotationType": "highlight",
            "annotationText": text,
            "annotationComment": comment,
            "annotationColor": color,
            "annotationPageLabel": str(page),
            "annotationSortIndex": sort_index or "%05d|00000000|00000" % page,
            "annotationPosition": json.dumps(
                {"pageIndex": page - 1, "rects": [[10, 20, 300, 40]]}),
            "tags": [],
            "relations": {},
            "dateAdded": "2024-01-01T00:00:00Z",
            "dateModified": "2024-01-02T00:00:00Z",
        },
    }


def _attachment(key, parent, filename, content_type="application/pdf"):
    return {
        "key": key,
        "version": 100,
        "library": {"type": "user", "id": 0, "name": "mock"},
        "links": {"self": "http://localhost/items/%s" % key},
        "meta": {"numChildren": 0},
        "data": {
            "key": key,
            "version": 100,
            "itemType": "attachment",
            "parentItem": parent,
            "linkMode": "imported_file",
            "contentType": content_type,
            "charset": "",
            "filename": filename,
            "title": filename,
            "md5": None,
            "mtime": 1700000000000,
            "tags": [],
            "relations": {},
            "dateAdded": "2024-01-01T00:00:00Z",
            "dateModified": "2024-01-01T00:00:00Z",
        },
    }


def _item(key, title, item_type="journalArticle", **extra):
    data = {
        "key": key,
        "version": 100,
        "itemType": item_type,
        "title": title,
        "creators": [{"creatorType": "author", "firstName": "Ada", "lastName": "Lovelace"},
                     {"creatorType": "author", "firstName": "Alan", "lastName": "Turing"}],
        "date": "2023-05-01",
        "abstractNote": "Placeholder abstract for offline tests.",
        "publicationTitle": "Journal of Placeholder Studies",
        "volume": "12",
        "issue": "3",
        "pages": "100-120",
        "DOI": "10.0000/placeholder.2023.001",
        "url": "https://example.invalid/paper",
        "tags": [{"tag": "placeholder"}],
        "collections": ["COLL0001"],
        "relations": {},
        "dateAdded": "2024-01-01T00:00:00Z",
        "dateModified": "2024-01-01T00:00:00Z",
    }
    data.update(extra)
    return {
        "key": key,
        "version": 100,
        "library": {"type": "user", "id": 0, "name": "mock"},
        "links": {"self": "http://localhost/items/%s" % key},
        "meta": {"numChildren": 0},
        "data": data,
    }


def make_fixture(annotation_count=130):
    """造一套确定性的测试数据。

    默认 130 条批注 —— 故意 **> 100**，这样任何「只取一页」的实现都会露馅。
    批注只挂在 ``ATT00001`` 上；``ATT00002`` 是同一篇的另一个附件，0 条批注——
    复现「批注只挂在某一个附件上」。
    """
    items = {}
    order = []

    parent = _item("ABCD1234", "A Placeholder Survey of Synthetic Benchmarks")
    items[parent["key"]] = parent
    order.append(parent["key"])

    plain = _item("WXYZ5678", "Another Placeholder Paper on Neutral Topics",
                  itemType="conferencePaper")
    items[plain["key"]] = plain
    order.append(plain["key"])

    att1 = _attachment("ATT00001", "ABCD1234", "placeholder-original.pdf")
    att2 = _attachment("ATT00002", "ABCD1234", "placeholder-bilingual.pdf")
    att_plain = _attachment("ATT00003", "WXYZ5678", "another-placeholder.pdf")
    for att in (att1, att2, att_plain):
        items[att["key"]] = att
        order.append(att["key"])

    colors = ["#ffd400", "#5fb236", "#2ea8e5", "#ff6666", "#a28ae5"]
    annotations = []
    for index in range(annotation_count):
        color = colors[index % len(colors)]
        page = (index // 5) + 1
        if index % 4 == 0:
            # 🔤…🔤 区间 + 区间外还有研究者自己的话
            comment = ("%sMachine gloss for snippet %d.%s\n"
                       "Researcher note %d: keep for the concept page."
                       % (MACHINE_MARK, index, MACHINE_MARK, index))
        elif index % 4 == 1:
            comment = "%sPure machine gloss %d.%s" % (MACHINE_MARK, index, MACHINE_MARK)
        elif index % 4 == 2:
            comment = "Hand-written researcher remark %d." % index
        else:
            comment = ""
        annotations.append(_annotation(
            "ANN%05d" % index, "ATT00001", color,
            "Highlighted sentence number %d about neutral subject matter." % index,
            comment, page))
    for ann in annotations:
        items[ann["key"]] = ann

    fulltext_pages = 27
    body = "\n".join(
        "Page %d line about benchmarks, evaluation and neutral metrics." % (p + 1)
        for p in range(fulltext_pages * 12))
    fulltext = {"ATT00001": body, "ATT00003": "Short indexed body for the second paper."}

    collections = [
        {"key": "COLL0001", "version": 5,
         "data": {"key": "COLL0001", "version": 5, "name": "Reading List",
                  "parentCollection": False, "numItems": 2}},
        {"key": "COLL0002", "version": 6,
         "data": {"key": "COLL0002", "version": 6, "name": "Nested Topic",
                  "parentCollection": "COLL0001", "numItems": 1}},
    ]

    tags = [{"tag": "placeholder", "links": {}, "meta": {}},
            {"tag": "benchmark", "links": {}, "meta": {}},
            {"tag": "survey", "links": {}, "meta": {}}]

    return {
        "items": items,
        "order": order,
        "annotations": annotations,
        "annotations_by_parent": {"ATT00001": annotations},
        "fulltext": fulltext,
        "fulltext_pages": {"ATT00001": fulltext_pages, "ATT00003": 3},
        "collections": collections,
        "tags": tags,
        "searches": [{"key": "SRCH0001", "version": 9,
                      "data": {"key": "SRCH0001", "version": 9,
                               "name": "Recently Added"}}],
        "library_version": 477,
    }


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"          # ← 真实 Local API 就是 HTTP/1.0
    server_version = "MockZotero/1.0"
    sys_version = ""
    fixture = None

    def log_message(self, fmt, *a):        # 静音，别污染测试输出
        pass

    # ---------- 响应工具 ----------
    def _send(self, status, body, content_type="application/json", headers=None):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False)
        raw = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        # 真实 Local API 每次都带这几个头；ping 子命令读的就是它们。
        self.send_header("X-Zotero-Version", "7.0.0-mock")
        self.send_header("Zotero-API-Version", "3")
        self.send_header("Zotero-Schema-Version", "44")
        self.send_header("Zotero-Server-ID", "mock-server")
        self.send_header("Last-Modified-Version", str(self.fixture["library_version"]))
        self.send_header("Content-Length", str(len(raw)))
        for key, value in (headers or {}).items():
            self.send_header(key, str(value))
        self.end_headers()
        self.wfile.write(raw)

    def _total(self, value):
        return {"Total-Results": value}

    # ---------- 路由 ----------
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")
        query = urllib.parse.parse_qs(parsed.query)
        parts = [p for p in path.split("/") if p]
        # 期望 /api/<library>/...
        if not parts or parts[0] != "api":
            return self._send(404, "Not found", "text/plain")
        parts = parts[1:]
        if parts and parts[0] in ("users", "groups"):
            parts = parts[2:]
        fixture = self.fixture

        # /itemTypes 在真实 Local API 上是 404
        if parts and parts[0] == "itemTypes":
            return self._send(404, "Not found", "text/plain")

        if not parts:
            return self._send(200, {"library": "mock"})

        head = parts[0]

        if head == "items" and len(parts) == 1:
            return self._list_items(query, fixture)
        if head == "items" and len(parts) >= 2:
            return self._item_route(parts[1:], query, fixture)
        if head == "collections":
            if len(parts) == 1:
                return self._send(200, [c for c in fixture["collections"]],
                                  headers=self._total(len(fixture["collections"])))
            for col in fixture["collections"]:
                if col["key"].lower() == parts[1].lower() or \
                        (col["data"].get("name") or "").lower() == parts[1].lower():
                    return self._send(200, col)
            return self._send(404, "Not found", "text/plain")
        if head == "tags":
            return self._paged(fixture["tags"], query)
        if head == "searches":
            return self._paged(fixture["searches"], query)
        return self._send(404, "Not found", "text/plain")

    def _paged(self, rows, query):
        """按真实 Local API 的口径分页：``start`` 生效、单页硬上限 100。

        真实 API 对 ``/tags`` 和 ``/searches`` 一样会**静默截断在 100 条**，
        所以 mock 也必须截——否则客户端漏写分页循环时测试会假装通过。
        """
        start = int((query.get("start") or ["0"])[0])
        limit = min(int((query.get("limit") or ["50"])[0]), REAL_PAGE_CAP)
        return self._send(200, rows[start:start + limit],
                          headers=self._total(len(rows)))

    def _list_items(self, query, fixture):
        items = [fixture["items"][k] for k in fixture["order"]]
        item_type = (query.get("itemType") or [None])[0]
        if item_type:
            items = [i for i in items if i["data"].get("itemType") == item_type]
        else:
            items = [i for i in items
                     if i["data"].get("itemType") not in ("annotation", "attachment")]
        term = (query.get("q") or [None])[0]
        if term:
            low = term.lower()
            items = [i for i in items if low in json.dumps(i["data"], ensure_ascii=False).lower()]
        start = int((query.get("start") or ["0"])[0])
        limit = min(int((query.get("limit") or ["50"])[0]), REAL_PAGE_CAP)
        window = items[start:start + limit]
        return self._send(200, window, headers=self._total(len(items)))

    def _item_route(self, rest, query, fixture):
        key = rest[0]
        obj = None
        for candidate in fixture["items"].values():
            if candidate["key"].upper() == key.upper():
                obj = candidate
                break

        # /items/<key>/children
        if len(rest) >= 2 and rest[1] == "children":
            if obj is None:
                return self._send(404, "Not found", "text/plain")
            return self._children(obj, query, fixture)

        # /items/<key>/fulltext
        if len(rest) >= 2 and rest[1] == "fulltext":
            return self._fulltext(key, fixture)

        if obj is None:
            return self._send(404, "Not found", "text/plain")

        fmt = (query.get("format") or [None])[0]
        if fmt:
            if fmt not in SUPPORTED_EXPORT_FORMATS:
                return self._send(
                    400, "Invalid 'format' value '%s'" % fmt, "text/plain")
            body = "%s export for %s" % (fmt.upper(), obj["data"].get("title"))
            return self._send(200, body, "text/plain; charset=utf-8")
        return self._send(200, obj)

    def _children(self, parent, query, fixture):
        key = parent["key"]
        is_attachment = parent["data"].get("itemType") == "attachment"

        attachments = [fixture["items"][k] for k in fixture["order"]
                       if fixture["items"][k]["data"].get("itemType") == "attachment"
                       and fixture["items"][k]["data"].get("parentItem") == key]
        if is_attachment:
            attachments = []

        annotations = []
        if is_attachment:
            annotations = list(fixture["annotations_by_parent"].get(key, []))
        else:
            # 裸 /children（不带 itemType）**静默漏掉批注**——只回附件/笔记。
            # 带 itemType=annotation 时，条目级调用**跨附件聚合**各附件的批注，
            # 与真机一致（真机实测：条目 130 = 附件 130 + 附件 0）。
            want = (query.get("itemType") or [None])[0]
            if want == "annotation":
                for att in attachments:
                    annotations.extend(
                        fixture["annotations_by_parent"].get(att["key"], []))

        want = (query.get("itemType") or [None])[0]
        if want == "annotation":
            pool = annotations
        elif want == "attachment":
            pool = attachments
        elif want == "note":
            pool = []
        else:
            # ← 坑 #1：不传 itemType 时批注被静默吞掉
            pool = attachments

        start = int((query.get("start") or ["0"])[0])
        limit = min(int((query.get("limit") or ["50"])[0]), REAL_PAGE_CAP)
        window = pool[start:start + limit]
        return self._send(200, window, headers=self._total(len(pool)))

    def _fulltext(self, key, fixture):
        # 父条目 key → 404（真实行为：必须传附件 key）
        if key not in fixture["fulltext"]:
            return self._send(404, "Not found", "text/plain")
        # ← 坑 #5：?page=N 被静默忽略，永远返回整篇
        pages = fixture["fulltext_pages"].get(key, 1)
        return self._send(200, {
            "content": fixture["fulltext"][key],
            "indexedPages": pages,
            "totalPages": pages,
        })


class MockZotero(object):
    """把 mock 服务器跑在后台线程里，带 ``api_base`` 方便直接喂给 CLI。"""

    def __init__(self, fixture=None, host="127.0.0.1", port=0):
        self.fixture = fixture or make_fixture()
        self.host = host
        self.port = port
        self._httpd = None
        self._thread = None
        self.requests = []

    @property
    def api_base(self):
        return "http://%s:%d/api" % (self.host, self.port)

    def start(self):
        handler = type("_BoundHandler", (_Handler,), {"fixture": self.fixture})
        self._httpd = HTTPServer((self.host, self.port), handler)
        self.port = self._httpd.server_address[1]
        self._thread = threading.Thread(target=self._httpd.serve_forever)
        self._thread.daemon = True
        self._thread.start()
        return self

    def stop(self):
        if self._httpd is not None:
            self._httpd.shutdown()
            self._httpd.server_close()
            self._httpd = None
        if self._thread is not None:
            self._thread.join(timeout=5)
            self._thread = None

    def __enter__(self):
        return self.start()

    def __exit__(self, *exc):
        self.stop()
        return False


def main(argv=None):
    """手动起一个 mock 服务器，方便 curl 着玩。"""
    import sys
    port = 23199
    if argv and len(argv) > 1:
        port = int(argv[1])
    server = MockZotero(port=port).start()
    print("mock Zotero on %s (Ctrl-C 退出)" % server.api_base)
    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop()
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv))
