---
title: Sources
type: concept
description: "How a pekit recipe gets its source tree: the git, url, and local source kinds, local overrides, materialisation and caching, archive extraction, version enumeration, provenance, and delegation."
related:
  - pekit/recipes/anatomy
  - pekit/recipes/versions
  - pekit/recipes/packages
  - pekit/using-pekit/invocation
  - pekit/reference/recipe-format
---

A **source** tells pekit where a recipe's code comes from. Before any build
target runs, pekit resolves the source into a concrete **source tree** on
disk — the directory that targets execute in and that [`@source:` package
references](~pekit/recipes/packages) read from. This page covers the source
kinds, how each is materialised, and how a recipe can borrow behaviour from its
source tree.

Sources are declared under `[source.*]` in the recipe. A recipe may have:

- **no external source** (sourceless) — the recipe directory itself is the tree;
- **one reproducible source** — either `[source.git]` **or** `[source.url]`,
  never both;
- **optionally a local override** — `[source.local]`, on its own or alongside a
  reproducible source.

In the code these map to `SourceConfig.HasReproducible()` (git or url set) and
`SourceConfig.HasExternal()` (reproducible **or** local set). Declaring two
reproducible tables is an error (`mixed_source`: "exactly one reproducible
source table is allowed").

## The three source kinds

### `[source.git]`

Clones a git repository and checks out a ref. It takes exactly four fields —
a required `url` (passed to `git clone --mirror`), a `ref` to check out
(templated with the [selected version](~pekit/recipes/versions); defaults to
`{{version}}` and must render non-empty), a `versions` **cap** that filters
enumerated or requested versions, and a `tag_regex` used when enumerating tags
(see [Enumeration](#enumeration)). The field-by-field schema is in the
[recipe format reference](~pekit/reference/recipe-format).

```toml
[source.git]
url = "https://github.com/example/widget.git"
ref = "v{{version}}"
versions = ">=2.0.0"
tag_regex = "^v([0-9]+\\.[0-9]+\\.[0-9]+)$"
```

If `ref` renders empty (for example, a bare `{{version}}` with no version
selected) pekit fails with `missing_version` — pass `--version` or set a
non-templated `ref`.

> The code does **not** implement a submodule option. `[source.git]` accepts
> only the four fields above; a `submodules` key is an `unknown_key` error.

### `[source.url]`

Downloads a file over HTTP(S), optionally extracting it as an archive. The
required `url` is templated with the selected version; `extract` (default
`false`) treats the download as an archive, with `root` naming the subdirectory
**inside the archive** to promote as the source tree; `versions` is a version
cap (as for git); `file_regex` is used when enumerating a URL listing; and
`checksum` pins the download to an expected digest — a single string or a
per-version table (see below). The full schema is in the
[recipe format reference](~pekit/reference/recipe-format).

```toml
[source.url]
url = "https://ftp.example.org/widget/widget-{{version}}.tar.gz"
extract = true
root = "widget-{{version}}"
checksum = "sha256:0f1e2d..."
```

`checksum` is a `sha256:<hex>` string, and it is the **only** algorithm the
verifier accepts — any other prefix fails with "unsupported checksum spec". It
may instead be a table keyed by version:

```toml
[source.url.checksum]
"1.2.0" = "sha256:aaaa..."
"1.3.0" = "sha256:bbbb..."
```

When the table form is used and the selected version has no entry, pekit fails
with `missing_checksum`. You rarely need `checksum`, though: every fetched
version is pinned automatically in the recipe's
[lockfile](#the-lockfile), and a URL source is only materialised
**unanchored** — not pinned to a digest — when it has neither a checksum nor a
lock entry, which matters for
[reproducible packaging](~pekit/recipes/packages).

A URL source can also carry a `[source.url.signature]` table pinning the
upstream maintainer's release-signing key: pekit fetches the detached
signature beside the artifact and verifies it before anything is locked or
built, closing the trust-on-first-use gap for brand-new versions. The full
schema is in the [recipe format reference](~pekit/reference/recipe-format).

### `[source.local]`

Points at a directory already on disk. Its single field is a required `path` —
the directory to use as the source tree, resolved relative to the recipe
directory.

```toml
[source.local]
path = "../widget-checkout"
```

`[source.local]` is an **override**, not a reproducible source: on its own a
recipe with only `[source.local]` is not reproducible (`HasReproducible()` is
false). The local tree is only used when a local flag selects it — see below.

## Selecting the local override

Two invocation flags choose the local override; they resolve differently and are
mutually exclusive (passing both is an error).

- **`--local`** (strict): require a local source. If neither `[source.local]`
  nor `--local=<path>` supplies a directory, pekit fails with
  `missing_local_source`. Use this to force building from a working checkout.
- **`--prefer-local`**: use the local source **if it is usable**, otherwise fall
  back to the reproducible source. If the local tree is missing and the recipe
  has no reproducible source, the fallback fails.

Both accept an inline path:

- `--local` / `--prefer-local` with **no** `=<path>` uses the directory from
  `[source.local]` (resolved relative to the recipe directory).
- `--local=<path>` / `--prefer-local=<path>` uses `<path>` resolved relative to
  the **invocation's working directory** (`cwd`), ignoring `[source.local]`.

The chosen directory must exist and be a readable directory, or pekit errors.
Local sources require an **exact** `--version` — `--latest`, `--all-versions`,
and constraint selectors are rejected (`unsupported_version_mode`); with no
version, a local build uses the placeholder `0.0.0-localdev`.

For a **sourceless** recipe, passing a local flag is an `unsupported_flag`
error — unless `--allow-unused` is set, in which case the flag is ignored with a
warning and the recipe stays sourceless.

## Materialisation

Resolving a source produces a `SourceState`: its `Kind`, the `SourceRoot`
(where targets run), a `ProvenanceRef`, and a timestamp. What pekit does to
produce the tree depends on the kind.

**Sourceless** (`recipe`). No work: the source root **is** the recipe
directory. Provenance is `recipe:<recipe-root>`.

**Local** (`local`). No copy or fetch: the source root **is** the local
directory itself; targets run in place. Provenance is `local:<path>`. Because
nothing is fetched, local sources are not cached and `--refresh-source` has no
effect on them.

**Git** (`git`). pekit keeps a bare **mirror** clone under
`<out_dir>/_source_cache/git/<hash>/repo.git`:

1. If the mirror does not exist, `git clone --mirror <url>`; otherwise
   `git fetch --prune --tags` to update it.
2. Resolve `ref` to an immutable commit (`git rev-parse <ref>^{commit}`).
3. When a version is selected, verify the resolved commit against the
   version's [lockfile entry](#the-lockfile) — or create the entry on first
   resolve.
4. Clone the mirror into `<out_dir>/git-<hash>/source`, then
   `git reset --hard <commit>` and `git clean -fdx` to pin the checkout.
5. Write a `source.pekit.json` manifest recording the URL, ref, resolved
   commit, and provenance.

Provenance is `git:<url>@<commit>` and the timestamp is the commit's committer
date, so a git build is anchored to a specific commit even when `ref` was a
branch or tag.

**URL** (`url`). pekit caches the downloaded artifact under
`<out_dir>/_source_cache/url/<hash>/`:

1. If the artifact is not already cached, download it (with a `pekit/2`
   user-agent).
2. If a `checksum` is set, verify it; on mismatch, re-download once and verify
   again before failing.
3. Verify the artifact against the version's [lockfile entry](#the-lockfile),
   cache hits included — or create the entry on first resolve, verifying the
   upstream signature first when `[source.url.signature]` is configured.
4. Materialise the tree at `<out_dir>/url-<hash>/source`: if `extract` is set,
   extract the archive to a temporary directory, then promote the `root`
   subdirectory (which must exist, else `missing_source_root`); otherwise copy
   the raw artifact into the source directory.
5. Write a `source.pekit.json` manifest.

The **downloaded artifact** is cached regardless. The **extracted tree** is
re-materialised from that cached artifact on each run when a checksum is set
(the pinned content is deterministic anyway); without a checksum the tree is
reused as long as the recorded manifest still matches.

### Caching and `--refresh-source`

Pekit does not expose configurable cache policies. Caching is exactly the
behaviour above — a persistent raw cache (mirror repo / downloaded artifact)
plus a materialised tree — and the one knob is **`--refresh-source`**, which
discards the cache and rebuilds from scratch:

- git: removes the mirror repo **and** the checkout scope, forcing a fresh
  `clone --mirror` and checkout.
- url: removes the cached artifact **and** the materialised scope, forcing a
  re-download and re-extract.
- local / sourceless: nothing to refresh.

A refresh does not relax the lock: the fresh download is still verified
against the lockfile, so `--refresh-source` is how you *check* upstream and
`pekit lock --repin` is how you *accept* a change.

### The lockfile

Fetched inputs are pinned **trust-on-first-use** in a machine-written
`pekit.lock` beside `pekit.toml`. The first time a source resolves for a
version, pekit records what it fetched — the artifact's SHA-256 for a url
source, the resolved commit for a git source — and every later resolve
verifies against that entry instead, cache hits included. A mismatch is a hard
`lock_mismatch` stop: upstream's published bytes (or a tag) changed under a
version that was already pinned. Accepting such a change is an explicit
ceremony, never automatic:

```text
pekit lock --repin --version 1.2.0
```

Commit the lockfile with the recipe. Local sources, dry runs, and git sources
without a selected version (a bare branch ref is a deliberately moving target)
are never locked. The file's exact schema is in
[Supporting files](~pekit/reference/supporting-files#pekitlock); the `lock`
command — including pre-locking versions without building — is in the
[command-line reference](~pekit/reference/cli).

### Archive extraction

Extraction is chosen by the artifact's **filename suffix**. Only these formats
are handled; anything else is an `unsupported_archive` error:

| Suffix | Handler |
| --- | --- |
| `.zip` | native zip reader |
| `.tar` | uncompressed tar |
| `.tar.gz`, `.tgz` | gzip + tar |
| `.tar.bz2`, `.tbz2` | bzip2 + tar |
| `.tar.zst` | zstd + tar |
| `.tar.xz`, `.txz` | tar piped through the external `xz -dc` (requires `xz` on `PATH`) |

Extraction is hardened: entries that escape the extraction root (absolute
paths, `..`, or traversal through a symlinked parent), unsafe symlink targets,
NUL bytes, unsupported entry types, and colliding entries are all rejected as
`unsafe_archive`.

## Enumeration

Reproducible sources can list the versions they offer upstream; this feeds
`--latest`, `--all-versions`, and constraint selectors (see
[Versions](~pekit/recipes/versions)).

- **git**: `git ls-remote --tags <url>`, with tags optionally filtered by
  `tag_regex`. If the regex has a capture group, group 1 is the version;
  otherwise an embedded `MAJOR.MINOR.PATCH` is extracted.
- **url**: fetch the directory listing derived from the `url` template (the part
  before the first `{{…}}`, up to the last `/`), filter entries by `file_regex`,
  and extract versions from the matches.

Local and sourceless recipes cannot enumerate
(`version_enumeration_unavailable`) — they require an exact version. The
`versions` field on a git or url source acts as a **cap** applied to the
enumerated (or requested) set; version selection itself is documented on the
[Versions](~pekit/recipes/versions) page.

## Source roots and provenance

The **source root** is the directory targets execute in and the base that
[`@source:` file references](~pekit/recipes/packages) resolve against. Every
resolution records a **provenance ref** identifying exactly what was
materialised:

| Kind | Provenance ref |
| --- | --- |
| sourceless | `recipe:<recipe-root>` |
| local | `local:<path>` |
| git | `git:<url>@<commit>` |
| url (checksummed) | `url:<url>#<checksum>` |
| url (locked, no checksum) | `url:<url>#sha256:<hash>` |
| url (no checksum, no lock entry) | `url:<url>` (marked **unanchored** — reachable only in a dry run, since a real resolve locks) |

For git and url sources the provenance is also written to a `source.pekit.json`
manifest beside the materialised tree, and pekit emits it as a `source` event
under `--verbose`.

## Delegation

A recipe can **borrow** behaviour from a `pekit.toml` that lives inside its
materialised source tree, using the `[delegate]` table (or the shorthand
`delegate = true`, which enables everything):

```toml
delegate = true

# or, selectively:
[delegate]
build    = true
env      = true
wrap     = true
packages = true
```

`[delegate]` has four surfaces plus `all`: `build` borrows the
build/test/install/clean **targets** from the source's recipe, `env` its
environment variables, `wrap` its command wrapper, and `packages` the package
definitions discovered in the source tree; `all` enables all four. (The key
table is in the [recipe format reference](~pekit/reference/recipe-format).)

Delegation only happens when the source tree is a **different** directory from
the recipe (so a sourceless or in-place local recipe never delegates), and, for
build targets, only when a `pekit.toml` exists at the source root. The merge
(`mergeDelegatedRecipe`) is **additive with the base recipe winning**: a
delegated target is adopted only if the base recipe does not already define a
target of the same kind and name, and adopted targets are tagged as owned by the
`source`. Env, wrap, and package delegation are likewise gated on the
corresponding `Allows…` flag and only apply when the source tree differs from
the recipe root.

This lets a thin Peios recipe wrap upstream software that already ships its own
pekit recipe: point `[source.git]` at the upstream repo, set `delegate = true`,
and reuse its build and packaging while overriding only what you need.

## Where to go next

For how enumerated versions are selected and rendered, read [Versions](~pekit/recipes/versions).

For turning the materialised tree into package payloads, read [Packaging files](~pekit/recipes/packages).

For the exhaustive `[source]` schema, read [Recipe format reference](~pekit/reference/recipe-format).
