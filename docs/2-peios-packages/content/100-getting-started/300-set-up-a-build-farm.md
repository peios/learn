---
title: Set Up a Build Farm
type: how-to
description: Install peipkg-manager on a Linux host, point it at a directory of recipes, and let it watch upstreams and publish packages automatically.
related:
  - peios-packages/getting-started/overview
  - peios-packages/running-a-farm/installation
  - peios-packages/running-a-farm/configuration
---

A build farm in this system is a single long-running process — `peipkg-manager` — running on a Linux host. Give it some recipes, a signing key, and a place to publish, and it watches upstream repositories for new versions and ships packages without further input.

This page is the shortest path from "fresh Debian box" to "official repo populating itself." Each step links to a more detailed page when you need it.

## What you'll set up

A working `peipkg-manager` instance on a Debian host that:

- Reads recipes from `/etc/peipkg-manager/recipes/`.
- Watches each recipe's upstream Git repository for new tags.
- Builds new versions, signs them, and publishes to a local repository state.
- (Optional) Syncs the state to a Cloudflare R2 bucket served as `pkgs.example.org`.

The setup uses one signing key, one rclone remote, and runs `peipkg-manager` as a systemd service. Single host, single architecture. Multi-host coordination is deliberately out of scope.

## Prerequisites

A Linux host (Debian 12 or similar) with:

- `git`, `bash`, `coreutils`
- `rclone` (for R2/S3 hosting; skip if hosting on GitHub Pages or a VPS via rsync)
- A persistent state directory (defaults to `/var/lib/peipkg-manager`)
- An Ed25519 signing key you control

You'll also need to create a GitHub repo for your *recipes* (the directory of `peipkg.toml` + `build.sh` files). The farm reads from this repo; new package additions or recipe fixes go through pull requests against it.

## Install the binaries

The farm shells out to `peipkg-build` and `peipkg-repo`, so all three need to be on `PATH`:

```bash
for tool in peipkg-build peipkg-repo peipkg-manager; do
  curl -sSL -o /usr/local/bin/$tool \
    https://github.com/peios/$tool/releases/download/latest/$tool-linux-amd64
  chmod +x /usr/local/bin/$tool
done
```

Verify:

```bash
peipkg-build help && peipkg-repo help && peipkg-manager -h
```

## Generate a signing key

```bash
mkdir -p /etc/peipkg-manager
openssl genpkey -algorithm ed25519 -out /etc/peipkg-manager/farm.ed25519
chmod 600 /etc/peipkg-manager/farm.ed25519
```

> [!WARNING]
> This is the only key signing the entire repository. Compromise of this file means every package the farm publishes can be forged. Store it on disk only — never in environment variables, container images, or shell history. Back it up offline if you want to be able to recover from a wiped host without users having to add a new trust anchor.

[Signing keys](../running-a-farm/signing-keys) covers custody and rotation.

## Drop in some recipes

Recipes live under `/etc/peipkg-manager/recipes/`, one directory per package:

```
/etc/peipkg-manager/recipes/
├── libfoo/
│   ├── peipkg.toml
│   └── build.sh
└── nginx/
    ├── peipkg.toml
    └── build.sh
```

A minimal recipe with auto-tracking enabled:

```toml
[meta]
license = "Zlib"
homepage = "https://zlib.net"
build_script = "build.sh"

[[package]]
name = "libz"
architecture = "x86_64"
description = "zlib compression library — runtime"
side_effects = ["ldconfig"]
files = [
  "usr/lib/x86_64-linux-peios/libz.so.1",
  "usr/lib/x86_64-linux-peios/libz.so.1.*",
]

[upstream]
git = "https://github.com/madler/zlib"
tag_pattern = "^v(\\d+\\.\\d+\\.\\d+)$"
peios_revision = 1

[watch]
github_webhook = true
poll_interval = "1h"
```

The `[meta]` and `[[package]]` sections are what `peipkg-build` consumes. The `[upstream]` and `[watch]` sections are what `peipkg-manager` reads to know how to detect new versions.

[Anatomy of a recipe](../authoring-recipes/anatomy) covers each section in detail.

## Write the manager config

```toml
# /etc/peipkg-manager/config.toml
[manager]
id = "peios-build-1"
recipes_dir = "/etc/peipkg-manager/recipes"
state_dir = "/var/lib/peipkg-manager"

[repo]
name = "my-peios-repo"
description = "My Peios package repository"

[signing]
key_file = "/etc/peipkg-manager/farm.ed25519"

[upload]
backend = "rclone"
remote = "r2:pkgs.example.org"

[http]
addr = ":8080"
webhook_secret_file = "/etc/peipkg-manager/webhook-secret"

[poll]
default_interval = "1h"
```

The `[upload]` section is optional. If you set `backend = "none"`, `peipkg-manager` produces a local repo state at `<state_dir>/repo/` and stops there — your own scripts can rsync or git-push it elsewhere.

[Configuration](../running-a-farm/configuration) is the field-by-field reference.

## Configure rclone (R2 example)

If you're hosting the official repo on Cloudflare R2:

```bash
rclone config create r2 s3 \
  provider=Cloudflare \
  endpoint=https://<account-id>.r2.cloudflarestorage.com \
  access_key_id=<key> \
  secret_access_key=<secret>
```

Test it:

```bash
rclone lsd r2:pkgs.example.org
```

[Hosting on R2](../running-a-farm/hosting/r2) covers the R2 setup including the custom domain. Other backends are documented under the same section.

## Run the daemon

For a one-off test (no daemon, no webhooks):

```bash
peipkg-manager --config /etc/peipkg-manager/config.toml --once
```

This polls every recipe once, builds anything new, publishes, optionally uploads, and exits. Good for "did I configure this right?"

For production, install it as a systemd service:

```ini
# /etc/systemd/system/peipkg-manager.service
[Unit]
Description=peipkg-manager build farm
After=network-online.target

[Service]
Type=simple
ExecStart=/usr/local/bin/peipkg-manager --config /etc/peipkg-manager/config.toml
Restart=on-failure
RestartSec=10s

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl enable --now peipkg-manager
journalctl -u peipkg-manager -f
```

You should see structured log lines for each recipe getting polled, builds starting, and publishes completing.

## Watch it work

Once running, `peipkg-manager` will:

- Poll each recipe's upstream at the configured interval (default 1h).
- Receive GitHub webhooks at `:8080/webhooks/github` if you set up the webhook in your upstream's GitHub settings.
- Detect any tag matching the recipe's `tag_pattern` that isn't already in the repository's archive index.
- Clone the source, build, sign, publish, sync.
- Skip versions that are already published. Skip versions that recently failed (exponential backoff).

You can ask the daemon what it's doing at any time:

```bash
curl http://localhost:8080/status | jq
```

```json
{
  "farm_id": "peios-build-1",
  "recipes": ["libz", "nginx"],
  "builds_attempted": 5,
  "builds_succeeded": 4,
  "in_flight": null,
  "failures": {
    "nginx@1.27.0-1": {"failures": 2, "next_retry": "2026-05-07T14:32:00Z"}
  }
}
```

[Monitoring](../running-a-farm/monitoring) covers the `/status` schema and what to alert on.

## Where to go from here

- **Add more packages.** Drop more recipe directories under `recipes_dir`, send the daemon a SIGHUP, and they get picked up.
- **Set up GitHub webhooks** so new tags trigger builds within seconds instead of waiting for the next poll. The `[http].webhook_secret_file` is what GitHub signs payloads with.
- **Audit your repository.** `peipkg-repo verify --repo /var/lib/peipkg-manager/repo --mode both --all-packages-dir <dir>` re-hashes every published `.peipkg` and confirms the indexes are intact.
- **Read [Authoring recipes](../authoring-recipes/anatomy)** if you'll be writing the recipes yourself.
