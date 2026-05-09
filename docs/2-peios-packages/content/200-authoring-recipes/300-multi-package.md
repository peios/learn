---
title: Multi-Package Recipes
type: how-to
description: How to split one upstream's build output across several .peipkg files (runtime, -dev, -doc), how the file-glob partition works, and the same_build dependency shorthand.
related:
  - peios-packages/authoring-recipes/anatomy
  - peios-packages/authoring-recipes/dependencies
---

Most non-trivial libraries ship as several packages from one source tree:

- `libfoo` — the runtime shared library plus its SONAME symlink.
- `libfoo-dev` — header files, the static archive, the developer-link `.so` symlink, the `pkg-config` file.
- `libfoo-doc` — manual pages and other documentation that don't need rebuilding for each architecture.

A recipe expresses this by declaring multiple `[[package]]` stanzas. One run of `build.sh` populates a single `$DESTDIR/`, and `peipkg-build` partitions the resulting files across the stanzas using glob patterns.

## Three stanzas, one build

```toml
[meta]
license = "MIT"
homepage = "https://example.org/libfoo"
build_script = "build.sh"

[[package]]
name = "libfoo"
architecture = "x86_64"
description = "libfoo runtime"
side_effects = ["ldconfig"]
files = [
  "usr/lib/x86_64-linux-peios/libfoo.so.1",
  "usr/lib/x86_64-linux-peios/libfoo.so.1.*",
]

[[package]]
name = "libfoo-dev"
architecture = "x86_64"
description = "libfoo development files"
dependencies = [
  { name = "libfoo", same_build = true },
]
files = [
  "usr/include/**",
  "usr/lib/x86_64-linux-peios/libfoo.so",
  "usr/lib/x86_64-linux-peios/libfoo.a",
  "usr/lib/x86_64-linux-peios/pkgconfig/**",
]

[[package]]
name = "libfoo-doc"
architecture = "noarch"
description = "libfoo manual pages"
side_effects = ["man-db"]
files = [
  "usr/share/man/**",
  "usr/share/doc/libfoo/**",
]
```

`build.sh` runs once and produces files spanning all three stanzas. `peipkg-build` reads `$DESTDIR/`, applies each stanza's `files` globs, and writes three separate `.peipkg` files: `libfoo_<v>_x86_64.peipkg`, `libfoo-dev_<v>_x86_64.peipkg`, `libfoo-doc_<v>_noarch.peipkg`.

## How the partition works

The `files` field uses **doublestar globs** — the standard `*` and `?` plus `**` for recursive matching. Patterns are matched against paths relative to `$DESTDIR/` (no leading slash).

Three rules apply during partitioning:

1. **Every file must match exactly one stanza.** A file matched by no stanza is an *orphan*; the build aborts with the orphan path listed.
2. **A file must not match more than one stanza.** Overlapping globs are an *overlap*; the build aborts with both stanza names.
3. **Directories are added implicitly.** If a stanza claims `usr/lib/x86_64-linux-peios/libfoo.so.1`, `peipkg-build` includes `usr/`, `usr/lib/`, and `usr/lib/x86_64-linux-peios/` as directory entries in that stanza's payload.

Together these rules force recipes to be exhaustive and unambiguous. If you discover an orphan, either add the path to the right stanza or remove it from `$DESTDIR/` in `build.sh`. If you hit an overlap, narrow one of the globs.

> [!TIP]
> When in doubt, list paths explicitly rather than relying on `**`. `usr/lib/x86_64-linux-peios/libfoo.so.1` and `usr/lib/x86_64-linux-peios/libfoo.so.1.*` is clearer than `usr/lib/x86_64-linux-peios/libfoo.so.*`, which would also catch `libfoo.so` (the developer link) — likely not what you want.

## The conventional split

For a typical shared-library package, the convention is:

| Stanza | Contains | `architecture` |
|---|---|---|
| Runtime (`libfoo`) | The actual `.so.X.Y.Z` file plus the SONAME symlink (`.so.X`). | Native |
| Development (`-dev`) | Headers, static archive, developer-link `.so` symlink, `pkgconfig/*.pc`. | Native |
| Documentation (`-doc`) | Man pages, info pages, anything under `/usr/share/doc/`. | `noarch` |

The runtime stanza ships the SONAME chain a binary needs at *load* time. The dev stanza ships what the linker needs at *compile* time. The doc stanza is architecture-independent because man pages don't change between x86_64 and aarch64.

## Cross-package symlinks

The `-dev` stanza's `.so` symlink (`libfoo.so`) typically points at the runtime stanza's `.so.1` (`libfoo.so.1`). That target lives in a different package — at build time, `-dev`'s payload alone doesn't contain `libfoo.so.1`.

This is permitted. The recipe expresses the dependency through the `dependencies` array, and the symlink target is verified at extract time when both packages are installed together. See [Dependencies](./dependencies) for the dep declaration; the spec details are in [PSD-009 §3.4 symlinks](../../../specs/psd-009--peipkg/v0.22/3-format/4-payload).

## The `same_build = true` shorthand

A `-dev` package usually depends on the *exact same build* of its runtime sibling — anything else means installing `libfoo-dev` 1.2.3 alongside `libfoo` 1.2.4, which would have unpredictable ABI consequences.

`same_build = true` on a dependency entry tells `peipkg-build` to rewrite the constraint at build time:

```toml
[[package]]
name = "libfoo-dev"
dependencies = [
  { name = "libfoo", same_build = true },
]
```

If this build's version is `1.2.3-1`, the produced manifest will contain:

```json
{"name": "libfoo", "constraint": "= 1.2.3-1"}
```

`peipkg-build` rejects `same_build = true` if the named dependency isn't a sibling stanza in the same recipe — the shorthand is specifically for runtime↔dev pairs and doesn't make sense for external dependencies.

## When NOT to split

If a package has no headers, no static lib, no developer-link symlink, no man pages — split would leave `-dev` and `-doc` empty. Don't bother. One stanza is fine. The convention is "split when there's something to put in each output," not "always have three packages."

A binary application (a daemon, a CLI tool) typically ships as one stanza: the binary, its config files in `/etc/`, and any man pages all under one name.
