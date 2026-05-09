---
title: peipkg-repo CLI
type: reference
description: Subcommands and flags for peipkg-repo, the index manager.
related:
  - peios-packages/running-a-farm/configuration
---

`peipkg-repo` turns a directory of `.peipkg` files into a signed repository state — descriptor, indexes, signatures, all on disk. Like `peipkg-build`, it has no daemon mode and no state of its own; the directory it produces *is* the state.

## Subcommands

| Subcommand | Purpose |
|---|---|
| `init` | Create an empty repository state from scratch. |
| `publish` | Add packages incrementally, regenerate indexes, sign, write a fresh state. |
| `verify` | Audit an existing state for integrity. |

## `peipkg-repo init`

```
peipkg-repo init [flags]
```

Creates a fresh state directory with an empty descriptor, empty active and archive indexes, and the public key file.

| Flag | Required | Description |
|---|---|---|
| `--name STRING` | **Yes** | Repository name. Recorded in `repo.json`. Kebab-case recommended. |
| `--description STRING` | Optional | Human-readable description. Empty if omitted. |
| `--sign-key PATH` | **Yes** | Ed25519 private key. The corresponding public key is published at `keys/<fingerprint>.pub`. |
| `--timestamp TS` | **Yes** | RFC 3339 UTC, ending in `Z`. Used as `generated_at` for the empty initial indexes. |
| `--out DIR` | **Yes** | Directory to write the new state into. Must be empty or non-existent. |

`init` refuses to overwrite a non-empty directory — once a repository exists, you publish into it (don't init again).

## `peipkg-repo publish`

```
peipkg-repo publish [flags]
```

Reads the previous state, ingests new `.peipkg` files, emits a fresh state with bumped `index_version`.

| Flag | Required | Description |
|---|---|---|
| `--in DIR` | **Yes** | Previous state directory. Must contain a valid `repo.json` and indexes. |
| `--new DIR` | One of `--new` or `--rebuild` | Directory containing new `.peipkg` files to add. |
| `--sign-key PATH` | **Yes** | Ed25519 private key. The same key that signed the previous state. |
| `--timestamp TS` | **Yes** | RFC 3339 UTC. Recorded as the new `generated_at` for both indexes. |
| `--out DIR` | **Yes** | New state directory. May be the same as `--in` (publish-in-place). |
| `--package-url-template TMPL` | Optional | URL template for new package entries. Placeholders: `{name}`, `{version}`, `{arch}`, `{filename}`. Default: `/p/{name}/{version}/{filename}` (the [PSD-009 §6.4](../../../specs/psd-009--peipkg/v0.22/6-repository/4-url-conventions) conventional path). Applies only to NEW entries — already-published entries keep their original URLs. |
| `--rebuild` | Optional | Ignore the previous archive entries and rebuild from scratch. Recovery hatch for when state has drifted. |
| `--all-packages-dir DIR` | Required with `--rebuild` | Directory containing every `.peipkg` ever published. Slow path (rehashes everything) but exhaustive. |

### Behaviour

- **Incremental publish** (default): reads `<in>/index/archive.json`, adds new entries from `--new`, increments `index_version`, writes the result to `--out`. Re-publishing the same `(name, version, architecture)` is rejected — the spec mandates retention, and a duplicate entry would silently overwrite history.
- **Rebuild publish** (`--rebuild`): ignores the previous archive, walks `--all-packages-dir`, hashes every `.peipkg` from disk, regenerates the state. Slow but recovers from corrupted indexes.

### URL templates

`peipkg-repo` doesn't care where packages are physically hosted — it just records URLs in the index. For the conventional layout (everything under one `<repo-base>`), the default template is the right answer. For split hosting (indexes on Pages, binaries on GitHub Releases), set `--package-url-template` to an absolute URL referencing your Releases:

```
--package-url-template "https://github.com/yourorg/your-repo/releases/download/{filename}/{filename}"
```

Old entries published under different templates keep their original URLs. The template applies only to entries added in this `publish` call.

## `peipkg-repo verify`

```
peipkg-repo verify [flags]
```

Reads a state directory and reports integrity issues. Read-only; never modifies the state.

| Flag | Required | Description |
|---|---|---|
| `--repo DIR` | **Yes** | State directory to audit. |
| `--mode MODE` | Optional (default `both`) | One of `metadata`, `hashes`, `both`. |
| `--all-packages-dir DIR` | Required when `mode` includes `hashes` | Directory containing the actual `.peipkg` files referenced by the indexes. |

### Modes

| Mode | What it checks | Speed |
|---|---|---|
| `metadata` | Signature envelopes parse, cryptographic signatures verify, archive ⊇ active relationship, per-name uniqueness in active. No file content reads. | Sub-second. |
| `hashes` | Re-hashes every `.peipkg` referenced by the indexes; compares to the recorded hash. Catches storage corruption. | Disk-bound. ~5 seconds per GB of packages. |
| `both` | Metadata first (fail-fast), then hashes if metadata passed. | Sum of the above. |

`metadata` mode is safe to run on every publish. `hashes` mode is a periodic audit — once a day from cron is plenty.

### Exit code

- `0` — passed.
- non-zero — found at least one issue. The issues are written to stderr.

A typical hash failure looks like:

```
FAIL: hash mismatch: nginx_1.27.0-1_x86_64.peipkg computed e3b0c44... index claims 4f91e7c1...
```

Causes:

- Storage corruption (rare on modern SSDs; common on spinning rust over years).
- Someone modified the `.peipkg` file out-of-band.
- `peipkg-repo publish` failed mid-write and left an inconsistent state (recover with `--rebuild`).

## What's not yet a subcommand

- `peipkg-repo rotate-key` — key rotation is currently a manual JSON edit + re-sign. See [Signing keys](../running-a-farm/signing-keys).
- `peipkg-repo prune-prerelease` — pre-release version pruning per [PSD-009 §6.3](../../../specs/psd-009--peipkg/v0.22/6-repository/3-archive-index) is permitted but not implemented in v0.

Both are operationally rare enough that automating them in v0 isn't a priority. They'll get subcommands once there's a real workflow to design against.
