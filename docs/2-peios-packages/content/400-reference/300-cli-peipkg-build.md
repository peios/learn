---
title: peipkg-build CLI
type: reference
description: Subcommands and flags for peipkg-build, the deterministic .peipkg emitter.
related:
  - peios-packages/getting-started/build-your-first-package
  - peios-packages/reference/recipe-format
---

`peipkg-build` is the byte-deterministic format emitter. Given a recipe and a source tree, it produces one or more signed `.peipkg` files. It has no daemon mode, no state, and no network access.

## Subcommands

| Subcommand | Purpose |
|---|---|
| `build` | Run a recipe end-to-end: execute `build.sh`, partition outputs across stanzas, emit one `.peipkg` per stanza. |
| `pack` | Skip the build step. Emit a single `.peipkg` from a pre-resolved manifest + a staged tree. For exotic builds where the recipe abstraction gets in the way. |

## `peipkg-build build`

```
peipkg-build build [flags]
```

| Flag | Required | Description |
|---|---|---|
| `--recipe PATH` | **Yes** | Path to `peipkg.toml`. The recipe directory is implied. |
| `--source PATH` | **Yes** | Source tree exposed to `build.sh` as `$SOURCE_DIR`. |
| `--version VERSION` | **Yes** | Package version. Format: `[<epoch>:]<upstream>-<peios_revision>`. |
| `--source-ref REF` | **Yes** | Recorded in `manifest.build.source_ref`. Conventional form: `git+<url>#refs/tags/<tag>`. |
| `--farm-id ID` | **Yes** | Recorded in `manifest.build.farm_id`. |
| `--timestamp TS` | **Yes** | RFC 3339 UTC timestamp ending in `Z`. Used as the mtime of every tar entry; drives byte-determinism. |
| `--out DIR` | **Yes** | Output directory. One `.peipkg` per recipe stanza is written here. Created if missing. |
| `--sign-key PATH` | Optional | Ed25519 private key. Omit to produce an unsigned package. |

### Output filename

Each stanza produces one file named `<name>_<version>_<architecture>.peipkg`. A multi-stanza recipe produces one file per stanza in the same `--out` directory.

### Failure modes

| Exit code | Cause |
|---|---|
| `0` | Success. |
| `1` | Build failed: `build.sh` exited non-zero, source/recipe paths invalid, missing required flag, signing key invalid, partition rejected (orphan or overlap), or any other build-time error. |
| `2` | Flag parsing error. |

When `build.sh` fails, `peipkg-build` prints whatever the script wrote to stderr and exits 1. When the partition step rejects (orphan path, overlapping globs, unknown architecture), the error message names the offending paths or stanzas.

## `peipkg-build pack`

```
peipkg-build pack [flags]
```

| Flag | Required | Description |
|---|---|---|
| `--manifest PATH` | **Yes** | Path to a fully-resolved `manifest.json`. The caller has already filled in name, version, dependencies, etc. |
| `--staged DIR` | **Yes** | Pre-staged file tree (the equivalent of what `build.sh` would have produced). |
| `--out PATH` | **Yes** | Output `.peipkg` file path. |
| `--sign-key PATH` | Optional | Ed25519 private key. |

`pack` is for when the standard recipe + `build.sh` flow doesn't fit — kernel builds, glibc builds, anything where the caller wants to produce the manifest by hand. The staged tree must be partitioned already (no `[[package]]` stanzas; one tree, one output).

Most users never need `pack`. If you're not sure whether you need it, you don't.

## Determinism

Same recipe + same source + same flags → same `.peipkg` bytes, every time. The byte-determinism rules ([PSD-009 §3.1.4](../../../specs/psd-009--peipkg/v0.22/3-format/1-container)) are enforced internally:

- Tar entries are lex-sorted by path.
- Every entry's mtime equals `--timestamp`.
- uid/gid are 0; owner/group are `"root"`.
- Mode is `0777` for every entry.
- No xattrs, no PAX records for paths that fit ustar.
- Zstandard compression is deterministic at the chosen level.

You can verify determinism by running the same `build` invocation twice and comparing `sha256sum` of the output. They will match.
