---
title: Tracking Upstream Versions
type: how-to
description: How [upstream] and [watch] sections tell peipkg-manager where source lives and how to recognise new versions, so the recipe stays stable while versions roll forward automatically.
related:
  - peios-packages/authoring-recipes/anatomy
  - peios-packages/running-a-farm/configuration
---

A recipe's `[upstream]` and `[watch]` sections are what makes the build farm autonomous. They describe where source lives, which tags are versions, and how often to look for new ones. Once written, a recipe rarely changes again — new versions of upstream just get picked up.

Both sections are read by `peipkg-manager`. `peipkg-build` ignores them.

## `[upstream]` — where source lives

```toml
[upstream]
git = "https://github.com/madler/zlib"
tag_pattern = "^v(\\d+\\.\\d+\\.\\d+)$"
peios_revision = 1
```

Three fields:

| Field | Purpose |
|---|---|
| `git` | The Git URL to clone source from. HTTPS or SSH. |
| `tag_pattern` | A regular expression matching the upstream tags that represent versions. Must contain exactly one capture group, which `peipkg-manager` extracts as the version string. |
| `peios_revision` | The build-revision counter. Combined with the captured upstream version to produce the package version: e.g. captured `"1.3.2"` plus revision `1` → `1.3.2-1`. |

When `peipkg-manager` polls or receives a webhook, it lists all of upstream's tags, applies `tag_pattern`, and considers any matching tag a candidate version.

> [!TIP]
> Test your regex before committing. The `tag_pattern` must match exactly the tags you want; `^v(\d+\.\d+\.\d+)$` matches `v1.3.2` but not `v1.3.2-rc.1` (which is good — pre-releases shouldn't auto-publish) and not `release-1.3.2` (which is bad if upstream uses that scheme).

### When to bump `peios_revision`

`peios_revision` exists to handle "rebuild same upstream version with different inputs."

You bump it when:

- The build script changed (a fix, a config flag tweak).
- A patch was applied to source that wasn't there before.
- A dependency you compile against changed (new ABI of a sibling package).

You do not bump it for new upstream tags — the upstream version covers that.

When you bump `peios_revision`, the recipe goes from `peios_revision = 1` to `peios_revision = 2`, and existing already-published versions get rebuilt at the new revision. New versions inherit the new revision.

## `[watch]` — how the manager learns about new versions

```toml
[watch]
github_webhook = true
poll_interval = "1h"
```

Two fields, both optional:

| Field | Purpose |
|---|---|
| `github_webhook` | When `true`, this recipe accepts GitHub-format webhooks at the build farm's `/webhooks/github` endpoint. The HMAC SHA-256 secret is verified against `[http].webhook_secret_file` from the manager's config. |
| `poll_interval` | How often `peipkg-manager` polls upstream's `git ls-remote --tags` for this recipe. Defaults to the manager's `[poll].default_interval` if absent. |

Polling and webhooks are complementary, not alternative. Polling is the always-on baseline that catches versions even when webhooks miss (network blip, GitHub Actions outage, recipe added before the webhook was configured). Webhooks are the latency improvement: an upstream tag pushed at 14:00 doesn't wait until the next 1-hour tick.

### Setting up the webhook on GitHub

In your upstream-mirror's GitHub settings → Webhooks → Add webhook:

- **Payload URL:** `https://<your-farm>/webhooks/github`
- **Content type:** `application/json`
- **Secret:** the contents of the file referenced by `[http].webhook_secret_file` in your `peipkg-config.toml`
- **Events:** "Just the push event" (tag pushes are part of push events)

The build farm's webhook handler verifies the HMAC SHA-256 signature on every incoming request. Unsigned or wrongly-signed requests are rejected with HTTP 401 and logged.

> [!NOTE]
> If you operate the build farm but don't control the upstream repo, you can't set up the GitHub webhook. Polling at a short interval (e.g., `15m`) is the alternative. Don't go below `5m` against public hosts; you'll hit GitHub's rate limit and `git ls-remote` will start refusing your queries.

## Recipes without `[upstream]`

A recipe that omits `[upstream]` loads cleanly but is not auto-watched. `peipkg-manager` skips it. The recipe is still buildable manually:

```bash
peipkg-build build --recipe path/to/peipkg.toml --version 1.0-1 ...
```

This is the right shape for packages that aren't tied to an upstream Git repo — internal first-party software, repackaged tarball releases, or packages you only ever build by hand.

## What stays in the recipe vs what doesn't

The `[upstream]` block describes the upstream as a *stable property* of the recipe: this package is sourced from this git URL with this tag scheme. That doesn't change unless upstream moves or restructures their tags.

What does NOT live in the recipe:

- The current version. The build farm derives it from the latest matching tag.
- The signing key. Lives in the build farm's config; the recipe doesn't know how packages get signed.
- The build farm's URL. Same — operational, not authorial.

This separation is why a recipes repository can have one PR per *capability change* (a new package, a build-script fix) rather than one PR per release. Routine version updates touch nothing.
