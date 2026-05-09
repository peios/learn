---
title: Build Scripts
type: how-to
description: How peipkg-build invokes build.sh, what environment it gets, and how to write one for autotools, cmake, meson, or anything else.
related:
  - peios-packages/authoring-recipes/anatomy
  - peios-packages/authoring-recipes/multi-package
---

Every recipe has a `build.sh`. `peipkg-build` runs it with a defined environment, and the script's only job is to populate `$DESTDIR/` with the files that should end up in the package.

## The contract

`peipkg-build` invokes the script in a clean environment with these variables set:

| Variable | Value |
|---|---|
| `SOURCE_DIR` | Absolute path to the upstream source tree. Read-only by convention. |
| `DESTDIR` | Absolute path to a fresh, empty staging directory. Write your installed files here. |
| `SOURCE_DATE_EPOCH` | UNIX seconds equivalent of the build's `--timestamp`. Pass to build systems that respect it. |
| `LC_ALL` | `C` |
| `TZ` | `UTC` |
| `PATH` | Inherited from the caller. |

The script runs with stdin closed and a fresh working directory (a per-build tmpdir, not `$SOURCE_DIR`). Standard output and standard error pass through to whoever invoked `peipkg-build`.

The script's exit status is what `peipkg-build` watches: zero is success, anything else aborts the build. Standard `set -eu` at the top of the script is recommended.

## The smallest possible build script

If your "build" is just copying staged files (the case for documentation packages or anything that doesn't compile):

```bash
#!/bin/sh
set -eu
cp -a "$SOURCE_DIR/." "$DESTDIR/"
```

This is exactly what the [hello example](../getting-started/build-your-first-package) uses.

## Autotools

```bash
#!/bin/sh
set -eu
cd "$SOURCE_DIR"
./configure \
  --prefix=/usr \
  --libdir=/usr/lib/x86_64-linux-peios \
  --sysconfdir=/etc \
  --localstatedir=/var
make -j"$(nproc)"
make install DESTDIR="$DESTDIR"
```

Notes:

- `--libdir=/usr/lib/x86_64-linux-peios` puts shared libraries under the per-architecture path Peios uses. For `noarch` packages omit it.
- `make install DESTDIR=$DESTDIR` is autotools' standard staged-install pattern. Most upstream projects support it; if one doesn't, you'll need to install manually with `cp` after `make`.
- Run from `$SOURCE_DIR` rather than the script's cwd because autotools wants to see its `configure` script.

## CMake

```bash
#!/bin/sh
set -eu
cmake -S "$SOURCE_DIR" -B build \
  -DCMAKE_INSTALL_PREFIX=/usr \
  -DCMAKE_INSTALL_LIBDIR=lib/x86_64-linux-peios \
  -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel "$(nproc)"
DESTDIR="$DESTDIR" cmake --install build
```

CMake's out-of-source build is the default and uses the script's cwd for build artefacts (`build/`) — exactly what `peipkg-build`'s tmpdir expects.

## Meson

```bash
#!/bin/sh
set -eu
meson setup build "$SOURCE_DIR" \
  --prefix=/usr \
  --libdir=lib/x86_64-linux-peios \
  --buildtype=release
meson compile -C build
DESTDIR="$DESTDIR" meson install -C build
```

## What ends up in the package

`build.sh` populates `$DESTDIR/`. After it exits, `peipkg-build` walks the staged tree and partitions files across the recipe's `[[package]].files` glob lists. **Every file in `$DESTDIR/` must be claimed by some stanza**; an unclaimed file aborts the build with an "orphan" error listing what it found.

This is intentional: it forces recipes to be explicit about what ships and prevents transient build artefacts (test binaries, intermediate files, autotools cruft) from silently leaking into a published package.

> [!TIP]
> When a build fails with orphans, the fix is almost always "add the path to the right stanza's `files` list" or "remove the unwanted output from `$DESTDIR/` in `build.sh`." See [Multi-package recipes](./multi-package) for how to split outputs across stanzas.

## Things to avoid

- **Don't write outside `$DESTDIR/`.** `peipkg-build` doesn't sandbox the script — it trusts you. Writing to `/etc`, `/usr`, or anywhere else on the host is undefined behaviour and almost certainly a bug.
- **Don't depend on `pwd`.** The script runs with cwd set to a per-build tmpdir, not `$SOURCE_DIR`. Always anchor paths against `$SOURCE_DIR` or `$DESTDIR`.
- **Don't fetch network resources.** `build.sh` should be deterministic and offline-runnable. The build farm clones source ahead of time and gives you the result; if you need vendored dependencies, vendor them into the upstream tree and use them from `$SOURCE_DIR`.
- **Don't call `git`** to read commit metadata. The source tree's `.git/` is stripped before `build.sh` runs (by design — see the discussion in [tracking upstream](./tracking-upstream)). The version comes from the build farm, not from the source tree.
