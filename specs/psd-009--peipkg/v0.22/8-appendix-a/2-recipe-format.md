---
title: Recipe Format
---

> [!INFORMATIVE]
> This appendix is non-normative. It describes the conventional
> on-disk format that producer-side tools (peipkg-build,
> peipkg-manager, and any third-party equivalents) use to describe
> a single source package. The format is not part of the on-wire
> peipkg specification; the spec defines what packages look like
> on the wire (chapters 3–6), not how producers describe them on
> input.

## Purpose and scope

A *recipe* is the input to a producer toolchain: a small TOML
file plus a build script that together describe how to turn an
upstream source tree into one or more `.peipkg` files.

Recipes are conventionally laid out as:

```
recipes/
  <package>/
    peipkg.toml      # the recipe document
    build.sh         # the build script (or whatever build_script names)
```

A recipe is consumed by multiple producer-side tools, each of
which interprets the parts of the recipe relevant to its
responsibilities. The format is therefore designed for
*partial parsing*: each tool decodes the sections it owns and
tolerates sections owned by other tools.

## Top-level sections

The recipe file's top-level sections are partitioned by which
tool owns them:

| Section | Owner | Purpose |
|---|---|---|
| `[meta]` | peipkg-build | Shared facts: license, homepage, the build-script path |
| `[[package]]` | peipkg-build | Per-package stanzas: name, architecture, file globs, dependencies, side effects |
| `[upstream]` | peipkg-manager | Upstream source location, tag pattern, peios revision counter |
| `[watch]` | peipkg-manager | How the build farm detects new upstream versions (webhook, poll interval) |

Tools MUST tolerate top-level sections they do not own. A
peipkg-build implementation that encounters `[upstream]` or
`[watch]` while parsing a recipe MUST NOT reject the recipe;
it ignores those sections and processes the ones it owns. The
same applies in reverse for peipkg-manager.

Tools MUST reject *unknown keys within sections they do own*
as typo errors. peipkg-build's parser, for instance, rejects
`[meta].homepag` (typo of `homepage`) but accepts an entire
`[upstream]` section because `[upstream]` is not under its
authority.

> [!INFORMATIVE]
> Strict parsing within owned sections plus permissive parsing
> at the top level is the smallest rule that catches typos
> (the common authoring mistake) without coupling tools to one
> another's schemas. peipkg-build needs no awareness of what
> peipkg-manager will do with `[upstream]`; it only needs to
> know that the section is none of its concern.

## peipkg-build sections

### `[meta]`

```toml
[meta]
license = "Zlib"                          # SPDX identifier or expression
homepage = "https://zlib.net"             # upstream URL
source = "github:madler/zlib"             # informational only
build_script = "build.sh"                 # path to the build script (relative to the recipe dir)
```

| Field | Required | Purpose |
|---|---|---|
| `license` | recommended | SPDX identifier; passed through to manifest §3.3.3 |
| `homepage` | recommended | Upstream homepage URL; passed through to manifest §3.3.3 |
| `source` | optional | Informational pointer to upstream; consumed by peipkg-manager via `[upstream]` rather than this field |
| `build_script` | required | Path to the build script the producer runs |

### `[[package]]`

One stanza per output `.peipkg`. A recipe with three stanzas
emits three packages (e.g. runtime, -dev, -doc) per architecture.

```toml
[[package]]
name = "libfoo"
architecture = "x86_64"
description = "Brief one-line description."
dependencies = [{ name = "libc" }]
optional_dependencies = []
conflicts = []
provides = []
replaces = []
side_effects = ["ldconfig"]
files = [
  "usr/lib/x86_64-linux-peios/libfoo.so.1",
  "usr/lib/x86_64-linux-peios/libfoo.so.1.*",
]
```

The schemas of `dependencies`, `optional_dependencies`,
`conflicts`, `provides`, and `replaces` mirror the manifest
schemas (§4.1). `side_effects` is the §4.3.4 enumerated list.
The `files` field is the producer-side glob list that
partitions a built tree across multiple stanzas.

A recipe-level convenience: dependency entries MAY carry a
`same_build = true` shorthand, which the producer rewrites at
build time into a strict version-equality constraint pinned to
the build's own version. This handles the "-dev depends on
runtime at exactly this build's version" case without
forcing the recipe to know its own version.

```toml
[[package]]
name = "libfoo-dev"
architecture = "x86_64"
dependencies = [
  { name = "libfoo", same_build = true },
  { name = "libc-dev" },
]
files = ["usr/include/**", "usr/lib/x86_64-linux-peios/libfoo.so", ...]
```

## peipkg-manager sections

> [!INFORMATIVE]
> The schemas in this section are described as peipkg-manager
> uses them today. They are not part of the on-wire peipkg
> specification, and another build-farm tool may interpret
> these sections differently or ignore them entirely.

### `[upstream]`

Describes where to fetch source for new versions and how to
recognise version tags.

```toml
[upstream]
git = "https://github.com/madler/zlib"
tag_pattern = "^v(\\d+\\.\\d+\\.\\d+)$"
peios_revision = 1
```

| Field | Purpose |
|---|---|
| `git` | Git URL the build farm clones from |
| `tag_pattern` | Regex matching upstream version tags; capture group 1 is the version string passed to peipkg-build |
| `peios_revision` | The revision counter (`-1`, `-2`, …) for the same upstream version; bumped when the recipe needs rebuilding without an upstream change |

### `[watch]`

Describes how the build farm becomes aware of new upstream
versions.

```toml
[watch]
github_webhook = true       # accept GitHub push/tag webhooks for this repository
poll_interval = "1h"        # belt-and-braces: also poll git tags at this interval
```

A recipe that omits `[watch]` is built only on explicit
operator request. A recipe that omits `[upstream]` is not
auto-built at all; the package exists for manual builds only.

## Versioning and stability

The recipe format described in this appendix is the format
implemented at PSD-009 v0.22's release. Subsequent versions
of this specification may extend it (new sections, new fields
within existing sections). The "tools tolerate unknown
top-level sections" rule preserves forward compatibility:
older tools encountering newer sections ignore them safely.

Within owned sections, new fields are additive: tools SHOULD
ignore unknown keys within their own sections when reading
recipes that may have been authored against newer
specifications, while still rejecting unknown keys when the
recipe is authored against the same or older specification.
The mechanism for distinguishing these cases is left to
implementations; a `schema_version` field within `[meta]` is
a reasonable extension point.
