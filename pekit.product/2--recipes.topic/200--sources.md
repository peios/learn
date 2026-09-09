---
title: Sources
type: concept
description: "How a recipe gets its source tree: the git, url, PyPI, and local kinds, materialisation and caching, the lockfile, patches, enumeration, and delegation."
related:
  - pekit/recipes/anatomy
  - pekit/recipes/versions
  - pekit/recipes/packages
  - pekit/running/invocation
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
- **one reproducible source** — one of `[source.git]`, `[source.url]`, or
  `[source.pypi]`, never more than one;
- **optionally a local override** — `[source.local]`, on its own or alongside a
  reproducible source.

A source is **reproducible** when it is git, url, or PyPI — those pin to exact
bytes. Declaring multiple reproducible tables is an error (`mixed_source`:
"exactly one reproducible source table is allowed").

## The four source kinds

### `[source.git]`

Clones a git repository and checks out a ref. It takes exactly five fields —
a required `url` (passed to `git clone --mirror`), a `ref` to check out
(templated with the [selected version](~pekit/recipes/versions); defaults to
`{{version}}` and must render non-empty), a `versions` **cap** that filters
enumerated or requested versions, and a `tag_regex` used when enumerating tags
(see [Enumeration](#enumeration)). The fifth, `tracked_path`, selects the
moving-ref snapshot mode described below. The field-by-field schema is in the
[recipe format reference](~pekit/reference/recipe-format).

```toml
[source.git]
url = "https://github.com/example/widget.git"
ref = "v{{version}}"
versions = ">=2.0.0"
tag_regex = "^v(?P<version>[0-9]+\\.[0-9]+\\.[0-9]+)$"
```

If `ref` renders empty (for example, a bare `{{version}}` with no version
selected) pekit fails with `missing_version` — pass `--version` or set a
non-templated `ref`.

> [!NOTE]
> There is **no** submodule option. A `submodules` key is an `unknown_key`
> error.

#### Tracking one file on a moving ref

Some upstream data has no release tags of its own: one file on a stable branch
*is* the published stream. Set `tracked_path` to follow that file without
turning every unrelated branch commit into a package release:

```toml
[source.git]
url = "https://github.com/example/upstream.git"
ref = "refs/heads/release"
tracked_path = "security/trust/certdata.txt"
versions = ">= 2026.01.01"
```

This is deliberately a bounded mode:

- `ref` must be fixed and non-templated; `tag_regex` cannot be combined with
  `tracked_path`;
- `tracked_path` is one clean repository-relative regular file, not a
  directory, symlink, or submodule;
- discovery observes the fixed ref and compares the selected blob's SHA-256
  with the newest matching lock entry. An unrelated commit, or any observation
  with the same bytes as that newest lock, creates no version;
- a changed blob receives the UTC discovery date `YYYY.MM.DD`. Further changed
  blobs discovered and locked that day receive `.2`, `.3`, and so on. The
  suffix follows committed lock history, and a backwards wall clock clamps to
  the newest locked date, so the sequence remains monotonic;
- the lock binds repository URL, fixed ref, path, immutable commit, Git blob
  object ID, and SHA-256 of the blob bytes. It is append-only for this mode:
  discover a change with `--latest`; `--repin` is rejected.

`--latest`, constraints, and `--all-versions` check the moving ref. The
enumerated set is all matching historical lock entries plus the current
changed blob, if there is one; `--all-versions` therefore retains history
rather than replacing it with the tip. An exact locked version does **not**
resolve or fetch the moving ref. It uses the pinned commit and path, works
offline when those objects are cached, and may fetch only the pinned commit on
a cold cache. An exact version not yet locked is accepted only when it is the
date version Pekit computes for the currently observed changed blob.

The source root preserves the tracked relative path and contains no other
upstream file. Targets therefore read the example above at
`$PEKIT_SOURCE_ROOT/security/trust/certdata.txt`. This mode is suited to a
single independently versioned data input; use ordinary git mode when the
build needs a repository tree.

### `[source.url]`

Downloads a file over HTTP(S), optionally extracting it as an archive. The
required `url` is templated with the selected version; `extract` (default
`false`) treats the download as an archive, with `root` naming the subdirectory
**inside the archive** to promote as the source tree; `versions` is a version
cap (as for git); `listing_url` can name a release page when the download
template does not live in a browsable directory; `file_regex` is used when
enumerating that listing; and `checksum` pins the download to an expected
digest — a single string or a per-version table (see below). The full schema is in the
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

A signing key that expires later does not invalidate an immutable historical
release: Pekit accepts the signature only when its signed creation time falls
within the key's validity period. A present-time key revocation, an explicitly
expired signature, a signature created after key expiry, or a materially
future-dated signature remains a hard failure by default. For an upstream that
knowingly continues to sign new releases after its key expires, a recipe may
set `ignore_expiry = true` in the signature table. This is an explicit
per-source exception to key expiry only: signature validity, the pinned
fingerprint, revocation, explicit signature expiry, and timestamp checks remain
mandatory.

Some upstreams publish one `major.minor` archive and then maintain it as an
incremental numbered patch series. `[source.url.patch_series]` models that
scheme without fetching anything from a build script:

```toml
[source.url]
url = "https://ftp.example.org/widget/widget-{{version}}.tar.gz"
extract = true
root = "widget-{{version}}"
versions = ">= 5.3.0"
file_regex = 'widget-[0-9]+\.[0-9]+\.tar\.gz'

[source.url.patch_series]
url = "https://ftp.example.org/widget/widget-{{major}}.{{minor}}-patches/widget{{major}}{{minor}}-{{patch}}"
patch_width = 3
strip = 0
```

For a selected `5.3.15`, the primary `url`, `root`, checksum lookup, and base
signature render with base version `5.3`; patch URLs render from `001` through
`015`. The resulting version is the base archive plus that ordered prefix.
Enumeration exposes `5.3.0`, `5.3.1`, …, `5.3.15`, so ordinary runs select the
latest while `--all-versions` can reproduce the complete patchlevel history.
The patch listing must be contiguous from 1; a missing number is
`url_patch_gap`. A missing patch directory represents a new base release at
patchlevel zero.

`[source.url.patch_series.signature]` accepts the same fields and has the same
required-verification semantics as `[source.url.signature]`. Each patch is
downloaded, verified, and recorded in the selected version's lock entry before
that entry is written, so failure anywhere in the chain leaves no partial
lock. `file_regex` is optional; when present it must contain a named `patch`
capture. `patch_width` controls zero-padding and `strip` is the non-negative
path-component count passed to `patch -p` (both default to zero).

### `[source.pypi]`

Selects a project source distribution from PyPI's standardized JSON Simple
API. This is the low-maintenance choice for recipes that should automatically
discover new PyPI releases:

```toml
[source.pypi]
project = "asciidoc"
artifact = "sdist"
versions = ">= 10.2.1"
```

All three fields are declarative rather than URL templates. `project` is the
PyPI project name; `artifact` is required and currently must be exactly
`"sdist"`; and `versions` is the usual optional source version cap. Pekit
normalizes the project name for the `/simple/<project>/` request, asks for the
versioned JSON representation, and considers only
[standardized `.tar.gz` sdists](https://packaging.python.org/en/latest/specifications/source-distribution-format/#source-distribution-file-name).

Automatic discovery deliberately excludes yanked files, prereleases, wheels,
legacy non-standard sdist filenames, and versions outside Pekit's version
grammar. A release must expose exactly one eligible sdist with a valid SHA-256:
none is `pypi_sdist_missing` when requested exactly, while multiple candidates
are `pypi_sdist_ambiguous`. Pekit never guesses between files.

The selected file's index-advertised SHA-256 is verified on download, and its
exact file URL and digest are written through the ordinary
[`pekit.lock`](#the-lockfile) mechanism. Once locked, an exact-version rebuild
does not need the live project index: it replays the pinned URL and hash from
the lock (using the artifact cache when present). `--latest`, constraints, and
`--all-versions` still consult the index so they can discover newly published
versions. A release that is yanked after it was locked therefore remains
rebuildable by exact version but is not selected during a fresh automatic
discovery.

### `[source.local]`

Points at a directory already on disk. Its single field is a required `path` —
the directory to use as the source tree, resolved relative to the recipe
directory.

```toml
[source.local]
path = "../widget-checkout"
```

`[source.local]` is an **override**, not a reproducible source: a recipe
with only `[source.local]` cannot be pinned or enumerated. The local tree is
only used when a local flag selects it — see below.

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

Resolving a source produces a source state: its kind, the source root
(where targets run), a provenance ref, and a timestamp. What pekit does to
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
   `git fetch --prune --tags` to update it. A **failed refresh** is fatal
   only when nothing pins what the ref means: if the selected version is
   locked, the entry matches the rendered ref, and the pinned commit is
   already in the mirror, pekit warns and builds from the locked commit
   instead — so a rate-limited or unreachable upstream cannot block a
   locked build. Unlocked resolves still fail hard.
2. Resolve `ref` to an immutable commit (`git rev-parse <ref>^{commit}`).
3. When a version is selected, verify the resolved commit against the
   version's [lockfile entry](#the-lockfile) — or create the entry on first
   resolve.
4. Clone the mirror into `<out_dir>/git-<hash>/source`, then
   `git reset --hard <commit>` and `git clean -fdx` to pin the checkout.
5. Apply the recipe's [patch series](#patches), when one is declared. Reset
   and clean restored the pristine tree, so the series re-applies on every
   resolve.
6. Write a `source.pekit.json` manifest recording the URL, ref, resolved
   commit, and provenance.

Provenance is `git:<url>@<commit>` and the timestamp is the commit's committer
date, so a git build is anchored to a specific commit even when `ref` was a
branch or tag.

**Tracked-path git** (`git`). Pekit keeps a separate bare cache under
`<out_dir>/_source_cache/git-tracked/<hash>/repo.git`. Discovery shallow-fetches
the fixed ref with a `blob:none` partial-clone filter, resolves its commit, and
requests only `tracked_path`'s blob. A server without partial-clone filtering
may transfer the other blobs in that shallow snapshot, but Pekit still
materialises and packages only the selected regular file. A locked resolve
uses the lock's commit directly and never consults the moving ref; a cold cache
therefore requires a server that permits fetching that pinned commit object.
The materialised tree is recreated from the verified blob on every resolve,
then any recipe patch series is applied. Provenance is
`git:<url>@<commit>:<path>#sha256:<blob-sha256>`.

**URL** (`url`). pekit caches the downloaded artifact under
`<out_dir>/_source_cache/url/<hash>/`:

1. If the artifact is not already cached, download it (with a `pekit/2`
   user-agent).
2. If a `checksum` is set, verify it; on mismatch, re-download once and verify
   again before failing.
3. For a remote patch series, download patches 1 through the selected
   patchlevel. Verify the base and every patch against the version's
   [lockfile entry](#the-lockfile), cache hits included — or atomically create
   the entry, verifying all configured upstream signatures first.
4. Materialise the tree at `<out_dir>/url-<hash>/source`: if `extract` is set,
   extract the archive to a temporary directory, then promote the `root`
   subdirectory (which must exist, else `missing_source_root`); otherwise copy
   the raw artifact into the source directory. Extraction preserves each
   regular file's archived mtime — release tarballs encode "generated
   outputs are newer than their inputs" in timestamps, and losing that
   fires autotools maintainer rebuild rules in environments without the
   maintainer tools.
5. Apply remote patches in numeric order with `patch`, no fuzz, then apply the
   recipe's [patch series](#patches), when one is declared. The
   series' content hash joins the materialisation scope, so an edited patch
   lands in a fresh extraction.
6. Write a `source.pekit.json` manifest.

The **downloaded artifact** is cached regardless. The **extracted tree** is
re-materialised from that cached artifact on each run when a checksum is set
(the pinned content is deterministic anyway); without a checksum the tree is
reused as long as the recorded manifest still matches.

**PyPI** (`pypi`). Pekit first selects the one eligible sdist for the chosen
version as described above, then uses the URL materialisation path: the
advertised hash is verified, the pristine `.tar.gz` is cached, its standardized
top-level directory is extracted, patches are applied, and the exact file is
locked. Provenance is `pypi:<normalized-project>@<version>#sha256:<hash>`.

### Caching and `--refresh-source`

Pekit does not expose configurable cache policies. Caching is exactly the
behaviour above — a persistent raw cache (mirror repo / downloaded artifact)
plus a materialised tree — and the one knob is **`--refresh-source`**, which
discards the cache and rebuilds from scratch:

- git: removes the mirror repo **and** the checkout scope, forcing a fresh
  `clone --mirror` and checkout. Tracked-path git removes its sparse cache and
  refetches the selected immutable commit (for an exact lock) or moving ref
  (during discovery), without changing what the lock asserts.
- url / PyPI: removes the cached artifact **and** the materialised scope,
  forcing a re-download and re-extract.
- local / sourceless: nothing to refresh.

A refresh does not relax the lock: the fresh download is still verified
against the lockfile, so `--refresh-source` is how you *check* upstream and
`pekit lock --repin` is how you *accept* a change.

### The lockfile

Fetched inputs are pinned **trust-on-first-use** in a machine-written
`pekit.lock` beside `pekit.toml`. The first time a source resolves for a
version, pekit records what it fetched — the artifact's SHA-256 for a url or
PyPI source, every ordered remote-patch URL and SHA-256 when present, or the
resolved commit for an ordinary git source. A tracked-path git entry records
the repository, fixed ref, path, commit, blob object ID, and blob SHA-256. Every
later resolve verifies against
that entry instead, cache hits included. A mismatch is a hard
`lock_mismatch` stop: upstream's published bytes (or a tag) changed under a
version that was already pinned. Accepting such a change is an explicit
ceremony, never automatic for ordinary git and URL sources:

```text
pekit lock --repin --version 1.2.0
```

Commit the lockfile with the recipe. Local sources, dry runs, and git sources
without a selected version (a bare branch ref is a deliberately moving target)
are never locked. The file's exact schema is in
[Supporting files](~pekit/reference/supporting-files#pekit-lock); the `lock`
command — including pre-locking versions without building — is in the
[command-line reference](~pekit/reference/cli).

### Source packages

A recipe with a reproducible source automatically emits a
**corresponding-source package** alongside its `peipkg`-format members — the
pristine upstream artifact, the patch series, and the recipe files, verifiable
against the committed `pekit.lock` — and every emitted manifest records the
provenance of its inputs, recipe, and builder. Both are covered in
[Signing and provenance](~pekit/running/signing-and-provenance); opt out or
rename with the recipe's
[`[source_package]`](~pekit/reference/recipe-format#source-package) table.

### Archive extraction

Extraction is chosen by the artifact's **filename suffix**. Only these formats
are handled; anything else is an `unsupported_archive` error:

| Suffix | Handler |
| --- | --- |
| `.zip` | native zip reader |
| `.tar` | uncompressed tar |
| `.tar.gz`, `.tgz`, `.crate` | gzip + tar (`.crate` is cargo's publish format — a plain gzipped tarball) |
| `.tar.bz2`, `.tbz2` | bzip2 + tar |
| `.tar.zst` | zstd + tar |
| `.tar.xz`, `.txz` | tar piped through the external `xz -dc` (requires `xz` on `PATH`) |

Extraction is hardened: entries that escape the extraction root (absolute
paths, `..`, or traversal through a symlinked parent), unsafe symlink targets,
NUL bytes, unsupported entry types, and colliding entries are all rejected as
`unsafe_archive`.

## Patches

A recipe can carry a patch series that pekit applies to the materialised
tree, declared as a directory name under `[source]`:

```toml
[source]
patches = "patches"
```

The directory's `series` file lists patch files in apply order (one relative
path per line; `#` starts a comment). pekit applies them with `git apply` —
strictly, with no fuzz — immediately after the pristine tree is materialised
and before any target runs, so targets always see the patched tree and
`@source:` mappings package patched files. How that interacts with caching
follows the source kind:

- **git** sources re-apply the series on every resolve: the checkout is
  reset to the pinned commit and cleaned first, so an edited patch takes
  effect on the next run.
- **url and PyPI** sources materialise once per patch-set content: the series'
  hash joins the materialisation scope, so an edited patch extracts and
  patches a fresh tree.
- **local** sources are never patched — a local tree is your own working
  state, often with the series already applied or mid-rework. pekit emits a
  warning and continues.

A failed hunk is `patch_apply`; a patch that matches nothing is
`patch_skipped`; either aborts materialisation and leaves no half-patched
tree behind. The series grammar and its validation errors are in
[Supporting files](~pekit/reference/supporting-files#the-patches-directory).

Patches are committed recipe content, so the [lockfile](#the-lockfile) is
uninvolved: it pins fetched bytes, and the patch series is already under
version control. The whole directory ships in the recipe's
[source package](#source-packages) under `patches/` — the shipped series is
the applied series by construction.

This recipe-owned series is distinct from
[`[source.url.patch_series]`](#source-url), whose patches are upstream inputs:
remote patches are signature-verified and locked, ship below
`upstream/patches/`, and are applied before any recipe-owned patches.

Rebasing on a version bump is deliberately manual: a stale patch fails
loudly, so materialise the new tree (`pekit lock --version <v>` is enough),
fix the patch, and run again.

## Enumeration

Reproducible sources can list the versions they offer upstream; this feeds
`--latest`, `--all-versions`, and constraint selectors (see
[Versions](~pekit/recipes/versions)).

- **git**: `git ls-remote --tags <url>`, with tags optionally filtered by
  `tag_regex`. A named `version` capture supplies the complete version. Named
  `major`, `minor`, and `patch` captures instead compose a dotted version;
  optional `prerelease` and `buildmeta` captures are appended. For example,
  `ref = "{{major}}{{minor}}{{patch}}"` with
  `tag_regex = '^(?P<major>\d{4})(?P<minor>\d{2})(?P<patch>\d{2})$'` maps the
  tag `20260810` to version `2026.08.10` and renders it back to the same ref.
  Without named version captures, pekit extracts the version from the ref
  template or an embedded `MAJOR.MINOR.PATCH`; unnamed capture groups only
  filter tags.
- **tracked-path git**: shallow-fetch the fixed ref and expose matching
  versions already in `pekit.lock`, plus one newly synthesized date version
  only when the current tracked blob differs from the newest lock.
- **url**: fetch `listing_url` when set, otherwise derive a directory listing
  from the `url` template (the part before the first `{{…}}`, up to the last
  `/`); filter entries by `file_regex`, and extract versions from the matches.
- **PyPI**: fetch the project's standardized JSON Simple API page once per
  invocation and enumerate the eligible sdists described under
  [`[source.pypi]`](#source-pypi).

Local and sourceless recipes cannot enumerate
(`version_enumeration_unavailable`) — they require an exact version. The
`versions` field on a git, url, or PyPI source acts as a **cap** applied to the
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
| tracked-path git | `git:<url>@<commit>:<path>#sha256:<blob-sha256>` |
| url (checksummed) | `url:<url>#<checksum>` |
| url (locked, no checksum) | `url:<url>#sha256:<hash>` |
| url with remote patches | the locked url ref above plus `+patches:sha256:<series-hash>` |
| url (no checksum, no lock entry) | `url:<url>` (marked **unanchored** — reachable only in a dry run, since a real resolve locks) |
| PyPI | `pypi:<normalized-project>@<version>#sha256:<hash>` |

For git, url, and PyPI sources the provenance is also written to a `source.pekit.json`
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
build targets, only when a `pekit.toml` exists at the source root. The merge is **additive with the base recipe winning**: a
delegated target is adopted only if the base recipe does not already define a
target of the same kind and name, and adopted targets are tagged as owned by the
`source`. Env, wrap, and package delegation are likewise gated on their
corresponding `[delegate]` flags and only apply when the source tree differs
from the recipe root.

This lets a thin Peios recipe wrap upstream software that already ships its own
pekit recipe: point `[source.git]` at the upstream repo, set `delegate = true`,
and reuse its build and packaging while overriding only what you need.

## Where to go next

For how enumerated versions are selected and rendered, read [Versions](~pekit/recipes/versions).

For turning the materialised tree into package payloads, read [Packaging files](~pekit/recipes/packages).

For the exhaustive `[source]` schema, read [Recipe format reference](~pekit/reference/recipe-format).
