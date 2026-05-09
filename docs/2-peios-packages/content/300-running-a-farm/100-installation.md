---
title: Installation
type: how-to
description: Get peipkg-manager (plus its peipkg-build and peipkg-repo dependencies) onto a Linux host as a systemd service.
related:
  - peios-packages/getting-started/set-up-a-build-farm
  - peios-packages/running-a-farm/configuration
---

A build farm is a single host running `peipkg-manager` as a long-lived daemon. The daemon shells out to `peipkg-build` and `peipkg-repo`, so all three binaries need to be on `PATH`.

## Host requirements

Any modern Linux distribution. Tested on Debian 12. Required runtime tools:

- `git` (for source clones and `ls-remote`)
- `bash` (for `build.sh` invocation)
- `coreutils` (for `cp -a`, `find`, `sha256sum`, etc.)
- `rclone` if you're hosting on R2/S3-style object storage

Storage: enough room for the source clones, build outputs, and the published repository state. For the official Peios repo at v1 scale (~100 packages, hundreds of MB each, retention forever), a 50–100 GB volume is sufficient and won't fill up for years. Logs go to systemd's journal; size them per your normal log retention.

Memory: peak usage is bounded by the largest single `.peipkg` (typically ≤100 MB) plus build process overhead. 1–2 GB of RAM is enough; 4 GB is plenty.

## Install the binaries

The three tools each publish a `latest` GitHub release with static `linux-amd64` and `linux-arm64` binaries. They have no shared library dependencies.

```bash
ARCH=$(dpkg --print-architecture 2>/dev/null || uname -m)  # amd64 or arm64
case "$ARCH" in
  x86_64) ARCH=amd64 ;;
  aarch64) ARCH=arm64 ;;
esac

for tool in peipkg-build peipkg-repo peipkg-manager; do
  curl -sSL -o /usr/local/bin/$tool \
    https://github.com/peios/$tool/releases/download/latest/$tool-linux-$ARCH
  chmod +x /usr/local/bin/$tool
done

peipkg-build help
peipkg-repo help
peipkg-manager -h
```

## Create the directory layout

`peipkg-manager` reads from one directory tree and writes to another. By convention:

```
/etc/peipkg-manager/
├── config.toml          # the operator's environment
├── farm.ed25519         # signing key (mode 0600)
├── webhook-secret       # GitHub webhook HMAC secret (mode 0600)
└── recipes/             # one subdirectory per package
    ├── libfoo/
    │   ├── peipkg.toml
    │   └── build.sh
    └── nginx/
        ├── peipkg.toml
        └── build.sh

/var/lib/peipkg-manager/  # state directory; manager owns this
├── sources/             # ephemeral per-build source clones
├── stage/               # ephemeral per-build output dirs
├── publish/             # outputs awaiting peipkg-repo publish
└── repo/                # the published repository state (peipkg-repo's domain)
```

Create the empty layout:

```bash
sudo install -d -o root -g root -m 0755 /etc/peipkg-manager
sudo install -d -o root -g root -m 0755 /etc/peipkg-manager/recipes
sudo install -d -o root -g root -m 0755 /var/lib/peipkg-manager
```

`peipkg-manager` creates the subdirectories of `state_dir` itself on first run, so no need to pre-create `sources/`, `stage/`, etc.

## Generate a signing key

```bash
sudo openssl genpkey -algorithm ed25519 -out /etc/peipkg-manager/farm.ed25519
sudo chmod 600 /etc/peipkg-manager/farm.ed25519
```

The detailed discussion is in [Signing keys](./signing-keys), including how to publish the public-key fingerprint so consumers can add the trust anchor.

## Generate a webhook secret

If you'll be using GitHub webhooks for any recipe, generate a strong random secret:

```bash
openssl rand -hex 32 | sudo tee /etc/peipkg-manager/webhook-secret > /dev/null
sudo chmod 600 /etc/peipkg-manager/webhook-secret
```

The same value goes into each upstream's GitHub webhook configuration.

## Write the config

A minimum `config.toml`:

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

[Configuration](./configuration) is the field-by-field reference.

## Configure rclone (R2 example)

If you're using `[upload].backend = "rclone"`, create the remote rclone will sync to:

```bash
sudo rclone config create r2 s3 \
  provider=Cloudflare \
  endpoint=https://<account-id>.r2.cloudflarestorage.com \
  access_key_id=<key> \
  secret_access_key=<secret>
```

[Hosting on R2](./hosting/r2) covers the bucket, custom domain, and access policies in detail. Other backends are documented as siblings.

## Install the systemd service

```ini
# /etc/systemd/system/peipkg-manager.service
[Unit]
Description=peipkg-manager build farm
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/local/bin/peipkg-manager --config /etc/peipkg-manager/config.toml
Restart=on-failure
RestartSec=10s

# Soft hardening — adjust as appropriate for your threat model.
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
PrivateTmp=true
ReadWritePaths=/var/lib/peipkg-manager

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now peipkg-manager
sudo journalctl -u peipkg-manager -f
```

## Verify

```bash
# Daemon up and listening
curl -fsSL http://localhost:8080/healthz

# Status endpoint shows the loaded recipe roster
curl -fsSL http://localhost:8080/status | jq
```

You should see structured logs scrolling past as `peipkg-manager` polls each recipe's upstream. The first poll for a new repo emits one trigger per upstream tag matching `tag_pattern` — the manager dedups against the (currently empty) archive index, builds anything new, and publishes.

## Where to go from here

- [Configuration](./configuration) — the `peipkg-config.toml` reference, field by field.
- [Signing keys](./signing-keys) — what to do with the key beyond `chmod 600`, and how rotation works.
- [Hosting](./hosting/r2) — pick the backend that fits your situation: R2 (recommended), GitHub Pages (simple), or VPS (full control).
- [Monitoring](./monitoring) — what the `/status` endpoint says and what to alert on.
