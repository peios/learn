"""Regression and boundary tests; no network, builder, or third-party packages."""

from contextlib import redirect_stderr, redirect_stdout
from dataclasses import replace
import io
from pathlib import Path
import tempfile
import unittest

import check_rendered_links as checker


class RenderedLinksTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.baseline = self.root / "baseline"
        self.candidate = self.root / "candidate"
        for tree in (self.baseline, self.candidate):
            tree.mkdir()
            self.write(tree, "index.html", "<h1 id='home'>Home</h1>")

    def write(self, tree, name, contents):
        path = tree / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents, encoding="utf-8")
        return path

    def scan(self, body, name="index.html", **kwargs):
        self.write(self.candidate, name, body)
        return checker.scan(self.candidate, **kwargs)

    def comparison(self):
        return checker.Comparison(checker.scan(self.baseline), checker.scan(self.candidate))

    def cli(self, *args):
        output, error = io.StringIO(), io.StringIO()
        with redirect_stdout(output), redirect_stderr(error):
            status = checker.main([str(self.baseline), str(self.candidate), *args])
        return status, output.getvalue(), error.getvalue()

    def test_relative_root_and_directory_urls(self):
        self.write(self.candidate, "guide/index.html", "<h1 id='start'>Start</h1>")
        self.write(self.candidate, "guide/next.html", "Next")
        result = self.scan("""
            <a href='/'>root</a><a href='/guide'>directory</a>
            <a href='/guide/'>directory slash</a><a href='next.html'>file</a>
            <a href='./next.html'>dot</a><a href='../index.html'>parent</a>
            <a href='../guide/../guide/next.html'>normalized</a>
        """, "guide/current.html")
        self.assertEqual(result.broken, {})
        self.assertEqual(result.local_links, 7)

    def test_directory_without_index_and_missing_files(self):
        (self.candidate / "empty").mkdir()
        self.write(self.candidate, "assets/readme.txt", "file")
        result = self.scan("""
            <a href='/empty'>empty directory</a><a href='/absent.html'>missing</a>
            <a href='/assets/readme.txt#page=3'>non-HTML fragment</a>
        """)
        self.assertEqual(set(result.broken), {("index.html", "/empty"), ("index.html", "/absent.html")})
        self.assertTrue(all(reason == "missing file or directory index" for reason in result.reasons.values()))

    def test_anchors_percent_encoding_queries_and_entities(self):
        self.write(self.candidate, "hello world/index.html", "<h2 id='café & tea'>Tea</h2><a name='old'>Old</a>")
        result = self.scan("""
            <h1 id='here'>Here</h1><a href='#here'>local</a><a href='?q=one#here'>query</a>
            <a href=''>empty</a><a href>valueless</a><a href='#'>top</a>
            <a href='/hello%20world/?q=one&amp;x=two#caf%C3%A9%20%26%20tea'>encoded</a>
            <a href='/hello%20world#old'>legacy named anchor</a>
            <a href='#TOP'>browser top</a><a href='#:~:text=some%20text'>text directive</a>
            <a href='#here:~:text=some%20text'>anchor and text directive</a>
            <a href='#missing'>broken</a><a href='#HERE'>case sensitive</a>
        """)
        self.assertEqual(set(result.broken), {("index.html", "#missing"), ("index.html", "#HERE")})
        self.assertEqual(result.local_links, 12)

    def test_encoded_text_directive_delimiters_are_literal_ids(self):
        result = self.scan("""
            <h1 id='anchor'>Anchor</h1><p id='literal:~:text=present'>Literal</p>
            <a href='#anchor:~:text=missing'>real directive</a>
            <a href='#:~:text=missing'>real directive without anchor</a>
            <a href='#anchor%3A~%3Atext=missing'>missing literal ID</a>
            <a href='#%3A~%3Atext=missing'>missing literal ID without anchor</a>
            <a href='#literal%3A~%3Atext=present'>existing literal ID</a>
        """)
        self.assertEqual(set(result.broken), {
            ("index.html", "#anchor%3A~%3Atext=missing"),
            ("index.html", "#%3A~%3Atext=missing"),
        })

    def test_directory_request_cannot_resolve_to_a_regular_file(self):
        result = self.scan("""
            <a href='/index.html/'>trailing slash</a><a href='/index.html/.'>dot suffix</a>
            <a href='/index.html/next/..'>parent suffix</a>
        """)
        self.assertEqual(len(result.broken), 3)

    def test_all_schemes_and_protocol_relative_are_skipped(self):
        result = self.scan("""
            <a href='https://learn.peios.org/missing'>same-origin absolute</a>
            <a href='http://example.invalid/missing'>external</a><a href='//example.invalid/path'>relative host</a>
            <a href='mailto:user@example.invalid'>mail</a><a href='tel:123'>phone</a>
            <a href='data:text/plain,missing'>data</a><a href='javascript:void(0)'>script</a>
            <a href='file:///etc/passwd'>file</a><a href='custom:missing'>other scheme</a>
        """)
        self.assertEqual(result.broken, {})
        self.assertEqual(result.local_links, 0)

    def test_new_inherited_and_resolved_pairs(self):
        self.write(self.baseline, "index.html", "<a href='old'>old</a><a href='fixed'>fixed</a>")
        self.write(self.candidate, "index.html", "<a href='old'>old</a><a href='new'>new</a><a href='fixed'>fixed</a>")
        self.write(self.candidate, "fixed/index.html", "Fixed")
        comparison = self.comparison()
        self.assertEqual(comparison.new, {("index.html", "new")})
        self.assertEqual(comparison.inherited, {("index.html", "old")})
        self.assertEqual(comparison.resolved, {("index.html", "fixed")})

    def test_formerly_valid_pair_becoming_broken_is_new(self):
        for tree in (self.baseline, self.candidate):
            self.write(tree, "index.html", "<a href='/target#exists'>target</a>")
            self.write(tree, "target/index.html", "<h1 id='exists'>Target</h1>" if tree == self.baseline else "Target")
        self.assertEqual(self.comparison().new, {("index.html", "/target#exists")})

    def test_pair_identity_excludes_reason_and_duplicate_count(self):
        self.write(self.baseline, "index.html", "<a href='target#missing'>once</a>")
        self.write(self.candidate, "index.html", "<a href='target#missing'>twice</a>" * 2)
        self.write(self.candidate, "target/index.html", "Target without that fragment")
        comparison = self.comparison()
        pair = ("index.html", "target#missing")
        self.assertFalse(comparison.new)
        self.assertEqual(comparison.inherited, {pair})
        self.assertNotEqual(comparison.baseline.reasons[pair], comparison.candidate.reasons[pair])
        self.assertEqual(comparison.baseline.broken[pair], 1)
        self.assertEqual(comparison.candidate.broken[pair], 2)

    def test_same_href_on_new_page_is_a_new_pair(self):
        for tree in (self.baseline, self.candidate):
            self.write(tree, "index.html", "<a href='/missing'>missing</a>")
        self.write(self.candidate, "new/index.html", "<a href='/missing'>missing</a>")
        self.assertEqual(self.comparison().new, {("new/index.html", "/missing")})

    def test_malformed_and_unsafe_urls(self):
        hrefs = ["%", "%2", "%GG", "%FF", "/%00", "#%00", "#%GG", "../outside.html",
                 "/../../outside.html", "/%2e%2e/outside.html", "%2e%2e%2foutside.html",
                 "..\\outside.html", "%5coutside.html", "//[", "bad\npath", "\x7f"]
        for href in hrefs:
            with self.subTest(href=href), self.assertRaises(ValueError):
                checker.local_target("index.html", href)
        result = self.scan("<a href='/%2e%2e/outside.html'>escape</a><a href='//['>bad</a>")
        self.assertEqual(len(result.broken), 2)
        self.assertTrue(all(reason.startswith("malformed or unsafe URL") for reason in result.reasons.values()))

    def test_encoded_path_separators_never_validate_against_decoded_targets(self):
        self.write(self.candidate, "target.html", "Root target")
        # Only the root target exists: decoding first used to create a false pass.
        result = self.scan("<a href='%2Ftarget.html'>Target</a>", "nested/index.html")
        self.assertEqual(set(result.broken), {("nested/index.html", "%2Ftarget.html")})
        self.write(self.candidate, "nested/target.html", "Nested target")
        self.write(self.candidate, "nested/child/target.html", "Child target")
        hrefs = ("%2Ftarget.html", "%2ftarget.html", "%5Ctarget.html", "%5ctarget.html",
                 "child%2Ftarget.html", "child%2ftarget.html", "child%5Ctarget.html",
                 "child%5ctarget.html", "/nested%2Ftarget.html", "/nested%5ctarget.html")
        result = self.scan("".join(f"<a href='{href}'>Target</a>" for href in hrefs), "nested/index.html")
        self.assertEqual(set(result.broken), {("nested/index.html", href) for href in hrefs})
        self.assertTrue(all("encoded separator" in reason for reason in result.reasons.values()))

    def test_encoded_separators_remain_valid_in_fragment_ids(self):
        result = self.scan("""
            <h1 id='part/section'>Slash</h1><h2 id='part&#92;section'>Backslash</h2>
            <a href='#part%2Fsection'>Slash</a><a href='#part%2fsection'>Lowercase slash</a>
            <a href='#part%5Csection'>Backslash</a><a href='#part%5csection'>Lowercase backslash</a>
        """)
        self.assertFalse(result.broken)
        self.assertEqual(result.local_links, 4)

    def test_safe_encoded_parent_segment_stays_within_output(self):
        self.write(self.candidate, "other/index.html", "Other")
        result = self.scan("<a href='%2e%2e/other/'>Other</a>", "guide/index.html")
        self.assertFalse(result.broken)

    def test_href_to_existing_outside_file_never_resolves(self):
        self.write(self.root, "outside.html", "Outside")
        result = self.scan("<a href='../outside.html'>outside</a><a href='/%2e%2e/outside.html'>encoded</a>")
        self.assertEqual(len(result.broken), 2)

    def test_symlink_files_directories_and_root_rejected(self):
        outside = self.write(self.root, "outside/index.html", "Outside")
        for target, name in ((outside, "linked.html"), (outside.parent, "linked"),
                             (self.candidate / "index.html", "internal.html")):
            with self.subTest(name=name):
                link = self.candidate / name
                link.symlink_to(target, target_is_directory=target.is_dir())
                with self.assertRaisesRegex(checker.InputError, "symlink or special file"):
                    checker.scan(self.candidate)
                link.unlink()
        link = self.root / "linked-root"
        link.symlink_to(self.candidate, target_is_directory=True)
        with self.assertRaisesRegex(checker.InputError, "real directory"):
            checker.scan(link)

    def test_uppercase_html_htm_and_area_links(self):
        self.write(self.candidate, "target.HTM", "<p id='ok'>Target</p>")
        result = self.scan("<area href='target.HTM#ok'/><area href='target.HTM#missing'/><a>no href</a>")
        self.assertEqual(result.broken, {("index.html", "target.HTM#missing"): 1})

    def test_first_duplicate_attribute_wins(self):
        result = self.scan("<p id='first' id='second'></p><a href='#first' href='#second'>First</a>")
        self.assertFalse(result.broken)

    def test_base_urls_and_invalid_utf8_are_explicit_input_errors(self):
        with self.assertRaisesRegex(checker.InputError, "base URLs"):
            self.scan("<base href='https://example.invalid/'><a href='missing'>External</a>")
        (self.candidate / "index.html").write_bytes(b"\xff")
        with self.assertRaises(checker.InputError):
            checker.scan(self.candidate)

    def test_empty_or_missing_output_is_not_a_pass(self):
        (self.candidate / "index.html").unlink()
        with self.assertRaisesRegex(checker.InputError, "no HTML"):
            checker.scan(self.candidate)
        with self.assertRaisesRegex(checker.InputError, "real directory"):
            checker.scan(self.root / "nonexistent")

    def test_scan_resource_limits(self):
        self.write(self.candidate, "nested/page.html", "<a href='one'>One</a><a href='two'>Two</a>")
        for field, value, message in (
            ("entries", 1, "entry limit"), ("depth", 0, "directory-depth limit"),
            ("pages", 1, "page-count limit"), ("page_bytes", 1, "page size limit"),
            ("total_bytes", 1, "total HTML size limit"), ("links", 1, "navigation-link limit"),
            ("href_chars", 1, "href length limit"),
        ):
            with self.subTest(field=field), self.assertRaisesRegex(checker.InputError, message):
                checker.scan(self.candidate, replace(checker.Limits(), **{field: value}))

    def test_cli_status_zero_for_inherited_with_occurrence_counts(self):
        for tree, count in ((self.baseline, 1), (self.candidate, 3)):
            self.write(tree, "index.html", "<a href='missing'>Missing</a>" * count)
        status, output, error = self.cli()
        self.assertEqual(status, 0)
        self.assertIn("Inherited: 1 page/href pairs (3 occurrences)", output)
        self.assertIn("PASS: no newly broken", output)
        self.assertEqual(error, "")

    def test_cli_status_one_for_new_and_bounded_details(self):
        self.write(self.candidate, "index.html", "<a href='one'>One</a><a href='two'>Two</a>")
        status, output, error = self.cli("--max-details", "1")
        self.assertEqual(status, 1)
        self.assertIn("Newly broken: 2 page/href pairs (2 occurrences)", output)
        self.assertIn("1 additional pairs omitted", output)
        self.assertIn("FAIL: newly broken", output)
        self.assertEqual(error, "")

    def test_cli_status_two_for_invalid_output_and_arguments(self):
        (self.candidate / "index.html").unlink()
        status, output, error = self.cli()
        self.assertEqual(status, 2)
        self.assertEqual(output, "")
        self.assertIn("ERROR:", error)
        for value in ("-1", "1001", "no"):
            with self.subTest(value=value), self.assertRaises(SystemExit) as raised:
                self.cli("--max-details", value)
            self.assertEqual(raised.exception.code, 2)

    def test_report_escapes_untrusted_filenames_and_hrefs(self):
        self.write(self.candidate, "\n::warning::evil.html", "<a href='missing\n::warning::evil'>Broken</a>")
        status, output, _ = self.cli()
        self.assertEqual(status, 1)
        self.assertNotIn("\n::warning::", output)
        self.assertIn("\\n::warning::", output)


if __name__ == "__main__":
    unittest.main()
