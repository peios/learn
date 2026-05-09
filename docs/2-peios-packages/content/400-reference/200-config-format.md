---
title: peipkg-config.toml Reference
type: reference
description: Compact field-by-field reference for peipkg-manager's configuration file. The how-to is on the configuration page.
related:
  - peios-packages/running-a-farm/configuration
---

`peipkg-manager` reads a single TOML configuration file passed via `--config`. Conventional path: `/etc/peipkg-manager/config.toml`.

For the full discussion (defaults, edge cases, what-not-to-do), see [Configuration](../running-a-farm/configuration). This page is the schema reference.

## Sections

| Section | Required |
|---|---|
| `[manager]` | Yes |
| `[repo]` | Yes |
| `[signing]` | Yes |
| `[upload]` | No (default: no upload) |
| `[http]` | No (default: no HTTP server) |
| `[poll]` | Yes |

## `[manager]`

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | **Yes** | Farm identifier recorded in every package's `manifest.build.farm_id`. |
| `recipes_dir` | string | **Yes** | Absolute path to the directory containing recipe subdirectories. |
| `state_dir` | string | **Yes** | Absolute path to the manager's writable state. Created on first run; subdirectories `sources/`, `stage/`, `publish/`, `repo/` are managed by the daemon. |

## `[repo]`

Used at first-run init only.

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | **Yes** | Repository name. Recorded in `repo.json`'s `repo.name`. Kebab-case recommended. |
| `description` | string | Optional | Human-readable description. Empty if omitted. |

## `[signing]`

| Field | Type | Required | Description |
|---|---|---|---|
| `key_file` | string | **Yes** | Path to Ed25519 private key (PEM PKCS#8 or 32-byte raw seed). Must be readable by the daemon's user. |

## `[upload]`

| Field | Type | Required | Description |
|---|---|---|---|
| `backend` | string | Optional (default `none`) | One of `rclone`, `none`. `none` (or omitted section) disables upload. |
| `remote` | string | Required when `backend = "rclone"` | rclone remote and path, e.g. `r2:pkgs.example.org`. Must exist in rclone's config. |

## `[http]`

| Field | Type | Required | Description |
|---|---|---|---|
| `addr` | string | Optional (default `""`) | Listen address. `""` disables HTTP entirely. |
| `webhook_secret_file` | string | Required when `addr` is set and any recipe has `github_webhook = true` | Path to a file containing the GitHub webhook HMAC secret. Trailing whitespace stripped. |

## `[poll]`

| Field | Type | Required | Description |
|---|---|---|---|
| `default_interval` | duration string | **Yes** | Per-recipe poll cadence default. Recipes can override via `[watch].poll_interval`. Minimum: `1m`. |

## Duration format

Duration values are Go-style human-readable strings:

| Suffix | Unit |
|---|---|
| `ns` | nanoseconds |
| `us`, `µs` | microseconds |
| `ms` | milliseconds |
| `s` | seconds |
| `m` | minutes |
| `h` | hours |

Durations can combine units: `1h30m`, `90m`, `5400s` are all equivalent.

## Strict parsing

Unknown keys at any level are rejected with an error naming the offending key. There is no forward-compatibility allowance for unknown fields — the manager binary is the source of truth for which fields are valid.

This is intentional: misspelt keys silently dropped by the parser would behave like "I forgot to set this," and the result is hard to debug. Strict rejection means a typo fails fast, before the daemon starts.
