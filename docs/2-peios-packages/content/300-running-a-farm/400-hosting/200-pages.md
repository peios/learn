---
title: Hosting on GitHub Pages
type: how-to
description: Use GitHub Pages plus Releases as a free, low-friction host for a third-party Peios repository. Better suited to small/medium repos than the official one.
related:
  - peios-packages/running-a-farm/configuration
  - peios-packages/running-a-farm/hosting/r2
---

GitHub Pages is the simplest option for a third-party repository: zero infrastructure, free hosting, automatic HTTPS, and a custom domain if you want one. It works well up to a point — at the official-Peios scale R2 is a better fit, but for small-to-medium repos (a handful of curated packages, internal/team-scoped distributions) Pages is the path of least resistance.

This page covers the layout that makes Pages work despite its constraints, and the publishing workflow.

## What Pages can and can't do

Pages serves static files from a Git branch. That works fine for the small files (`repo.json`, `index/*.json`, key files). It doesn't work well for `.peipkg` files because:

- Pages has a 1 GB **soft** limit and 100 GB **hard** limit on repository size. Binary blobs in git history bloat the repo; even at modest scale you'll hit the soft limit within a few months.
- Pages has fair-use bandwidth limits. A popular repo serving binaries straight from Pages will get throttled.
- Pages doesn't support server-side redirects, which means workarounds like "host the index here, redirect to a CDN there" don't work.

The way around this: **use GitHub Releases for the binaries**. Releases storage isn't counted against repo size, individual assets up to 2 GB, no hard repo cap. Indexes still go on Pages; per-package URLs in the index point at Release assets.

## The split layout

```
github.com/yourorg/your-repo/   ← serves Pages from the `gh-pages` branch
├── repo.json
├── repo.json.sig
├── keys/
│   └── <fingerprint>.pub
└── index/
    ├── active.json
    ├── active.json.sig
    ├── archive.json
    └── archive.json.sig

github.com/yourorg/your-repo/releases/   ← `.peipkg` files as Release assets
├── <some-tag>/
│   ├── nginx_1.27.0-1_x86_64.peipkg
│   ├── libfoo_1.2.3-1_x86_64.peipkg
│   └── ...
```

`repo.json`'s index URLs are conventional (`/index/active.json` etc.). Per-package URLs in the index point absolutely at the Release URLs (`https://github.com/yourorg/your-repo/releases/download/...`).

## Configure peipkg-manager

```toml
# peipkg-config.toml
[upload]
backend = "none"   # peipkg-manager produces the local state; we publish it ourselves
```

`backend = "none"` means `peipkg-manager` writes its repo state to `<state_dir>/repo/` and stops. A wrapper script handles the actual upload.

The recipe needs a custom URL template per package so the index references Release URLs:

```toml
# in each recipe's peipkg.toml or via peipkg-repo's --package-url-template flag
# (the recipe doesn't carry this — it's a publish-time concern; see below)
```

## The publishing flow

The wrapper script runs after `peipkg-manager` finishes a sweep, or as part of CI on the recipes repo:

```bash
#!/bin/sh
set -eu
STATE_DIR=/var/lib/peipkg-manager
REPO_DIR=$STATE_DIR/repo
RELEASE_TAG=pkgs-$(date -u +%Y%m%d%H%M%S)

# 1. Upload .peipkg files as Release assets, with absolute URLs that the
#    index will reference.
PEIPKGS=$(find "$STATE_DIR/publish" -name '*.peipkg' 2>/dev/null)
if [ -n "$PEIPKGS" ]; then
  gh release create "$RELEASE_TAG" $PEIPKGS \
    --title "Package release $RELEASE_TAG" \
    --notes "Automated release"
fi

# 2. Re-run peipkg-repo publish with the URL template pointing at the new Release.
RELEASE_URL_BASE="https://github.com/yourorg/your-repo/releases/download/$RELEASE_TAG"
peipkg-repo publish \
  --in "$REPO_DIR" \
  --new "$STATE_DIR/publish" \
  --out "$REPO_DIR" \
  --sign-key /etc/peipkg-manager/farm.ed25519 \
  --timestamp "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --package-url-template "$RELEASE_URL_BASE/{filename}"

# 3. Push the index files to gh-pages.
cd /tmp/pages
rsync -a --delete "$REPO_DIR/" .
git add -A
git commit -m "publish: $RELEASE_TAG"
git push origin gh-pages
```

> [!NOTE]
> This is more complex than the R2 case because `peipkg-manager`'s v0 doesn't have a "Pages-aware" upload backend. The shell-script wrapper effectively becomes part of the build farm; the alternative is contributing a Pages backend to `peipkg-manager`, which is a reasonable next feature.

## Custom domain

You can serve Pages at `pkgs.example.org` instead of `yourorg.github.io/your-repo/`:

1. In the repo's "Settings" → "Pages", set "Custom domain" to `pkgs.example.org`.
2. Add a CNAME record on your DNS pointing `pkgs.example.org` to `yourorg.github.io`.
3. Wait for cert provisioning.

The custom domain doesn't change anything about how peipkg-manager publishes — `repo.json` is at `https://pkgs.example.org/repo.json` regardless.

## When to migrate off Pages

Pages is fine until you hit one of:

- Repo size approaches the 1 GB soft limit (your index growth is normal but lots of historical packages are accumulating in old Releases).
- Bandwidth fair-use throttling (you have enough users that GitHub starts noticing).
- You need cache headers you can control (Pages sets defaults you can't override per file).

When that happens, R2 is the natural next step — the layout (`<repo-base>/repo.json`, `index/`, `keys/`) is the same; you only swap the backend.
