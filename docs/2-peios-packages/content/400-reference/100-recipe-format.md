---
title: Recipe Format Reference
type: reference
description: Schema reference for peipkg.toml. The spec appendix is the normative source; this is the operator-friendly view.
related:
  - peios-packages/authoring-recipes/anatomy
  - peios-packages/authoring-recipes/dependencies
---

A recipe is a directory containing `peipkg.toml` and `build.sh`. This page is the schema reference for the TOML file. For the normative spec, see [PSD-009 appendix A.2](../../../specs/psd-009--peipkg/v0.22/8-appendix-a/2-recipe-format).

## Top-level sections

| Section | Owner | Required |
|---|---|---|
| `[meta]` | `peipkg-build` | Yes |
| `[[package]]` | `peipkg-build` | At least one |
| `[upstream]` | `peipkg-manager` | No (recipe is manual-build-only without it) |
| `[watch]` | `peipkg-manager` | No |

Tools tolerate top-level sections they don't own; unknown keys *within* an owned section are typo errors.

## `[meta]`

Shared facts across all stanzas in this recipe.

| Field | Type | Required | Description |
|---|---|---|---|
| `license` | string | Recommended | SPDX identifier or expression. Passed through to manifest. |
| `homepage` | string | Recommended | Upstream homepage URL. Passed through to manifest. |
| `source` | string | Optional | Informational pointer to upstream. Not consumed by tooling — `[upstream]` is what tools read. |
| `build_script` | string | **Yes** | Path to the build script, relative to the recipe directory. Conventional value: `"build.sh"`. |

## `[[package]]`

One stanza per output `.peipkg`. Multiple stanzas allowed; each becomes a separate package.

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | **Yes** | Package name. Conforms to [PSD-009 §2.1](../../../specs/psd-009--peipkg/v0.22/2-identity/1-naming) — lowercase letters, digits, `-`, `+`, `.`. |
| `architecture` | string | **Yes** | Architecture identifier — `noarch` or one of the supported values per [§2.3](../../../specs/psd-009--peipkg/v0.22/2-identity/3-architecture). |
| `description` | string | Recommended | One-line human-readable description. ASCII printable, < 80 characters by convention. |
| `dependencies` | array of dependency objects | Recommended | Required runtime dependencies. |
| `optional_dependencies` | array of dependency objects | Optional | Enhance functionality but not required. |
| `conflicts` | array of dependency objects | Optional | Cannot be installed alongside. |
| `provides` | array of provides objects | Optional | Virtual capabilities this package fulfils. |
| `replaces` | array of replaces objects | Optional | Packages this one supersedes. |
| `side_effects` | array of strings | Optional | Maintenance operations from the [§4.3.4 enumerated list](../../../specs/psd-009--peipkg/v0.22/4-dependencies/3-side-effects). |
| `files` | array of strings | **Yes** | Doublestar globs matching paths under `$DESTDIR/` that this stanza claims. |

### Dependency object

```toml
{ name = "libssl", constraint = ">= 3.0", arch = "any", same_build = false }
```

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | **Yes** | Depended-on package name (or virtual capability). |
| `constraint` | string | Optional | Version constraint per [§2.2.8](../../../specs/psd-009--peipkg/v0.22/2-identity/2-versioning). Operators: `=`, `>`, `>=`, `<`, `<=`, `!=`. Multiple constraints comma-separated. |
| `arch` | string | Optional (default `any`) | Architecture qualifier. Only `any` is currently valid. |
| `same_build` | bool | Optional | Recipe-level shorthand: rewrites `constraint` to `= <this build's version>` at build time. Only valid when `name` refers to a sibling stanza in the same recipe. |

### Provides object

```toml
{ name = "http-server", version = "1.27.0" }
```

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | **Yes** | Virtual capability name. |
| `version` | string | Optional | Version of the capability provided. |

### Replaces object

```toml
{ name = "old-package-name", constraint = "< 2.0" }
```

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | **Yes** | The package this one supersedes. |
| `constraint` | string | Optional | Version constraint. Bare-name (no constraint) replaces any version. |

## `[upstream]`

Read by `peipkg-manager`. Describes where source lives and which tags are versions.

| Field | Type | Required | Description |
|---|---|---|---|
| `git` | string | **Yes** (when `[upstream]` is present) | Upstream Git URL. HTTPS or SSH. |
| `tag_pattern` | string | **Yes** | Regex matching version tags. Must contain exactly one capture group — the captured text is the upstream version. |
| `peios_revision` | integer | **Yes** | The build revision. Combined with the captured upstream version: captured `1.3.2` + revision `1` → package version `1.3.2-1`. Bumped manually when the recipe needs rebuilding without an upstream change. |

## `[watch]`

Read by `peipkg-manager`. Describes how the manager learns about new versions.

| Field | Type | Required | Description |
|---|---|---|---|
| `github_webhook` | bool | Optional (default `false`) | Accept GitHub-format webhooks for this recipe. |
| `poll_interval` | duration string | Optional (default = config's `[poll].default_interval`) | How often to poll upstream's tag list. Format: Go duration (`5m`, `1h`, `24h`). Minimum: `1m`. |

## Strict-vs-loose parsing

Within `[meta]` and `[[package]]`, `peipkg-build` rejects unknown keys as typos:

```toml
[meta]
homepag = "https://typo.example"   # error: unknown key
```

Within `[upstream]` and `[watch]`, `peipkg-manager` does the same. But each tool tolerates *top-level sections it doesn't own*: `peipkg-build` ignores `[upstream]` and `[watch]` entirely; `peipkg-manager` ignores `[meta]` and `[[package]]`.

This is what makes the recipe a shared file format.

## Forward compatibility

Recipes parse forward-compatibly: a future spec version may add new top-level sections (`[provenance]`, `[signing]`, etc.) and tools tolerate unrecognised top-level sections. Fields *within* known sections are validated more strictly; future expansion is via either new sections or explicit `schema_version` bumps.

The current schema is the v0.22 / PSD-009 baseline. Future versions of this specification may relax some "Required" fields and tighten others. Recipes shipped now are expected to remain valid under v1.0.
