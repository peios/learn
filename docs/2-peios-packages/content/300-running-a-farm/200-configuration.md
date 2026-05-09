---
title: Configuration
type: reference
description: The peipkg-config.toml reference. Every field, what it does, and what happens when you leave it out.
related:
  - peios-packages/running-a-farm/installation
  - peios-packages/reference/config-format
---

`peipkg-manager` reads its configuration from a single TOML file passed via `--config`. By convention the path is `/etc/peipkg-manager/config.toml`.

The config has six sections: `[manager]`, `[repo]`, `[signing]`, `[upload]`, `[http]`, `[poll]`. Each is documented below.

## A complete example

```toml
[manager]
id = "peios-build-1"
recipes_dir = "/etc/peipkg-manager/recipes"
state_dir = "/var/lib/peipkg-manager"

[repo]
name = "peios-official"
description = "Official Peios package repository"

[signing]
key_file = "/etc/peipkg-manager/farm.ed25519"

[upload]
backend = "rclone"
remote = "r2:pkgs.peios.org"

[http]
addr = ":8080"
webhook_secret_file = "/etc/peipkg-manager/webhook-secret"

[poll]
default_interval = "1h"
```

## `[manager]`

Identity and disk layout for the daemon itself.

| Field | Required | Description |
|---|---|---|
| `id` | Yes | The build farm's identifier. Recorded in every package's `manifest.build.farm_id` ([PSD-009 §3.3.4](../../../specs/psd-009--peipkg/v0.22/3-format/3-manifest)). Use a stable string like `peios-build-1`. |
| `recipes_dir` | Yes | Directory containing one subdirectory per package. Each subdirectory must contain a `peipkg.toml`; subdirectories without one are silently ignored, so it's safe to keep notes or scratch directories alongside. |
| `state_dir` | Yes | Manager's writable working area. Subdirectories `sources/`, `stage/`, `publish/`, and `repo/` are created on first run. |

## `[repo]`

The repository's identity. Used at first-run init only — once the repository state exists at `<state_dir>/repo/`, these values come from `repo.json` and changing the config doesn't change the published descriptor.

| Field | Required | Description |
|---|---|---|
| `name` | Yes | Recorded in `repo.json`'s `repo.name`. Should be kebab-case ([PSD-009 §6.1.2](../../../specs/psd-009--peipkg/v0.22/6-repository/1-descriptor)). |
| `description` | No | Human-readable one-line description. Empty string if omitted. |

> [!NOTE]
> If you need to change `repo.name` after the repository has been initialised, edit `repo.json` directly and re-sign with `peipkg-repo` (the descriptor is signed independently of the indexes; see the [CLI reference](../reference/cli-peipkg-repo)).

## `[signing]`

The Ed25519 private key that signs every package and every published index/descriptor.

| Field | Required | Description |
|---|---|---|
| `key_file` | Yes | Path to the key on disk. Either a 32-byte raw seed or a PEM-encoded PKCS#8 `PRIVATE KEY` block ([PSD-009 §5.2.2](../../../specs/psd-009--peipkg/v0.22/5-signing/2-key-management)). |

The file must be readable by the daemon's user. Mode 0600 is recommended.

[Signing keys](./signing-keys) discusses generation, custody, and rotation.

## `[upload]`

Where to publish the repository state after each successful publish.

| Field | Required | Description |
|---|---|---|
| `backend` | No (default `none`) | One of `rclone`, `none`. `none` (or omitting the section) leaves the published state at `<state_dir>/repo/` and stops there — your own scripts can sync it elsewhere. |
| `remote` | Required when `backend = "rclone"` | An rclone remote and path, e.g., `r2:pkgs.peios.org`. Must exist in rclone's config (`rclone config show <remote>`). |

When `backend = "rclone"`, the daemon runs `rclone sync <state_dir>/repo/ <remote>` after every successful `peipkg-repo publish`.

[Hosting on R2](./hosting/r2) covers the rclone setup. For GitHub Pages or VPS deployments, set `backend = "none"` and run your own sync logic from a wrapper script — see [Hosting on Pages](./hosting/pages) or [Hosting on a VPS](./hosting/vps).

## `[http]`

The optional HTTP server. Powers webhook reception and the `/status` endpoint. Setting `addr = ""` disables the HTTP server entirely; polling becomes the only watch mechanism.

| Field | Required | Description |
|---|---|---|
| `addr` | No (default `""`) | Listen address, e.g., `:8080`, `127.0.0.1:8080`, `0.0.0.0:8080`. Empty disables HTTP. |
| `webhook_secret_file` | Required when `addr` is set and any recipe uses `github_webhook = true` | Path to a file containing the HMAC SHA-256 secret GitHub uses to sign webhook payloads. |

The webhook secret file's contents are taken as-is, with trailing whitespace (including newlines) stripped. Keep the same value in your GitHub webhook configuration.

The HTTP server exposes three endpoints:

- `GET /healthz` — always returns `200 ok`. For readiness checks.
- `GET /status` — JSON status report. See [Monitoring](./monitoring).
- `POST /webhooks/github` — webhook receiver. HMAC-verified.

## `[poll]`

Default polling cadence for recipes.

| Field | Required | Description |
|---|---|---|
| `default_interval` | Yes | How often each recipe gets polled if its own `[watch].poll_interval` is unset. Format: human-readable Go duration (`5m`, `1h`, `24h`). Minimum: `1m`. |

Each recipe can override its own poll interval via `[watch].poll_interval`. The default is the floor — recipes opt to go faster, never slower.

> [!CAUTION]
> Aggressive polling against public hosts (GitHub, GitLab, sourcehut) is rate-limited. `5m` polls against ~50 recipes will get you blocked from GitHub's `git-upload-pack` for an hour. The default `1h` is plenty for most workloads; if you need lower latency, set up GitHub webhooks for that recipe instead of polling more often.

## What's not in the config

Some things are deliberately not config-driven:

- **The recipes themselves.** Each recipe's `[upstream]` and `[watch]` blocks live in the recipe, not in the manager config. Adding a new package = drop a recipe directory under `recipes_dir` and (optionally) reload the daemon.
- **TLS for the HTTP listener.** `peipkg-manager`'s HTTP server is plain HTTP. Put it behind a reverse proxy (caddy, nginx) for TLS. Webhook endpoints typically don't need to be public — point the upstream's webhook at a tunnelled or internal address.
- **Build sandboxing.** v0 trusts the host. The threat model is "operator typos break things"; if you need stronger isolation (e.g., for third-party recipe submissions), run `peipkg-manager` inside a container or VM.

## Reloading

Send `SIGHUP` to the daemon to reload recipes:

```bash
systemctl reload peipkg-manager
```

(`Reload=` isn't currently wired into the systemd unit — `systemctl reload` is equivalent to `kill -HUP <pid>`.)

The webhook secret and signing key are read on startup; changing those requires a full restart.
