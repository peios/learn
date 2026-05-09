---
title: Build Your First Package
type: how-to
description: Walk through producing a signed .peipkg from scratch using peipkg-build. The example builds a tiny "hello" package end-to-end on any Linux host.
related:
  - peios-packages/getting-started/overview
  - peios-packages/authoring-recipes/anatomy
  - peios-packages/reference/cli-peipkg-build
---

This page produces a working `.peipkg` from nothing on any Linux host with `git`, `bash`, and `peipkg-build` on `PATH`. No build farm is required — `peipkg-build` is a standalone binary that turns a recipe into a single signed package file.

## What you'll build

A `.peipkg` named `hello_0.1-1_noarch.peipkg` containing one file: `usr/share/hello/MESSAGE`. It will be signed with a test key you generate inline. After this page you'll have a working example you can poke at, and a mental model for how `peipkg-build` is invoked.

## Prerequisites

Install the latest static `peipkg-build` binary:

```bash
curl -sSL -o /usr/local/bin/peipkg-build \
  https://github.com/peios/peipkg-build/releases/download/latest/peipkg-build-linux-amd64
chmod +x /usr/local/bin/peipkg-build
peipkg-build help
```

You should see two subcommands listed: `build` and `pack`.

## Lay out the recipe

A recipe is a directory with two files: `peipkg.toml` (the structured description) and `build.sh` (the script that produces the staged file tree). Make a working directory:

```bash
mkdir -p hello-pkg/recipe hello-pkg/source/usr/share/hello
echo 'Hello, Peios!' > hello-pkg/source/usr/share/hello/MESSAGE
```

`source/` is the upstream "source tree" we'll pretend to be packaging. In a real recipe this would be a `git clone` of the upstream project; here it's a directory with one file in it.

Write the recipe:

```bash
cat > hello-pkg/recipe/peipkg.toml <<'EOF'
[meta]
license = "CC0-1.0"
homepage = "https://example.org/hello"
build_script = "build.sh"

[[package]]
name = "hello"
architecture = "noarch"
description = "Smallest legal peipkg example."
files = [
  "usr/share/hello/MESSAGE",
]
EOF
```

The `[meta]` table holds shared facts: the SPDX license, a homepage URL, and the path to the build script (relative to the recipe directory). Each `[[package]]` stanza becomes one output `.peipkg` — this recipe declares a single one.

Write the build script:

```bash
cat > hello-pkg/recipe/build.sh <<'EOF'
#!/bin/sh
set -eu
cp -a "$SOURCE_DIR/." "$DESTDIR/"
EOF
chmod +x hello-pkg/recipe/build.sh
```

`peipkg-build` invokes `build.sh` with two environment variables you care about: `$SOURCE_DIR` (read-only path to the upstream source) and `$DESTDIR` (a fresh empty directory where the script installs the files that will end up in the package). For a real package, `build.sh` runs the upstream's build system (`./configure && make && make install DESTDIR=$DESTDIR`); here we just copy the source.

> [!NOTE]
> The recipe's `[[package]].files` list uses the same paths that appear under `$DESTDIR/`. `peipkg-build` walks the staged tree, partitions files across the recipe's stanzas by glob match, and rejects the build if anything in `$DESTDIR/` is unclaimed.

## Generate a signing key

`peipkg-build` produces signed packages. Generate a throwaway test key:

```bash
openssl genpkey -algorithm ed25519 -out hello-pkg/test-signing.ed25519
```

> [!CAUTION]
> This key is for the example only. Real signing keys live on the build farm host with appropriate permissions; see [Signing keys](../running-a-farm/signing-keys) for the operational discussion.

## Run the build

```bash
mkdir -p hello-pkg/out
peipkg-build build \
  --recipe hello-pkg/recipe/peipkg.toml \
  --source hello-pkg/source \
  --version 0.1-1 \
  --source-ref "test://hello/0.1.0" \
  --farm-id local-test \
  --timestamp 2026-05-01T12:00:00Z \
  --out hello-pkg/out \
  --sign-key hello-pkg/test-signing.ed25519
```

You should see one file written:

```
hello-pkg/out/hello_0.1-1_noarch.peipkg
```

The filename follows the convention `<name>_<version>_<architecture>.peipkg` and is computed from the recipe and the `--version` flag.

## What the flags mean

| Flag | What it is |
|---|---|
| `--recipe` | Path to `peipkg.toml`. The recipe directory is implied; `build.sh` is found relative to it. |
| `--source` | Read-only source tree exposed to `build.sh` as `$SOURCE_DIR`. |
| `--version` | The package version string. Format: `[<epoch>:]<upstream>-<peios_revision>` per [PSD-009 §2.2](../../../specs/psd-009--peipkg/v0.22/2-identity/2-versioning). |
| `--source-ref` | Recorded in the manifest's `build.source_ref` field — a machine-resolvable pointer to the inputs. Conventionally `git+<url>#<ref>`. |
| `--farm-id` | The build farm's identifier. Recorded in the manifest's `build.farm_id` for provenance. |
| `--timestamp` | RFC 3339 UTC timestamp ending in `Z`. Used as the mtime on every tar entry, which is how `peipkg-build` achieves byte-determinism. |
| `--out` | Output directory. One `.peipkg` per recipe stanza lands here. |
| `--sign-key` | Ed25519 private key (PEM PKCS#8 or 32-byte raw seed). Optional — omit to produce an unsigned package. |

## Inspect the output

`.peipkg` is just a Zstandard-compressed tar archive. Look inside:

```bash
zstd -d --stdout hello-pkg/out/hello_0.1-1_noarch.peipkg | tar tf -
```

You should see:

```
.peipkg/manifest.json
.peipkg/files.json
usr/
usr/share/
usr/share/hello/
usr/share/hello/MESSAGE
.peipkg/signature
```

The `.peipkg/` prefix is reserved for metadata: the manifest (package identity, dependencies, side effects), the per-file integrity manifest (SHA-256 of every file), and the inline Ed25519 signature. The rest is the payload as it'll be installed.

## Build it again

Run the same command a second time, with the same flags, and the resulting `.peipkg` will be byte-identical to the first one:

```bash
sha256sum hello-pkg/out/hello_0.1-1_noarch.peipkg
mv hello-pkg/out/hello_0.1-1_noarch.peipkg hello-pkg/out/run-1.peipkg
peipkg-build build --recipe ... --out hello-pkg/out  # same flags
sha256sum hello-pkg/out/hello_0.1-1_noarch.peipkg hello-pkg/out/run-1.peipkg
```

Same input, same bytes. That property is what makes signatures meaningful and audits possible. It's not an accident — `peipkg-build` enforces byte-determinism through tar entry ordering, fixed mtimes, and a deterministic Zstandard encoder.

## Where to go from here

The example is intentionally minimal — one stanza, one file, no dependencies. Real recipes have more moving parts:

- **Multi-package splits.** A library typically ships as runtime + `-dev` + `-doc`, three stanzas from one build. See [Multi-package recipes](../authoring-recipes/multi-package).
- **Dependencies.** Every non-trivial package depends on others. See [Dependencies](../authoring-recipes/dependencies).
- **Tracking upstream.** When you want a build farm to pick up new upstream releases automatically, the recipe gains `[upstream]` and `[watch]` sections. See [Tracking upstream](../authoring-recipes/tracking-upstream).
- **Putting it on a farm.** Once recipes work locally, [Set up a build farm](./set-up-a-build-farm) walks through `peipkg-manager`.
