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

## Deployment

Every push to `main` builds the site and deploys it to GitHub Pages. The
workflow downloads the latest Trail release rather than building it, so a change
to the builder reaches the site on its next deploy.

> This README sits in `.github/` rather than the repository root because the root
> is also the site root, where Trail accepts only `trail.toml` and `*.product`
> directories. GitHub renders it from here just the same.
