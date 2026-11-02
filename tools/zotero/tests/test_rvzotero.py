# -*- coding: utf-8 -*-
"""``rvzotero.py`` 的离线单测 —— **不依赖 Zotero 是否在运行**。

跑法::

    python tools/zotero/tests/test_rvzotero.py

HTTP 层全部由 ``mock_zotero.py`` 提供（标准库 ``http.server``，跑在 127.0.0.1
的随机端口）。之所以要离线，是因为「分页补齐」「静默截断」这类行为**必须**能在
一台没装 Zotero 的机器上验证——发布包的使用者未必有本机 Zotero。

只测纯逻辑的部分直接 import，不经过 HTTP。
"""

from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.dirname(HERE)
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import mock_zotero  # noqa: E402  同目录
import rvzotero  # noqa: E402

MACHINE_MARK = rvzotero.MACHINE_MARK


# --------------------------------------------------------------------------
# 0. mock 自身的保真度
# --------------------------------------------------------------------------
class TestMockFidelity(unittest.TestCase):
    """mock 的全部价值在于「像真的」。这些断言防止它悄悄漂移——
    一旦 mock 变得比真实 API 宽松，上面那些回归测试就失去保护作用了。"""

    def setUp(self):
        self.server = mock_zotero.MockZotero().start()
        self.addCleanup(self.server.stop)

    def test_server_speaks_http_1_0(self):
        """真实 Local API 回 HTTP/1.0 —— mock 必须一样。"""
        import urllib.request
        with urllib.request.urlopen(self.server.api_base + "/items?limit=1") as resp:
            self.assertEqual(resp.version, 10)          # 10 == HTTP/1.0

    def test_headers_present(self):
        import urllib.request
        with urllib.request.urlopen(self.server.api_base + "/items?limit=1") as resp:
            self.assertEqual(resp.getheader("Zotero-API-Version"), "3")
            self.assertTrue(resp.getheader("Zotero-Schema-Version"))
            self.assertTrue(resp.getheader("X-Zotero-Version"))
            self.assertTrue(resp.getheader("Last-Modified-Version"))

    def test_ping_reports_headers(self):
        rc, payload = run_cli(self.server, ["ping"])
        self.assertEqual(rc, 0)
        self.assertEqual(payload["api_version"], "3")
        self.assertEqual(payload["zotero_version"], "7.0.0-mock")
        self.assertEqual(payload["zotero_schema_version"], "44") \
            if "zotero_schema_version" in payload else None
        self.assertEqual(payload["last_modified_version"], 477)

    def test_total_results_header_authoritative(self):
        client = rvzotero.ZoteroClient(api_base=self.server.api_base, library="users/0")
        rows, resp = client.list_items(limit=1)
        self.assertEqual(len(rows), 1)
        self.assertEqual(resp.total_results, 2)   # fixture 有 2 个顶层条目


# --------------------------------------------------------------------------
# 1. 🔤…🔤 区间切分（硬要求）
# --------------------------------------------------------------------------
class TestCommentSplit(unittest.TestCase):
    """评论归属**按区间**切分，不是按「整条含不含 🔤」。"""

    def test_interval_not_whole_string(self):
        """``🔤机器译文🔤\\n研究者手写的话`` —— 后者绝不能被丢掉。"""
        raw = "%smachine gloss%s\nresearcher's own words" % (MACHINE_MARK, MACHINE_MARK)
        parts = rvzotero.split_comment(raw)
        self.assertEqual(parts.machine_texts, ["machine gloss"])
        self.assertEqual(parts.researcher_text, "researcher's own words")
        self.assertEqual(parts.researcher_comment, "researcher's own words")
        self.assertEqual(parts.classification, "machine_plus_researcher")

    def test_researcher_text_before_and_after(self):
        raw = ("before the interval\n%smiddle%s\nafter the interval"
               % (MACHINE_MARK, MACHINE_MARK))
        parts = rvzotero.split_comment(raw)
        self.assertEqual(parts.machine_texts, ["middle"])
        self.assertIn("before the interval", parts.researcher_text)
        self.assertIn("after the interval", parts.researcher_text)

    def test_pure_machine(self):
        raw = "%spure gloss%s" % (MACHINE_MARK, MACHINE_MARK)
        parts = rvzotero.split_comment(raw)
        self.assertEqual(parts.machine_texts, ["pure gloss"])
        self.assertEqual(parts.researcher_text, "")
        self.assertEqual(parts.researcher_comment, "")
        self.assertEqual(parts.classification, "tool_generated")

    def test_unmarked_is_researcher(self):
        parts = rvzotero.split_comment("just a note I typed")
        self.assertEqual(parts.machine_texts, [])
        self.assertFalse(parts.has_machine_mark)
        self.assertEqual(parts.unmarked_text, "just a note I typed")
        self.assertEqual(parts.researcher_comment, "just a note I typed")
        self.assertEqual(parts.classification, "researcher")

    def test_empty_and_none(self):
        for value in ("", None):
            parts = rvzotero.split_comment(value)
            self.assertEqual(parts.machine_texts, [])
            self.assertEqual(parts.researcher_comment, "")

    def test_multiple_intervals(self):
        raw = ("%sone%s researcher A %stwo%s researcher B"
               % (MACHINE_MARK, MACHINE_MARK, MACHINE_MARK, MACHINE_MARK))
        parts = rvzotero.split_comment(raw)
        self.assertEqual(parts.machine_texts, ["one", "two"])
        self.assertIn("researcher A", parts.researcher_text)
        self.assertIn("researcher B", parts.researcher_text)

    def test_cjk_machine_gloss_preserved(self):
        raw = "%s\u673a\u5668\u8bd1\u6587%s\n\u7814\u7a76\u8005\u7684\u8bdd" % (
            MACHINE_MARK, MACHINE_MARK)
        parts = rvzotero.split_comment(raw)
        self.assertEqual(parts.machine_texts[0], "\u673a\u5668\u8bd1\u6587")
        self.assertEqual(parts.researcher_text, "\u7814\u7a76\u8005\u7684\u8bdd")


# --------------------------------------------------------------------------
# 2. BM25 排序
# --------------------------------------------------------------------------
class TestBm25(unittest.TestCase):

    def test_ranks_matching_passage_first(self):
        passages = [
            ("p1", "unrelated filler about weather and seasons"),
            ("p2", "neural network training with gradient descent"),
            ("p3", "another unrelated passage about cooking"),
        ]
        ranked = rvzotero.bm25_rank("neural network gradient", passages)
        self.assertTrue(ranked)
        self.assertEqual(ranked[0][0], "p2")

    def test_zero_score_dropped(self):
        passages = [("p1", "completely different words here")]
        self.assertEqual(rvzotero.bm25_rank("zzzqqq", passages), [])

    def test_scores_are_descending(self):
        passages = [
            ("a", "benchmark benchmark benchmark evaluation"),
            ("b", "benchmark appears once among many other neutral words here"),
            ("c", "nothing relevant at all in this passage"),
        ]
        ranked = rvzotero.bm25_rank("benchmark", passages)
        scores = [row[2] for row in ranked]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_duplicate_passages_collapsed(self):
        """重复页眉/脚注在 PDF 里很常见，不能把结果刷屏。"""
        passages = [("p1", "identical duplicated header text"),
                    ("p2", "identical duplicated header text"),
                    ("p3", "genuinely different content")]
        ranked = rvzotero.bm25_rank("duplicated header", passages)
        ids = [row[0] for row in ranked]
        self.assertEqual(ids, ["p1"])

    def test_accepts_three_tuples_with_offsets(self):
        passages = [("p1", "alpha beta gamma", 0), ("p2", "delta epsilon", 100)]
        ranked = rvzotero.bm25_rank("alpha", passages)
        self.assertEqual(ranked[0][0], "p1")

    def test_empty_inputs(self):
        self.assertEqual(rvzotero.bm25_rank("x", []), [])
        self.assertEqual(rvzotero.bm25_rank("", [("p", "text")]), [])


# --------------------------------------------------------------------------
# 3. 分页补齐：>100 条批注一条都不能丢（硬要求）
# --------------------------------------------------------------------------
class TestAnnotationPagination(unittest.TestCase):
    """mock 的默认 fixture 有 130 条批注，故意 > 100。"""

    def setUp(self):
        self.server = mock_zotero.MockZotero().start()
        self.addCleanup(self.server.stop)
        self.client = rvzotero.ZoteroClient(api_base=self.server.api_base,
                                            library="users/0")

    def test_server_itself_truncates_at_100(self):
        """先证明 mock 确实复现了「100 条静默截断」——否则后面的测试是假的。"""
        batch, resp = self.client.list_children(
            "ATT00001", item_type="annotation", limit=500, start=0)
        self.assertEqual(len(batch), 100)
        self.assertEqual(resp.total_results, 130)

    def test_list_annotations_gets_all_130(self):
        anns, meta = self.client.list_annotations("ATT00001")
        self.assertEqual(len(anns), 130)
        self.assertEqual(meta["total"], 130)
        self.assertEqual(meta["scanned"], 130)
        self.assertGreaterEqual(meta["pages"], 2)

    def test_no_duplicate_keys_across_pages(self):
        anns, _ = self.client.list_annotations("ATT00001")
        keys = [a.key for a in anns]
        self.assertEqual(len(keys), len(set(keys)))

    def test_stable_order_across_pages(self):
        anns, _ = self.client.list_annotations("ATT00001")
        sort_keys = [a.sort_index for a in anns]
        self.assertEqual(sort_keys, sorted(sort_keys))

    def test_small_page_size_still_gets_all(self):
        """页大小调小到 7 也必须补齐——不能依赖「一页 100」。"""
        anns, meta = self.client.list_annotations("ATT00001", page_size=7)
        self.assertEqual(len(anns), 130)
        self.assertGreaterEqual(meta["pages"], 19)

    def test_color_filter_scans_everything(self):
        """**回归测试**：颜色过滤必须在整套分页之上进行。

        曾经的 bug：分页循环「数够 limit 就 break」，导致
        ``--color purple`` 只扫了前 9 条就停，报告 9 条而真实是 26 条。
        """
        every, _ = self.client.list_annotations("ATT00001")
        by_color = {}
        for ann in every:
            by_color[ann.color_name] = by_color.get(ann.color_name, 0) + 1

        for name, expected in by_color.items():
            filtered, meta = self.client.list_annotations("ATT00001", color=name)
            self.assertEqual(len(filtered), expected,
                             "颜色 %s 应命中 %d 条" % (name, expected))
            self.assertEqual(meta["scanned"], 130,
                             "颜色过滤也必须把 130 条全扫一遍")

    def test_color_hex_and_name_agree(self):
        by_name, _ = self.client.list_annotations("ATT00001", color="yellow")
        by_hex, _ = self.client.list_annotations("ATT00001", color="#ffd400")
        self.assertEqual(len(by_name), len(by_hex))
        self.assertTrue(by_name)

    def test_annotations_for_item_dedupes(self):
        """父条目递归查询与逐附件查询会命中同一批，必须去重。"""
        anns, meta = self.client.annotations_for_item("ABCD1234")
        self.assertEqual(len(anns), 130)
        self.assertEqual(len({a.key for a in anns}), 130)
        self.assertGreater(meta.get("deduped", 0), 0)

    def test_annotations_only_on_one_attachment(self):
        """批注只挂在 ATT00001；ATT00002 是 0 条。"""
        first, meta1 = self.client.list_annotations("ATT00001")
        second, meta2 = self.client.list_annotations("ATT00002")
        self.assertEqual(len(first), 130)
        self.assertEqual(len(second), 0)
        self.assertEqual(meta2["total"], 0)

    def test_annotation_has_official_page_label(self):
        anns, _ = self.client.list_annotations("ATT00001")
        ann = anns[0]
        self.assertTrue(ann.page_label)
        self.assertEqual(ann.page, ann.page_label)
        self.assertTrue(ann.color_name)


# --------------------------------------------------------------------------
# 4. children 默认漏批注，annotations 不漏（硬要求）
# --------------------------------------------------------------------------
class TestChildrenQuirk(unittest.TestCase):

    def setUp(self):
        self.server = mock_zotero.MockZotero().start()
        self.addCleanup(self.server.stop)
        self.client = rvzotero.ZoteroClient(api_base=self.server.api_base,
                                            library="users/0")

    def test_mock_reproduces_silent_zero(self):
        """裸 ``/children`` 返回 0 条批注且**不报错**——这是真实行为。"""
        children, resp = self.client.list_children("ATT00001")
        self.assertEqual(len(children), 0)
        self.assertEqual(resp.total_results, 0)

    def test_client_sends_item_type_annotation(self):
        """客户端必须自己带上 ``?itemType=annotation``。"""
        children, resp = self.client.list_children("ATT00001", item_type="annotation")
        self.assertTrue(children)
        self.assertEqual(resp.total_results, 130)

    def test_children_command_reports_annotation_count(self):
        rc, payload = run_cli(self.server, ["children", "--key", "ABCD1234"])
        self.assertEqual(rc, 0)
        self.assertEqual(payload["children"]["annotation"]["total"], 130)

    def test_children_warns_when_explicitly_capped(self):
        """显式传 ``--limit`` 命中单页上限时必须警告——静默截断是最大的敌人。

        默认已经翻完全部分页（无隐式上限），所以只有**用户自己要了上限**时才有话要说。
        """
        rc, payload = run_cli(self.server,
                              ["children", "--key", "ABCD1234", "--limit", "100"])
        self.assertEqual(rc, 0)
        self.assertIn("warning", payload)
        self.assertIn("annotations", payload["warning"])

    def test_children_default_takes_everything(self):
        """不传 ``--limit`` 时取全量，不应再出现上限警告。"""
        rc, payload = run_cli(self.server, ["children", "--key", "ABCD1234"])
        self.assertEqual(rc, 0)
        self.assertNotIn("warning", payload)
        self.assertEqual(payload["children"]["attachment"]["total"], 2)
        self.assertEqual(payload["children"]["annotation"]["total"], 130)


# --------------------------------------------------------------------------
# 5. 附件路径解析
# --------------------------------------------------------------------------
class TestAttachmentPath(unittest.TestCase):

    def test_storage_dir_from_env(self):
        old = os.environ.get("RV_ZOTERO_STORAGE")
        try:
            os.environ["RV_ZOTERO_STORAGE"] = os.path.join(os.sep, "tmp", "storage")
            self.assertEqual(rvzotero.default_storage_dir(),
                             os.path.join(os.sep, "tmp", "storage"))
        finally:
            if old is None:
                os.environ.pop("RV_ZOTERO_STORAGE", None)
            else:
                os.environ["RV_ZOTERO_STORAGE"] = old

    def test_storage_dir_from_api_base_env(self):
        old = os.environ.get("RV_ZOTERO_DATA_DIR")
        try:
            os.environ["RV_ZOTERO_DATA_DIR"] = os.path.join(os.sep, "data")
            self.assertEqual(rvzotero.default_storage_dir(),
                             os.path.join(os.sep, "data", "storage"))
        finally:
            if old is None:
                os.environ.pop("RV_ZOTERO_DATA_DIR", None)
            else:
                os.environ["RV_ZOTERO_DATA_DIR"] = old

    def test_relative_link_mode_is_not_a_local_file(self):
        """linked_url / linked_file 不能当成磁盘路径。"""
        item = {"data": {"key": "ATT00009", "itemType": "attachment",
                         "linkMode": "linked_url", "filename": "x.pdf",
                         "contentType": "application/pdf"}}
        path, kind = rvzotero.resolve_attachment_path(item)
        self.assertEqual(kind, "linked_url")
        self.assertIsNone(path)

    def test_stored_attachment_path_shape(self):
        item = {"data": {"key": "ATT00001", "itemType": "attachment",
                         "linkMode": "imported_file", "filename": "paper.pdf",
                         "contentType": "application/pdf"}}
        path, kind = rvzotero.resolve_attachment_path(item, storage_dir=os.sep + "storage")
        self.assertEqual(kind, "stored")
        self.assertTrue(path.endswith(os.path.join("ATT00001", "paper.pdf")))

    def test_cli_attachment_reports_resolved_path_and_kind(self):
        """默认调用**会**解析并打印磁盘路径——旧名字声称「不泄露绝对路径」，名不副实。

        路径由 ``default_storage_dir()`` + 附件 key + filename 拼成，属本机运行时
        输出，不进仓库。这里断言的是「解析形状正确」与「文件不存在时不假装存在」。
        """
        server = mock_zotero.MockZotero().start()
        self.addCleanup(server.stop)
        rc, payload = run_cli(server, ["attachment", "--key", "ATT00001"])
        self.assertEqual(rc, 0)
        self.assertEqual(payload["pathKind"], "stored")
        self.assertEqual(
            payload["path"],
            os.path.join(payload["storageDir"], "ATT00001", payload["filename"]))
        self.assertTrue(os.path.isabs(payload["path"]))
        self.assertFalse(payload["exists"], "本机不该真的有这个 mock 附件文件")
        self.assertTrue(payload.get("note"))

    def test_cli_attachment_storage_override_changes_resolved_path(self):
        storage = os.path.join(os.sep, "custom", "storage")
        server = mock_zotero.MockZotero().start()
        self.addCleanup(server.stop)
        rc, payload = run_cli(
            server, ["attachment", "--key", "ATT00001", "--storage", storage])
        self.assertEqual(rc, 0)
        self.assertEqual(payload["storageDir"], storage)
        self.assertEqual(
            payload["path"], os.path.join(storage, "ATT00001", "placeholder-original.pdf"))

    def test_cli_attachment_all_lists_every_attachment(self):
        server = mock_zotero.MockZotero().start()
        self.addCleanup(server.stop)
        rc, payload = run_cli(server, ["attachment", "--key", "ABCD1234", "--all"])
        self.assertEqual(rc, 0)
        self.assertEqual(payload["attachmentCount"], 2)
        self.assertEqual(len(payload["attachments"]), 2)
        for block in payload["attachments"]:
            self.assertEqual(block["pathKind"], "stored")
            self.assertTrue(os.path.isabs(block["path"]))


class TestIncludePluralOnly(unittest.TestCase):
    """``--include`` 只认复数；帮助文本必须和实现对得上。

    回归来源：``parse_include`` 只接受 ``annotations/attachments/notes``，但
    ``children --help`` 一度印的是单数 ``attachment,note,annotation``，
    照帮助文本敲会直接吃退出码 2。
    """

    def setUp(self):
        self.server = mock_zotero.MockZotero().start()
        self.addCleanup(self.server.stop)

    def test_singular_is_usage_error(self):
        for value in ("attachment,note,annotation",
                      "annotation", "note", "attachment"):
            rc, _ = run_cli(self.server, ["children", "--key", "ABCD1234",
                                          "--include", value])
            self.assertEqual(rc, 2, "--include %r 应报参数错" % value)

    def test_plural_is_accepted(self):
        for value in ("attachments,notes,annotations",
                      "annotations", "notes", "attachments"):
            rc, payload = run_cli(self.server, ["children", "--key", "ABCD1234",
                                                "--include", value])
            self.assertEqual(rc, 0, "--include %r 应可用" % value)
            self.assertTrue(payload["children"])

    def test_singular_error_suggests_plural(self):
        """报错要直接给出改法，而不是只说「不允许」。"""
        rc, _, stderr = run_cli_raw(
            ["--api", self.server.api_base, "children",
             "--key", "ABCD1234", "--include", "annotation"])
        self.assertEqual(rc, 2)
        self.assertIn("annotations", stderr)

    def test_help_text_documents_plural_not_singular(self):
        """帮助文本里 ``--include`` 那一行必须写复数，不能漂回单数。"""
        import contextlib
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            with self.assertRaises(SystemExit):
                rvzotero.main(["children", "--help"])
        text = buffer.getvalue()
        include_lines = [ln for ln in text.splitlines() if "--include" in ln]
        self.assertTrue(include_lines, "帮助里应出现 --include")
        joined = " ".join(include_lines) + " " + text
        for plural in ("annotations", "attachments", "notes"):
            self.assertIn(plural, joined)
        # 单数只允许出现在 --item-type 的说明里，不允许出现在 --include 的说明里。
        include_help = text.split("--include", 1)[1].split("--limit", 1)[0]
        self.assertNotIn("attachment,note,annotation", include_help)

    def test_parse_include_unit(self):
        self.assertEqual(rvzotero.parse_include("annotations,notes"),
                         {"annotations", "notes"})
        self.assertEqual(rvzotero.parse_include(""), set())
        self.assertEqual(rvzotero.parse_include("  NOTES "), {"notes"})
        with self.assertRaises(rvzotero.UsageError):
            rvzotero.parse_include("annotation")
        with self.assertRaises(rvzotero.UsageError):
            rvzotero.parse_include("bogus")


class TestGlobalFlagsBeforeSubcommand(unittest.TestCase):
    """写在子命令**前面**的全局开关不能被 argparse 的默认值抹掉。

    回归来源：argparse 会把子命令解析出的 namespace 整体覆盖回父 namespace，
    子命令里 `--human` 若带 `default=False`，`rvzotero --human ping` 会照样
    输出 JSON。修法是给子命令级的 `--json`/`--human` 用 ``default=SUPPRESS``。
    """

    def setUp(self):
        self.server = mock_zotero.MockZotero().start()
        self.addCleanup(self.server.stop)

    def test_human_before_subcommand_takes_effect(self):
        rc, _, stdout = run_cli_raw(
            ["--api", self.server.api_base, "--human", "ping"])
        self.assertEqual(rc, 0)
        self.assertNotIn("{", stdout, "前置 --human 必须真的切到人类可读输出")

    def test_human_after_subcommand_still_works(self):
        rc, _, stdout = run_cli_raw(
            ["--api", self.server.api_base, "ping", "--human"])
        self.assertEqual(rc, 0)
        self.assertNotIn("{", stdout)

    def test_json_before_subcommand(self):
        rc, payload, _ = run_cli_raw(
            ["--api", self.server.api_base, "--json", "ping"])
        self.assertEqual(rc, 0)
        self.assertIsInstance(payload, dict)

    def test_json_after_subcommand(self):
        rc, payload, _ = run_cli_raw(
            ["--api", self.server.api_base, "ping", "--json"])
        self.assertEqual(rc, 0)
        self.assertIsInstance(payload, dict)

    def test_human_and_json_together_is_usage_error(self):
        rc, _, stderr = run_cli_raw(
            ["--api", self.server.api_base, "--human", "--json", "ping"])
        self.assertEqual(rc, 2)
        self.assertIn("--human", stderr)

    def test_default_is_json(self):
        rc, payload, _ = run_cli_raw(["--api", self.server.api_base, "ping"])
        self.assertEqual(rc, 0)
        self.assertIsInstance(payload, dict)

    def test_human_before_subcommand_with_real_command(self):
        """不只是 ping —— 带上子命令参数也要生效。"""
        rc, _, stdout = run_cli_raw(
            ["--api", self.server.api_base, "--human",
             "annotations", "--key", "ABCD1234", "--limit", "2"])
        self.assertEqual(rc, 0)
        self.assertNotIn('"annotations"', stdout)


# --------------------------------------------------------------------------
# 6. 连不上 Zotero → 退出码 3 + 可执行的修复指引（硬要求）
# --------------------------------------------------------------------------
class TestConnectionFailure(unittest.TestCase):

    def test_exit_code_3_and_actionable_hint(self):
        # 端口 1 基本不可能是 Zotero；立刻拒绝连接。
        rc, payload, stderr = run_cli_raw(
            ["--api", "http://127.0.0.1:1/api", "ping"])
        self.assertEqual(rc, 3)
        self.assertIn("Zotero", stderr)
        # 「可执行的修复」= 必须出现可照做的动作词，而不是一句「失败了」。
        for hint in ("启动", "设置", "23119"):
            self.assertIn(hint, stderr, "修复指引里应出现 %r" % hint)

    def test_hint_mentions_allow_other_applications(self):
        self.assertIn("允许其他应用", rvzotero.CONNECTION_HINT)

    def test_connection_error_is_typed(self):
        self.assertEqual(rvzotero.ConnectionFailure.exit_code, 3)
        self.assertEqual(rvzotero.UsageError.exit_code, 2)
        self.assertEqual(rvzotero.ApiError.exit_code, 4)
        self.assertEqual(rvzotero.NotFound.exit_code, 5)


# --------------------------------------------------------------------------
# 7. 其它：退出码、默认 JSON、页码估算标记、导出
# --------------------------------------------------------------------------
class TestExitCodesAndOutput(unittest.TestCase):

    def setUp(self):
        self.server = mock_zotero.MockZotero().start()
        self.addCleanup(self.server.stop)

    def test_not_found_is_5(self):
        rc, _ = run_cli(self.server, ["get", "--key", "ZZZZZZZZ"])
        self.assertEqual(rc, 5)

    def test_usage_error_is_2(self):
        rc, _ = run_cli(self.server, ["get"])
        self.assertEqual(rc, 2)

    def test_bad_color_is_2_not_silent_zero(self):
        """无法识别的颜色必须**报参数错**，不能悄悄返回 0 条。"""
        rc, _ = run_cli(self.server, ["annotations", "--key", "ABCD1234",
                                      "--color", "not-a-color"])
        self.assertEqual(rc, 2)

    def test_unsupported_export_format_is_4(self):
        """``?format=citation`` 真实 API 回 400 —— 必须原样暴露为退出码 4。"""
        client = rvzotero.ZoteroClient(api_base=self.server.api_base, library="users/0")
        with self.assertRaises(rvzotero.ApiError) as ctx:
            client.export_raw("ABCD1234", "citation")
        self.assertEqual(ctx.exception.exit_code, 4)
        self.assertIn("citation", str(ctx.exception))

    def test_item_types_endpoint_is_404(self):
        client = rvzotero.ZoteroClient(api_base=self.server.api_base, library="users/0")
        with self.assertRaises(rvzotero.NotFound):
            client.get_json("/itemTypes")

    def test_json_is_default(self):
        rc, payload, _ = run_cli_raw(["--api", self.server.api_base, "ping"])
        self.assertEqual(rc, 0)
        self.assertIsInstance(payload, dict)

    def test_ping_reports_library_version(self):
        rc, payload = run_cli(self.server, ["ping"])
        self.assertEqual(rc, 0)
        self.assertEqual(payload["library"], "users/0")
        self.assertIn("last_modified_version", payload)

    def test_fulltext_page_param_is_ignored_by_server(self):
        """回归：``?page=N`` 被服务端忽略，传任何页都拿到整篇。"""
        client = rvzotero.ZoteroClient(api_base=self.server.api_base, library="users/0")
        whole = client.fulltext("ATT00001")["content"]
        for page in (1, 2, 27):
            self.assertEqual(client.fulltext("ATT00001", page=page)["content"], whole)

    def test_fulltext_parent_key_is_404(self):
        client = rvzotero.ZoteroClient(api_base=self.server.api_base, library="users/0")
        with self.assertRaises(rvzotero.NotFound):
            client.fulltext("ATT00002")   # 有附件但没有索引全文

    def test_retrieve_marks_pages_as_estimated(self):
        """**证据纪律**：估算页码必须自曝身份，不能像官方页码标签一样权威。"""
        rc, payload = run_cli(self.server, ["retrieve", "--key", "ATT00001",
                                            "--query", "benchmarks", "--passages", "2"])
        self.assertEqual(rc, 0)
        self.assertTrue(payload["results"])
        for row in payload["results"]:
            self.assertTrue(row["pageEstimated"])
            self.assertEqual(row["pageSource"], "char_offset_estimate")
        self.assertIn("估算", payload["note"])

    def test_retrieve_makes_single_fulltext_request(self):
        """只取一次全文——逐页请求等于把同一篇下载 N 遍。"""
        rc, payload = run_cli(self.server, ["retrieve", "--key", "ATT00001",
                                            "--query", "benchmarks"])
        self.assertEqual(rc, 0)
        self.assertNotIn("fetchedPages", payload)
        self.assertEqual(payload["chars"], len(self.server.fixture["fulltext"]["ATT00001"]))

    def test_fulltext_local_slice_is_labelled(self):
        rc, payload = run_cli(self.server, ["fulltext", "--key", "ATT00001",
                                            "--pages", "2-3"])
        self.assertEqual(rc, 0)
        self.assertTrue(payload["pageEstimated"])
        self.assertEqual(payload["pageSource"], "local_char_offset_slice")
        self.assertEqual(payload["requestedPages"], "2-3")
        whole = self.server.fixture["fulltext"]["ATT00001"]
        self.assertLess(len(payload["content"]), len(whole))
        self.assertIn("本地", payload["note"])

    def test_fulltext_unlabelled_when_whole(self):
        rc, payload = run_cli(self.server, ["fulltext", "--key", "ATT00001"])
        self.assertEqual(rc, 0)
        self.assertFalse(payload["pageEstimated"])
        self.assertEqual(payload["pageSource"], "zotero_fulltext_index")

    def test_bad_page_range_is_2(self):
        rc, _ = run_cli(self.server, ["fulltext", "--key", "ATT00001", "--pages", "x-y"])
        self.assertEqual(rc, 2)

    def test_annotations_report_truncation(self):
        """``返回的比存在的少`` 必须显式说出来。"""
        rc, payload = run_cli(self.server, ["annotations", "--key", "ABCD1234",
                                            "--limit", "10"])
        self.assertEqual(rc, 0)
        self.assertEqual(payload["total"], 10)
        self.assertEqual(payload["matchedTotal"], 130)
        self.assertTrue(payload["truncated"])
        self.assertIn("note", payload)

    def test_annotations_all_not_truncated(self):
        rc, payload = run_cli(self.server, ["annotations", "--key", "ABCD1234", "--all"])
        self.assertEqual(rc, 0)
        self.assertEqual(payload["total"], 130)
        self.assertFalse(payload["truncated"])

    def test_human_output_has_no_json_braces(self):
        rc, payload, stdout = run_cli_raw(
            ["--human", "--api", self.server.api_base, "ping"])
        self.assertEqual(rc, 0)
        self.assertNotIn("{", stdout)

    def test_period_helper_does_not_double(self):
        self.assertEqual(rvzotero._period("n.d."), "n.d.")
        self.assertEqual(rvzotero._period("2023"), "2023.")
        self.assertEqual(rvzotero._period(""), "")
        self.assertEqual(rvzotero._period(None), "")

    def test_undated_item_has_no_double_period(self):
        """``n.d.`` 自带句点，不能再补 —— 无日期条目是常见路径，不是边角。"""
        for style in ("apa", "ieee", "gb-t-7714"):
            citation = rvzotero.format_citation(
                {"data": {"itemType": "journalArticle", "title": "Untitled Draft",
                          "creators": [{"creatorType": "author", "lastName": "Doe",
                                        "firstName": "Jane"}]}}, style)
            self.assertNotIn("..", citation, "%s: %s" % (style, citation))

    def test_ieee_creators_do_not_crash(self):
        """回归：``"%s %s" % (a, b).strip()`` 会对元组取 strip → AttributeError。"""
        for style in ("ieee", "gb-t-7714", "apa"):
            citation = rvzotero.format_citation(
                {"data": {"itemType": "journalArticle", "title": "T",
                          "date": "2023",
                          "creators": [{"creatorType": "author", "lastName": "Doe",
                                        "firstName": "Jane"}]}}, style)
            self.assertTrue(citation)

    def test_export_citation_local_fallback(self):
        rc, payload = run_cli(self.server, ["export", "--key", "ABCD1234",
                                            "--format", "citation"])
        self.assertEqual(rc, 0)
        citation = payload["citations"][0]["citation"]
        self.assertIn("2023", citation)
        self.assertNotIn("((", citation)   # 回归：_year 曾返回带括号的 (n.d.)

    def test_citation_has_no_double_period(self):
        """回归：姓名缩写自带句点，作者串后不能再补一个 → ``A..``。"""
        rc, payload = run_cli(self.server, ["export", "--key", "ABCD1234",
                                            "--format", "citation"])
        self.assertEqual(rc, 0)
        citation = payload["citations"][0]["citation"]
        self.assertNotIn("..", citation, "不应出现连续两个句点：%s" % citation)

    def test_ieee_citation_shape(self):
        rc, payload = run_cli(self.server, ["export", "--key", "ABCD1234",
                                            "--format", "citation", "--style", "ieee"])
        self.assertEqual(rc, 0)
        citation = payload["citations"][0]["citation"]
        self.assertIn("2023", citation)
        self.assertNotIn("..", citation)

    def test_fulltext_slice_marks_content_as_partial(self):
        """切片时 ``contentIsWholeDocument`` 必须是 False——不能让人误以为拿到了整篇。"""
        rc, payload = run_cli(self.server, ["fulltext", "--key", "ATT00001",
                                            "--pages", "2-3"])
        self.assertEqual(rc, 0)
        self.assertFalse(payload["contentIsWholeDocument"])
        self.assertTrue(payload["fetchedWholeDocument"])

    def test_fulltext_whole_marks_content_as_whole(self):
        rc, payload = run_cli(self.server, ["fulltext", "--key", "ATT00001"])
        self.assertEqual(rc, 0)
        self.assertTrue(payload["contentIsWholeDocument"])

    def test_collections_and_tags(self):
        rc, payload = run_cli(self.server, ["collections"])
        self.assertEqual(rc, 0)
        self.assertEqual(payload["total"], 2)
        rc, payload = run_cli(self.server, ["tags"])
        self.assertEqual(rc, 0)
        self.assertEqual(payload["total"], 3)


# --------------------------------------------------------------------------
# 8. 纯函数：页码、片段、颜色、转义
# --------------------------------------------------------------------------
class TestPositionalKeyShim(unittest.TestCase):
    """`annotations ABCD1234` 这种位置参数写法（README 里就是这么演示的）。

    回归点：旧实现取「第一个不以 - 开头的 token」当子命令，于是
    ``--api <url> annotations ABCD1234`` 会把 **`--api` 的值**当成子命令，
    容错静默失效 —— 偏偏所有真实调用都带 `--api`/`--library`。
    """

    @staticmethod
    def _key_commands():
        """从 parser 现取「有 --key 的子命令」，不硬编码。"""
        parser = rvzotero.build_parser()
        out = []
        for name, sub in rvzotero._subparsers(parser).items():
            if any(a.dest == "key" for a in sub._actions):
                out.append(name)
        return out

    def test_shim_covers_every_subcommand_with_key(self):
        names = self._key_commands()
        self.assertIn("annotations", names)
        self.assertIn("export", names)   # 旧硬编码列表漏掉的正是 export
        for name in names:
            argv = rvzotero.normalize_argv([name, "ABCD1234"])
            self.assertIn("--key", argv, name)
            self.assertIn("ABCD1234", argv, name)

    def test_shim_skips_value_of_global_option(self):
        """`--api <url>` 的值不能被当成子命令。"""
        argv = ["--api", "http://127.0.0.1:23119/api", "annotations", "ABCD1234"]
        self.assertIn("--key", rvzotero.normalize_argv(argv))
        argv = ["--library", "users/0", "get", "ABCD1234"]
        self.assertIn("--key", rvzotero.normalize_argv(argv))
        argv = ["--timeout", "30", "export", "ABCD1234", "--format", "bibtex"]
        self.assertIn("--key", rvzotero.normalize_argv(argv))

    def test_shim_is_order_independent(self):
        """`--key` 必须补在末尾，所以位置参数写在选项前后都成立。"""
        for argv in (["annotations", "ABCD1234", "--color", "purple"],
                     ["annotations", "--color", "purple", "ABCD1234"]):
            normalized = rvzotero.normalize_argv(argv)
            self.assertEqual(normalized[-2:], ["--key", "ABCD1234"], argv)
            self.assertNotIn("ABCD1234", normalized[:-2], argv)

    def test_shim_does_not_touch_explicit_key(self):
        argv = ["annotations", "--key", "ABCD1234"]
        self.assertEqual(rvzotero.normalize_argv(argv), argv)
        argv = ["annotations", "--key=ABCD1234"]
        self.assertEqual(rvzotero.normalize_argv(argv), argv)

    def test_shim_leaves_keyless_and_flagless_calls_alone(self):
        self.assertEqual(rvzotero.normalize_argv(["ping"]), ["ping"])
        self.assertEqual(rvzotero.normalize_argv(["annotations", "--all"]),
                         ["annotations", "--all"])
        self.assertEqual(rvzotero.normalize_argv(["annotations", "--help"]),
                         ["annotations", "--help"])

    def test_positional_form_works_end_to_end(self):
        with mock_zotero.MockZotero() as server:
            explicit = run_cli(server, ["annotations", "--key", "ABCD1234"])
            positional = run_cli(server, ["annotations", "ABCD1234"])
            self.assertEqual(explicit[0], 0)
            self.assertEqual(positional[0], 0)
            self.assertEqual(explicit[1]["total"], positional[1]["total"])

    def test_positional_form_works_with_global_api_flag(self):
        """真实调用几乎都带 `--api`，这条是上一个回归的直击。"""
        with mock_zotero.MockZotero() as server:
            code, payload, _ = run_cli_raw(
                ["--api", server.api_base, "annotations", "ABCD1234"])
            self.assertEqual(code, 0)
            self.assertEqual(payload["total"], 130)

    def test_export_positional_form_no_longer_errors(self):
        """docs-author 实测 `export ABC12345 --format bibtex` 曾 rc=2。"""
        with mock_zotero.MockZotero() as server:
            code, payload = run_cli(server, ["export", "ABCD1234", "--format", "bibtex"])
            self.assertEqual(code, 0)
            self.assertTrue(payload["text"].strip())

    def test_positional_form_works_with_global_api_flag(self):
        """真实调用几乎都带 `--api`，这条是上一个回归的直击。"""
        with mock_zotero.MockZotero() as server:
            explicit = run_cli_raw(
                ["--api", server.api_base, "annotations", "--key", "ABCD1234"])
            positional = run_cli_raw(
                ["--api", server.api_base, "annotations", "ABCD1234"])
            self.assertEqual(positional[0], 0)
            self.assertIsNotNone(positional[1])
            self.assertEqual(positional[1]["total"], explicit[1]["total"])
            self.assertEqual(positional[1]["matchedTotal"], 130)


class TestChangesSnapshot(unittest.TestCase):
    """`changes --db <文件>` 的快照/基线两段式（文档里一律带文件名）。"""

    def test_baseline_then_diff_reports_deletions(self):
        with mock_zotero.MockZotero() as server:
            with tempfile.TemporaryDirectory() as tmp:
                db = os.path.join(tmp, "snap.json")
                code, first = run_cli(server, ["changes", "--db", db])
                self.assertEqual(code, 0)
                self.assertEqual(first["mode"], "baseline")
                self.assertTrue(os.path.exists(db))
                code, second = run_cli(server, ["changes", "--db", db])
                self.assertEqual(code, 0)
                self.assertIn("deleted", second)

    def test_db_requires_a_filename(self):
        with mock_zotero.MockZotero() as server:
            code, _, err = run_cli_raw(
                ["--api", server.api_base, "changes", "--db"])
            self.assertEqual(code, 2)
            self.assertIn("--db", err)


class TestAnnotationHelpMatchesBehaviour(unittest.TestCase):
    """docs-author 实测：`--help` 曾写「--all 取全部（默认已是全部）」，
    但默认 limit=100，130 条只给 100 条 —— 帮助文本在教用户踩坑。
    """

    def test_help_does_not_claim_default_is_all(self):
        parser = rvzotero.build_parser()
        sub = rvzotero._subparsers(parser)["annotations"]
        help_text = sub.format_help()
        self.assertNotIn("默认已是全部", help_text)
        self.assertIn("--all", help_text)

    def test_default_is_all_not_truncated(self):
        """默认就是全量：批注是证据层本身，最大的坑不能留在默认路径上。"""
        with mock_zotero.MockZotero() as server:
            _, default = run_cli(server, ["annotations", "--key", "ABCD1234"])
            self.assertEqual(default["total"], 130)
            self.assertEqual(default["matchedTotal"], 130)
            self.assertFalse(default["truncated"])
            self.assertEqual(default.get("note", ""), "")

    def test_all_is_an_explicit_no_op(self):
        """``--all`` 仍可用，且结果与默认完全一致（显式无操作）。"""
        with mock_zotero.MockZotero() as server:
            _, default = run_cli(server, ["annotations", "--key", "ABCD1234"])
            _, full = run_cli(server, ["annotations", "--key", "ABCD1234", "--all"])
            self.assertEqual(full["total"], 130)
            self.assertFalse(full["truncated"])
            self.assertEqual(len(full["annotations"]), len(default["annotations"]))

    def test_explicit_limit_truncates_and_says_so(self):
        """``--limit N`` 是**显式**上限，此时必须如实报出「返回的比存在的少」。"""
        with mock_zotero.MockZotero() as server:
            _, limited = run_cli(server,
                                 ["annotations", "--key", "ABCD1234", "--limit", "40"])
            self.assertEqual(limited["total"], 40)
            self.assertEqual(limited["matchedTotal"], 130)
            self.assertTrue(limited["truncated"])
            self.assertIn("--limit", limited["note"])
            self.assertIn("130", limited["note"])


class TestStructuralReadsAreFullByDefault(unittest.TestCase):
    """结构性读取默认全量；只有检索型保留条数上限。

    判据：列**全部**子项 / 全部集合 / 全部标签默认就该是全部——少给是丢数据；
    ``search`` / ``retrieve`` 默认有上限——那里「少给」是功能。
    这里用 >100 的假数据证明客户端**真的翻完了分页**，而不是只看首页。
    """

    @staticmethod
    def _big_fixture():
        fx = mock_zotero.make_fixture()
        fx["tags"] = [{"tag": "tag-%03d" % i, "links": {}, "meta": {}}
                      for i in range(105)]
        fx["searches"] = [{"key": "SRCH%04d" % i, "version": 9,
                           "data": {"key": "SRCH%04d" % i, "version": 9,
                                    "name": "Saved search %03d" % i}}
                          for i in range(105)]
        return fx

    def setUp(self):
        self.server = mock_zotero.MockZotero(fixture=self._big_fixture()).start()
        self.addCleanup(self.server.stop)

    def test_tags_default_paginates_past_100(self):
        rc, payload = run_cli(self.server, ["tags"])
        self.assertEqual(rc, 0)
        self.assertEqual(payload["total"], 105)
        self.assertEqual(payload["scanned"], 105)
        self.assertEqual(payload["pages"], 2)
        self.assertEqual(payload["count"], 105)
        self.assertFalse(payload["truncated"])

    def test_tags_query_filters_over_every_page(self):
        """命中的标签落在第 2 页——只在首页里找会得到**假阴性**。"""
        rc, payload = run_cli(self.server, ["tags", "--query", "tag-104"])
        self.assertEqual(rc, 0)
        self.assertEqual(payload["matchedTotal"], 1)
        self.assertEqual(payload["tags"], ["tag-104"])

    def test_tags_explicit_limit_truncates_and_says_so(self):
        rc, payload = run_cli(self.server, ["tags", "--limit", "5"])
        self.assertEqual(rc, 0)
        self.assertEqual(len(payload["tags"]), 5)
        self.assertEqual(payload["matchedTotal"], 105)
        self.assertTrue(payload["truncated"])
        self.assertIn("--limit", payload["note"])

    def test_searches_default_paginates_past_100(self):
        rc, payload = run_cli(self.server, ["searches"])
        self.assertEqual(rc, 0)
        self.assertEqual(payload["total"], 105)
        self.assertEqual(len(payload["searches"]), 105)

    def test_collections_default_is_full(self):
        rc, payload = run_cli(self.server, ["collections"])
        self.assertEqual(rc, 0)
        self.assertEqual(payload["total"], 2)

    def test_search_keeps_its_default_cap(self):
        """检索型保留默认上限——这是刻意的，不要「顺手统一」。"""
        parser = rvzotero.build_parser()
        sub = rvzotero._subparsers(parser)["search"]
        limit_action = [a for a in sub._actions if a.dest == "limit"][0]
        self.assertEqual(limit_action.default, 25)


class TestPureHelpers(unittest.TestCase):

    def test_parse_page_range(self):
        self.assertEqual(rvzotero.parse_page_range("5"), (5, 5))
        self.assertEqual(rvzotero.parse_page_range("3-7"), (3, 7))
        self.assertEqual(rvzotero.parse_page_range("7-3"), (3, 7))
        self.assertEqual(rvzotero.parse_page_range("3-7", total_pages=5), (3, 5))

    def test_parse_page_range_rejects_junk(self):
        for bad in ("abc", "", "1-2-3", "-5"):
            with self.assertRaises(rvzotero.UsageError):
                rvzotero.parse_page_range(bad)

    def test_estimate_page_clamps_to_total(self):
        meta = {"chars_per_page_estimate": 100.0, "total_pages": 3}
        self.assertEqual(rvzotero.estimate_page(0, meta), 1)
        self.assertEqual(rvzotero.estimate_page(150, meta), 2)
        self.assertEqual(rvzotero.estimate_page(10 ** 6, meta), 3)

    def test_estimate_page_without_meta(self):
        self.assertIsNone(rvzotero.estimate_page(50, {}))

    def test_split_passages_offsets_are_monotonic(self):
        text = "\n\n".join("Block %d. %s" % (i, "word " * 40) for i in range(12))
        rows = rvzotero.split_passages_with_offsets(text)
        self.assertTrue(rows)
        offsets = [off for off, _ in rows]
        self.assertEqual(offsets, sorted(offsets))
        for off, chunk in rows:
            self.assertEqual(text[off:off + len(chunk)].strip(), chunk.strip())

    def test_split_passages_empty(self):
        self.assertEqual(rvzotero.split_passages(""), [])
        self.assertEqual(rvzotero.split_passages_with_offsets(""), [])

    def test_slice_by_page(self):
        self.assertEqual(rvzotero.slice_by_page("abcdefghij", 5, 1, 1), "abcde")
        self.assertEqual(rvzotero.slice_by_page("abcdefghij", 5, 2, 2), "fghij")
        self.assertEqual(rvzotero.slice_by_page("abc", 0, 1, 2), "abc")

    def test_normalize_color_names_and_hex(self):
        self.assertEqual(rvzotero.normalize_color("purple"), "purple")
        self.assertEqual(rvzotero.normalize_color("#A28AE5"), "purple")
        self.assertEqual(rvzotero.normalize_color("A28AE5"), "purple")
        self.assertIsNone(rvzotero.normalize_color(None))

    def test_normalize_color_strict_raises(self):
        with self.assertRaises(rvzotero.UsageError):
            rvzotero.normalize_color("chartreuse", strict=True)

    def test_display_width_counts_cjk_as_two(self):
        self.assertEqual(rvzotero.display_width("ab"), 2)
        self.assertEqual(rvzotero.display_width("\u4e2d\u6587"), 4)

    def test_json_output_keeps_cjk_readable(self):
        buffer = io.StringIO()
        rvzotero.emit({"t": "\u4e2d\u6587"}, True, stream=buffer)
        self.assertIn("\u4e2d\u6587", buffer.getvalue())
        self.assertNotIn("\\u4e2d", buffer.getvalue())


class TestPassageSplitterNeverDropsSilently(unittest.TestCase):
    """回归：`min_chars` 过滤曾经是一条**静默丢弃**路径。

    旧实现 ``if len(out) <= 3: return out`` 之后直接
    ``[(off, c) for off, c in out if len(c) >= min_chars]``——切出 >3 段时把所有
    短于 60 字符的段整块扔掉，**一个字都不报**。中文尤其致命：中文一个字就是一个
    词，60 字符的门槛会把完全正常的段落判成碎片。

    现有 2 个 split 测试恰好都落在 ``len(out) <= 3`` 的直通分支上，所以这条路径
    一直没被覆盖——这正是漏网原因。本类专门锁死「合并 / 过滤」分支。
    """

    # verifier 合成的那类文本：798 字中文，句句很短，切出来全部 < 60 字符。
    CJK_SHORT = "".join(
        "%d、这是第%d个短句。" % (i, i) for i in range(1, 61))

    def test_verifier_short_cjk_case_is_not_dropped(self):
        text = self.CJK_SHORT
        self.assertGreater(len(text), 600)
        pieces, stats = rvzotero.split_passages_report(text)
        self.assertGreater(len(pieces), 0, "798 字中文被切成了 0 段——静默丢弃回来了")
        self.assertGreater(stats["keptChars"], 0)
        # 内容几乎全部保住（只允许丢掉空白）
        self.assertGreater(stats["keptChars"], len(text) * 0.9)

    def test_nonempty_text_never_yields_zero_kept_chars(self):
        """硬不变量：任何非空 text 处理后 keptChars 必须 > 0。"""
        samples = [
            self.CJK_SHORT,
            "x",                                   # 单字符
            "短",                                   # 单个汉字
            "。",                                   # 只有标点（无内容字符）→ 必须走兜底
            "-----\n-----\n-----",                  # 只有排版符号 → 兜底
            "One two three.",
            "\n\n\n",                               # 只有空白 → 这是「确实没有内容」
            "NoTerminatorAtAllJustOneVeryLongRunOfWords " * 40,
            "中文没有句号但很长" * 100,
            "Mixed 中英 mixed 内容 interspersed 混杂 " * 30,
        ]
        for text in samples:
            pieces, stats = rvzotero.split_passages_report(text)
            if not text.strip():
                self.assertEqual(pieces, [])
                continue
            self.assertGreater(
                stats["keptChars"], 0,
                "有内容却 0 片段（keptChars=0）：%r" % text[:40])

    def test_merge_branch_is_actually_exercised(self):
        """锁死分支：必须真的发生「原始片段 → 合并」的收敛，而不是走旧直通分支。"""
        pieces, stats = rvzotero.split_passages_report(self.CJK_SHORT)
        self.assertGreater(stats["rawPassages"], 3,
                           "样本太小，落回了旧的 len(out) <= 3 直通分支")
        self.assertLess(stats["mergedPassages"], stats["rawPassages"],
                        "合并分支没有执行——短片段没有被并起来")
        self.assertGreater(len(pieces), 0)

    def test_filter_branch_is_actually_exercised(self):
        """锁死分支：纯排版符号段被丢弃并且**记了账**。

        构造要点：排版垃圾段必须**排在最后**——短片段优先向后合并，夹在中间的
        分隔线会被并进正文，只有末尾那段没有「后」可并，才会真正落到过滤分支。
        """
        text = ("Paragraph one carries enough words to clear the sixty char bar.\n\n"
                "Paragraph two carries enough words to clear the sixty char bar.\n\n"
                "------------------------------------------\n")
        pieces, stats = rvzotero.split_passages_report(text)
        self.assertGreater(len(pieces), 0)
        self.assertGreater(stats["droppedPassages"], 0, "过滤分支没有执行")
        self.assertGreater(stats["droppedChars"], 0)
        self.assertEqual(stats["fallbackApplied"], False)
        for _, chunk in pieces:
            self.assertTrue(rvzotero._CONTENT_RE.search(chunk))

    def test_punctuation_only_document_falls_back_to_not_dropping(self):
        """整篇都没有内容字符时回退为不丢弃——绝不产出「有内容却 0 片段」。"""
        pieces, stats = rvzotero.split_passages_report("-----\n\n=====\n\n*****")
        self.assertGreater(len(pieces), 0)
        self.assertGreater(stats["keptChars"], 0)
        self.assertEqual(stats["droppedPassages"], 0)
        self.assertTrue(stats["fallbackApplied"])

    def test_cjk_threshold_is_lower_than_latin(self):
        self.assertEqual(
            rvzotero.passage_min_chars("这是一段中文"), rvzotero.PASSAGE_CJK_MIN_CHARS)
        self.assertEqual(
            rvzotero.passage_min_chars("this is english"),
            rvzotero.PASSAGE_MIN_CHARS)
        self.assertLess(rvzotero.PASSAGE_CJK_MIN_CHARS, rvzotero.PASSAGE_MIN_CHARS)
        self.assertTrue(rvzotero.is_cjk_heavy(self.CJK_SHORT))
        self.assertFalse(rvzotero.is_cjk_heavy("plain english text " * 20))

    def test_latin_short_paragraphs_survive_by_merging(self):
        text = "\n\n".join("Para %d." % i for i in range(20))   # 每段都 < 60 字符
        pieces, stats = rvzotero.split_passages_report(text)
        self.assertGreater(stats["rawPassages"], 3)
        self.assertGreater(len(pieces), 0)
        self.assertEqual(stats["droppedPassages"], 0)
        joined = "\n".join(chunk for _, chunk in pieces)
        for i in range(20):
            self.assertIn("Para %d." % i, joined, "有段落被静默丢掉了")

    def test_merged_pieces_respect_max_chars(self):
        text = "\n\n".join("短句 %d。" % i for i in range(80))
        pieces, _ = rvzotero.split_passages_report(text, max_chars=120)
        self.assertGreater(len(pieces), 0)
        for _, chunk in pieces:
            self.assertLessEqual(len(chunk), 120)

    def test_offsets_still_slice_the_source_exactly(self):
        """合并后的片段仍是源文本上的**连续切片**（偏移可核对，页码估算才站得住）。"""
        for text in (self.CJK_SHORT,
                     "\n\n".join("Para %d." % i for i in range(20)),
                     "Mixed 中英 mixed 内容 interspersed 混杂 " * 30):
            pieces, _ = rvzotero.split_passages_report(text)
            offsets = [off for off, _ in pieces]
            self.assertEqual(offsets, sorted(offsets))
            for off, chunk in pieces:
                self.assertEqual(text[off:off + len(chunk)], chunk)

    def test_empty_text_reports_zero_source_chars(self):
        pieces, stats = rvzotero.split_passages_report("")
        self.assertEqual(pieces, [])
        self.assertEqual(stats["sourceChars"], 0)
        self.assertEqual(stats["keptChars"], 0)

    def test_stats_keys_are_stable(self):
        """stats 的键是给下游如实报告用的契约，不能悄悄改名。"""
        _, stats = rvzotero.split_passages_report(self.CJK_SHORT)
        for key in ("sourceChars", "rawPassages", "mergedPassages", "passages",
                    "keptChars", "droppedPassages", "droppedChars",
                    "fallbackApplied", "cjkHeavy", "minCharsUsed"):
            self.assertIn(key, stats)


class TestRetrieveReportsWhatItDropped(unittest.TestCase):
    """`retrieve` 的输出层：0 片段必须说清成因，丢弃必须记账。"""

    def _fixture_with_text(self, text):
        fx = mock_zotero.make_fixture()
        fx["fulltext"]["ATT00001"] = text
        fx["fulltext_pages"]["ATT00001"] = 27
        return fx

    def test_retrieve_reports_pagination_and_drop_counters(self):
        text = "\n\n".join("第 %d 段，讲的是有效性与信度。" % i for i in range(40))
        with mock_zotero.MockZotero(self._fixture_with_text(text)) as server:
            code, payload = run_cli(
                server, ["retrieve", "--key", "ATT00001", "--query", "有效性与信度"])
            self.assertEqual(code, 0)
            for key in ("passageCount", "rawPassageCount", "mergedPassageCount",
                        "keptChars", "droppedPassages", "droppedChars",
                        "minCharsUsed", "cjkMinChars", "cjkHeavy", "passageNote"):
                self.assertIn(key, payload, "少了如实报告字段 %s" % key)
            self.assertGreater(payload["passageCount"], 0)
            self.assertGreater(payload["keptChars"], 0)
            self.assertTrue(payload["cjkHeavy"])
            self.assertEqual(payload["minCharsUsed"],
                             rvzotero.PASSAGE_CJK_MIN_CHARS)

    def test_empty_fulltext_warns_that_there_is_nothing_to_search(self):
        with mock_zotero.MockZotero(self._fixture_with_text("")) as server:
            code, payload = run_cli(
                server, ["retrieve", "--key", "ATT00001", "--query", "anything"])
            self.assertEqual(code, 0)
            self.assertEqual(payload["passageCount"], 0)
            self.assertIn("warning", payload)
            self.assertIn("空", payload["warning"])
            self.assertIn("没有可检索内容", payload["warning"])

    def test_no_match_is_distinguished_from_no_passages(self):
        """「确实没有匹配」与「切分后为空」是两回事，输出必须区分。"""
        text = "\n\n".join("第 %d 段，只谈完全无关的话题。" % i for i in range(30))
        with mock_zotero.MockZotero(self._fixture_with_text(text)) as server:
            code, payload = run_cli(
                server, ["retrieve", "--key", "ATT00001", "--query", "zzzzqqqq"])
            self.assertEqual(code, 0)
            self.assertGreater(payload["passageCount"], 0)
            self.assertEqual(payload["matched"], 0)
            self.assertIn("matchNote", payload)
            self.assertIn("确实没有", payload["matchNote"])

    def test_dropped_segments_are_reported_in_warning(self):
        text = ("Real content paragraph one carries plenty of words here.\n\n"
                "Real content paragraph two carries plenty of words here.\n\n"
                "------------------------------\n")
        with mock_zotero.MockZotero(self._fixture_with_text(text)) as server:
            code, payload = run_cli(
                server, ["retrieve", "--key", "ATT00001", "--query", "content"])
            self.assertEqual(code, 0)
            self.assertGreater(payload["droppedPassages"], 0)
            self.assertIn("warning", payload)
            self.assertIn("丢弃", payload["warning"])

    def test_whole_document_is_never_split_into_zero(self):
        """端到端：中文长文经 mock 全文进来，片段数必须 > 0（verifier 的原始现场）。"""
        text = TestPassageSplitterNeverDropsSilently.CJK_SHORT * 2
        with mock_zotero.MockZotero(self._fixture_with_text(text)) as server:
            code, payload = run_cli(
                server, ["retrieve", "--key", "ATT00001", "--query", "短句"])
            self.assertEqual(code, 0)
            self.assertGreater(payload["passageCount"], 0)
            self.assertGreater(payload["keptChars"], 0)
            self.assertGreater(payload["returned"], 0)


class TestMockMatchesRealApi(unittest.TestCase):
    """mock 的 children 语义必须与真机一致（详见 mock 顶部注释）。

    真机实测（Zotero 10.0.7）：条目 key + ``itemType=annotation`` → 130 条
    （= 附件 ATT00001 的 130 + 附件 ATT00002 的 0）；裸 ``/children`` → 0 条批注。
    """

    def test_item_level_annotation_filter_aggregates_across_attachments(self):
        with mock_zotero.MockZotero() as server:
            client = rvzotero.ZoteroClient(server.api_base, "users/0")
            rows, resp = client.list_children("ABCD1234", item_type="annotation")
            self.assertEqual(len(rows), 100, "单页上限 100，其余靠分页补齐")
            self.assertEqual(resp.total_results, 130)
            allrows, total, pages = client.list_children_all(
                "ABCD1234", item_type="annotation")
            self.assertEqual(len(allrows), 130)
            self.assertEqual(total, 130)
            self.assertEqual(pages, 2)
            keys = set(r["key"] for r in allrows)
            self.assertEqual(len(keys), 130, "条目级聚合出现了重复")

    def test_bare_children_returns_no_annotations(self):
        with mock_zotero.MockZotero() as server:
            client = rvzotero.ZoteroClient(server.api_base, "users/0")
            rows, _resp = client.list_children("ABCD1234")
            kinds = set(r["data"].get("itemType") for r in rows)
            self.assertNotIn("annotation", kinds)
            self.assertEqual(len(rows), 2)

    def test_attachment_level_filter_returns_its_own_annotations(self):
        with mock_zotero.MockZotero() as server:
            client = rvzotero.ZoteroClient(server.api_base, "users/0")
            rows, total, pages = client.list_children_all(
                "ATT00001", item_type="annotation")
            self.assertEqual(len(rows), 130)
            self.assertEqual(total, 130)
            self.assertEqual(pages, 2)
            empty, empty_total, _p = client.list_children_all(
                "ATT00002", item_type="annotation")
            self.assertEqual(empty, [])
            self.assertEqual(empty_total, 0)

    def test_bare_children_on_attachment_returns_nothing(self):
        """真机实测：附件 key 的裸 /children 回**空数组**，连批注都不给。"""
        with mock_zotero.MockZotero() as server:
            client = rvzotero.ZoteroClient(server.api_base, "users/0")
            rows, _resp = client.list_children("ATT00001")
            self.assertEqual(rows, [])

    def test_mock_pagination_header_is_authoritative(self):
        with mock_zotero.MockZotero() as server:
            client = rvzotero.ZoteroClient(server.api_base, "users/0")
            _rows, meta = client.list_annotations("ATT00001")
            self.assertEqual(meta["total"], 130)
            self.assertEqual(meta["scanned"], 130)


# --------------------------------------------------------------------------
# 辅助：在进程内跑 CLI（不起子进程，快）
# --------------------------------------------------------------------------
def run_cli_raw(argv, cwd=None):
    """跑一次 main()，返回 ``(exit_code, parsed_json_or_None, stderr_text)``。

    也会接住 ``SystemExit``：argparse 自己的参数错（例如 `--db` 后面忘写文件名）
    是直接 ``sys.exit(2)`` 的，不接住就会把异常漏进测试进程。
    """
    old_out, old_err = sys.stdout, sys.stderr
    out, err = io.StringIO(), io.StringIO()
    sys.stdout, sys.stderr = out, err
    try:
        code = rvzotero.main(list(argv))
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else (0 if exc.code is None else 2)
    finally:
        sys.stdout, sys.stderr = old_out, old_err
    text = out.getvalue()
    try:
        payload = json.loads(text)
    except ValueError:
        payload = None
    return code, payload, err.getvalue()


def run_cli(server, argv):
    code, payload, _ = run_cli_raw(["--api", server.api_base] + list(argv))
    return code, payload


if __name__ == "__main__":
    unittest.main(verbosity=2)
