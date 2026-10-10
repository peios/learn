#!/usr/bin/env python3
"""Compare local navigation links in two static HTML output trees (stdlib only)."""

import argparse
from collections import Counter
from dataclasses import dataclass, field
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import stat
import sys
from urllib.parse import unquote, urlsplit


class InputError(Exception):
    """The supplied output cannot be checked safely or within the scan limits."""


@dataclass(frozen=True)
class Limits:
    entries: int = 100_000
    depth: int = 128
    pages: int = 20_000
    page_bytes: int = 32 * 1024 * 1024
    total_bytes: int = 512 * 1024 * 1024
    links: int = 2_000_000
    href_chars: int = 16_384


@dataclass
class Page:
    anchors: set = field(default_factory=set)
    links: Counter = field(default_factory=Counter)


@dataclass
class Scan:
    pages: int
    local_links: int
    broken: Counter
    reasons: dict


@dataclass
class Comparison:
    baseline: Scan
    candidate: Scan

    @property
    def new(self):
        return self.candidate.broken.keys() - self.baseline.broken.keys()

    @property
    def inherited(self):
        return self.candidate.broken.keys() & self.baseline.broken.keys()

    @property
    def resolved(self):
        return self.baseline.broken.keys() - self.candidate.broken.keys()


class PageParser(HTMLParser):
    def __init__(self, limits, remaining_links):
        super().__init__(convert_charrefs=True)
        self.page = Page()
        self.limits = limits
        self.remaining_links = remaining_links
        self.link_count = 0

    def handle_starttag(self, tag, attrs):
        # Keep the first occurrence, as browsers do for duplicate attributes.
        attrs = dict(reversed(attrs))
        if tag == "base" and "href" in attrs:
            raise InputError("HTML base URLs are unsupported")
        if attrs.get("id") is not None:
            self.page.anchors.add(attrs["id"])
        if tag == "a" and attrs.get("name") is not None:
            self.page.anchors.add(attrs["name"])
        if tag in {"a", "area"} and "href" in attrs:
            href = attrs["href"] or ""
            self.link_count += 1
            if self.link_count > self.remaining_links:
                raise InputError("navigation-link limit exceeded")
            if len(href) > self.limits.href_chars:
                raise InputError("href length limit exceeded")
            self.page.links[href] += 1


def inventory(root, limits):
    """Index files without following symlinks or inspecting any href target."""
    if root.is_symlink() or not root.is_dir():
        raise InputError(f"output root must be a real directory: {str(root)!r}")
    files, directories, html = set(), {""}, {}
    pending = [(root, "", 0)]
    entries = total_bytes = 0
    while pending:
        directory, relative, depth = pending.pop()
        with os.scandir(directory) as children:
            for entry in children:
                entries += 1
                if entries > limits.entries:
                    raise InputError("output entry limit exceeded")
                name = f"{relative}/{entry.name}" if relative else entry.name
                info = entry.stat(follow_symlinks=False)
                if stat.S_ISDIR(info.st_mode):
                    if depth + 1 > limits.depth:
                        raise InputError("output directory-depth limit exceeded")
                    directories.add(name)
                    pending.append((Path(entry.path), name, depth + 1))
                elif stat.S_ISREG(info.st_mode):
                    files.add(name)
                    if name.lower().endswith((".html", ".htm")):
                        total_bytes += info.st_size
                        if info.st_size > limits.page_bytes:
                            raise InputError(f"HTML page size limit exceeded: {name!r}")
                        if total_bytes > limits.total_bytes:
                            raise InputError("total HTML size limit exceeded")
                        html[name] = info.st_size
                        if len(html) > limits.pages:
                            raise InputError("HTML page-count limit exceeded")
                else:
                    raise InputError(f"symlink or special file in output: {name!r}")
    if not html:
        raise InputError("output contains no HTML pages")
    return files, directories, html


def decode(component):
    if re.search(r"%(?![0-9a-fA-F]{2})", component):
        raise ValueError("invalid percent escape")
    value = unquote(component, encoding="utf-8", errors="strict")
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise ValueError("control character in URL")
    return value


def local_target(page, href):
    """Return (path, fragment), None for nonlocal URLs, or raise ValueError."""
    if any(ord(char) < 32 or ord(char) == 127 for char in href):
        raise ValueError("control character in URL")
    url = urlsplit(href.strip(" "))
    # Includes https, mailto, data, tel, javascript, file, and //host/path.
    # No URL is fetched, including same-origin absolute URLs.
    if url.scheme or url.netloc:
        return None
    # Encoded separators have server-dependent path semantics. Reject them rather
    # than let decoding turn a relative URL into a root-relative path (or vice versa).
    if re.search(r"%(?:2f|5c)", url.path, re.IGNORECASE):
        raise ValueError("encoded separator in local path")
    # Strip literal text directives before decoding; encoded :~: is part of an ID.
    path, fragment = decode(url.path), decode(url.fragment.split(":~:", 1)[0])
    if "\\" in path:
        raise ValueError("backslash in local path")
    if not path:
        return page, fragment
    parts = [] if path.startswith("/") else page.split("/")[:-1]
    for part in path.split("/"):
        if part in {"", "."}:
            continue
        if part == "..":
            if not parts:
                raise ValueError("local path escapes output root")
            parts.pop()
        else:
            parts.append(part)
    target = "/".join(parts)
    if target and (path.endswith(("/", "/.", "/..")) or path in {".", ".."}):
        target += "/"
    return target, fragment


def scan(root, limits=Limits()):
    root = Path(root)
    files, directories, html = inventory(root, limits)
    pages = {}
    link_count = 0
    for name, size in sorted(html.items()):
        parser = PageParser(limits, limits.links - link_count)
        # Only inventoried regular HTML files are opened, never href-derived paths.
        # Outputs must be static while scanned; concurrent modification is unsupported.
        with (root / name).open("rb") as source:
            data = source.read(size + 1)
        if len(data) != size:
            raise InputError(f"HTML output changed while scanning: {name!r}")
        try:
            parser.feed(data.decode("utf-8"))
            parser.close()
        except (UnicodeError, InputError) as error:
            raise InputError(f"{name!r}: {error}") from error
        pages[name] = parser.page
        link_count += parser.link_count

    broken, reasons = Counter(), {}
    local_links = 0
    for name, page in pages.items():
        for href, count in page.links.items():
            reason = None
            try:
                target = local_target(name, href)
            except ValueError as error:
                reason = f"malformed or unsafe URL: {error}"
                target = None
            if target is None and reason is None:
                continue
            local_links += count
            if reason is None:
                path, fragment = target
                directory = path.rstrip("/")
                if directory in directories:
                    path = f"{directory}/index.html" if directory else "index.html"
                if path not in files:
                    reason = "missing file or directory index"
                elif fragment and path in pages:
                    if fragment.lower() != "top" and fragment not in pages[path].anchors:
                        reason = "missing HTML fragment"
            if reason is not None:
                pair = (name, href)
                broken[pair] = count
                reasons[pair] = reason
    return Scan(len(pages), local_links, broken, reasons)


def print_report(comparison, max_details):
    for label, result in (("Baseline", comparison.baseline), ("Candidate", comparison.candidate)):
        print(f"{label}: {result.pages} HTML pages; {result.local_links} local-link occurrences; "
              f"{len(result.broken)} broken page/href pairs ({sum(result.broken.values())} occurrences).")
    for label, pairs, result in (
        ("Newly broken", comparison.new, comparison.candidate),
        ("Inherited", comparison.inherited, comparison.candidate),
        ("Resolved or removed", comparison.resolved, comparison.baseline),
    ):
        print(f"{label}: {len(pairs)} page/href pairs "
              f"({sum(result.broken[pair] for pair in pairs)} occurrences).")
        for page, href in sorted(pairs)[:max_details]:
            pair = (page, href)
            # Escape filenames and hrefs so log text cannot become workflow commands.
            print(f"  {json.dumps(page, ensure_ascii=True)} -> {json.dumps(href, ensure_ascii=True)}: "
                  f"{result.reasons[pair]} ({result.broken[pair]} occurrences)")
        if len(pairs) > max_details:
            print(f"  ... {len(pairs) - max_details} additional pairs omitted.")
    print("FAIL: newly broken local links." if comparison.new else "PASS: no newly broken local links.")


def detail_limit(value):
    number = int(value)
    if not 0 <= number <= 1000:
        raise argparse.ArgumentTypeError("must be between 0 and 1000")
    return number


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path, help="rendered output for the exact PR event base")
    parser.add_argument("candidate", type=Path, help="rendered output for the proposed merge")
    parser.add_argument("--max-details", type=detail_limit, default=20,
                        help="maximum printed pairs per category (0–1000; default: 20)")
    args = parser.parse_args(argv)
    try:
        comparison = Comparison(scan(args.baseline), scan(args.candidate))
    except (InputError, OSError) as error:
        print(f"ERROR: rendered-link scan could not complete: {str(error)!r}", file=sys.stderr)
        return 2
    print_report(comparison, args.max_details)
    return 1 if comparison.new else 0


if __name__ == "__main__":
    sys.exit(main())
