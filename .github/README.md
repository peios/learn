# Peios Learn

The source of [learn.peios.org](https://learn.peios.org) — concepts, guides, and
reference for the Peios operating system and the projects around it.

The site is built with [Trail](https://github.com/peios/trail), and its
structure is the directory tree: a `<slug>.product` directory per documented
thing, `<order>--<slug>.topic` for a set of articles, `<order>--<slug>.book` for
an ordered document, and one `.md` file per page. There is no table-of-contents
file to keep in sync — adding a file adds the page.

Trail's own documentation lives here too, under `trail.product/`, and is the
reference for the format:

- [Anatomy of a site](https://learn.peios.org/trail/getting-started/anatomy-of-a-site)
- [Articles and frontmatter](https://learn.peios.org/trail/writing/articles-and-frontmatter)
- [Directory and file names](https://learn.peios.org/trail/reference/directory-names)

## Building locally

```console
$ trail serve
```

Serves the site at <http://127.0.0.1:8724>, rebuilding as you edit. `trail build`
writes it to `dist/` instead. Both need a `trail` binary — `cargo build --release`
in [peios/trail](https://github.com/peios/trail), or the prebuilt Linux binary
from that repository's latest release.

## Pull-request validation

`.github/workflows/validate-docs.yml` strictly builds the proposed merge and the
exact base commit recorded in the pull-request event, using the same
checksum-pinned Trail binary. It then checks rendered HTML navigation links.
The proposed merge and base are separate, shallow checkouts; their outputs and
the binary stay outside both site roots. This read-only workflow does not deploy.

The rendered-link check fails when a source-page/href pair is broken in the
proposed merge but was not broken in the event base. It reports baseline,
candidate, newly broken, inherited, and resolved-or-removed pair counts, along
with duplicate occurrence counts. Existing generated print-view fragment defects
remain visible without blocking unrelated documentation fixes. There is no saved
allowlist: every PR compares fresh builds of its exact event base and proposed
merge. Increasing occurrences of an already-broken pair does not create a new
pair; the same broken href on another source page does.

Run the standard-library tests with Python 3.9 or newer:

```console
$ python3 -B -m unittest discover -s .github/scripts -p 'test_*.py' -v
```

To compare two already-built output directories locally:

```console
$ python3 -B .github/scripts/check_rendered_links.py /tmp/trail-base-site /tmp/trail-site
```

Build both revisions with the same verified Trail binary and `trail build
--strict --out <output-directory>`. Use separate source checkouts and output
directories outside the site roots. Do not compare a candidate against itself or
against a moving branch if you want the same regression boundary as CI.

The checker reads `a` and `area` hrefs from HTML, including generated print pages.
It resolves relative and root-relative paths, directory `index.html` pages, and
percent-encoded HTML IDs or named anchors. Query strings are ignored. Non-HTML
file links are checked for existence; their fragments are not interpreted.
External/protocol-relative URLs and every explicit scheme, including same-origin
absolute HTTPS URLs, are not fetched or checked. Resource `src` attributes,
JavaScript-generated links, and text-fragment content matches are outside its
scope. HTML `base` URLs are rejected rather than silently misresolved.

The exit status is 0 for no new broken pairs, 1 for regressions, or 2 if inputs
cannot be safely checked. Symlinks, special files, empty/nonexistent output,
invalid UTF-8 HTML, and exceeded scan limits are input errors. Malformed local
URLs and paths escaping the output root are broken links. Percent-encoded path
separators (`%2F` and `%5C`, case-insensitive) are also rejected as broken links:
server-dependent decoding makes their target ambiguous. Encoded separators in
fragment IDs are supported. Hrefs never cause the checker to read outside its
inventoried output. Keep output trees unchanged
while checking them. Default limits per tree are 100,000 entries, 128 directory
levels, 20,000 HTML pages, 32 MiB per page, 512 MiB of HTML, 2 million navigation
link occurrences, and 16,384 characters per href. `--max-details 0` prints counts
only; the default prints up to 20 pairs per category (maximum 1,000).

## Deployment

Every push to `main` builds the site and deploys it to GitHub Pages. The
workflow downloads the latest Trail release rather than building it, so a change
to the builder reaches the site on its next deploy.

> This README sits in `.github/` rather than the repository root because the root
> is also the site root, where Trail accepts only `trail.toml` and `*.product`
> directories. GitHub renders it from here just the same.
