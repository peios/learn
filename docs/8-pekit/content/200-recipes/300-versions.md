---
title: Versions
type: concept
description: "How pekit parses version strings, selects which versions to build with --version, --latest, and --all-versions, and renders version components into sources and packages."
related:
  - pekit/recipes/sources
  - pekit/recipes/anatomy
  - pekit/recipes/packages
  - pekit/using-pekit/invocation
  - pekit/reference/cli
  - pekit/reference/supporting-files
---

A pekit build is almost always **about a version** of some upstream software. The
recipe declares where source of a given version comes from and how to name the
packages it produces; the invocation decides *which* versions are in scope. This
page covers the version grammar pekit accepts, the `{{...}}` variables that carry
version components into your recipe, and how the `--version`, `--latest`, and
`--all-versions` selectors resolve against a source.

## Version forms

A version is written as:

```text
MAJOR[.MINOR[.PATCH]][-PRERELEASE][+BUILDMETA]
```

Only `MAJOR` is mandatory. Minor and patch are each optional but ordered — you
cannot write a patch without a minor. The optional `-PRERELEASE` and `+BUILDMETA`
tails may each contain digits, ASCII letters, dots, and hyphens.

| Written version    | major | minor | patch | prerelease | buildmeta |
| ------------------ | ----- | ----- | ----- | ---------- | --------- |
| `2`                | `2`   |       |       |            |           |
| `2.43`             | `2`   | `43`  |       |            |           |
| `2.43.1`           | `2`   | `43`  | `1`   |            |           |
| `1.21.0-rc.1`      | `1`   | `21`  | `0`   | `rc.1`     |           |
| `1.21.0+build.5`   | `1`   | `21`  | `0`   |            | `build.5` |
| `1.21.0-rc.1+bld`  | `1`   | `21`  | `0`   | `rc.1`     | `bld`     |

Anything that does not match this grammar is rejected with an `invalid_version`
error. Comparison and ordering are numeric on major/minor/patch (a missing
component counts as `0`), with the prerelease string compared lexically to break
ties.

## Version template variables

Six variables expose the parsed components of the selected version. They render
anywhere pekit expands `{{...}}` templates in a recipe — most importantly in
[source](~pekit/recipes/sources) refs and URLs, and in
[package](~pekit/recipes/packages) version and metadata fields. (These six are
the version-derived subset of the template engine; the complete variable table,
including the multi-package-only `{{multipack}}`, is in
[Supporting files](~pekit/reference/supporting-files).)

| Variable          | Expands to                       |
| ----------------- | -------------------------------- |
| `{{version}}`     | the version exactly as written   |
| `{{major}}`       | the major component              |
| `{{minor}}`       | the minor component              |
| `{{patch}}`       | the patch component              |
| `{{prerelease}}`  | the prerelease tail, or empty    |
| `{{buildmeta}}`   | the build-metadata tail, or empty |

```toml
[source.git]
url = "https://github.com/example/tool.git"
ref = "v{{version}}"
```

Two rules govern rendering:

- **Referencing a component the version does not have is an error.** `{{version}}`
  fails when no version is selected at all; `{{minor}}` and `{{patch}}` fail when
  the selected version stops short of that component (for example `{{patch}}`
  against `2.43`). `{{prerelease}}` and `{{buildmeta}}` are the exception — they
  render as empty text when absent rather than erroring.
- **Unknown variables are an error.** Any `{{name}}` that is not one of the six
  above (or the multi-package `{{multipack}}` token) is rejected. There is no
  silent pass-through.

> Version variables do **not** apply to shell target commands. A `command`
> in a build/test/install target receives version data through the
> `PEKIT_VERSION`, `PEKIT_VERSION_MAJOR`, `PEKIT_VERSION_MINOR`,
> `PEKIT_VERSION_PATCH`, `PEKIT_VERSION_PRERELEASE`, and
> `PEKIT_VERSION_BUILDMETA` environment variables instead — see
> [recipe anatomy](~pekit/recipes/anatomy).

## Selecting versions

Three mutually exclusive flags choose the version set. Supplying more than one is
rejected with `--version, --latest, and --all-versions are mutually exclusive`.

| Flag                    | Selects                                                        | Needs an enumerable source? |
| ----------------------- | ------------------------------------------------------------- | --------------------------- |
| `--version <selector>`  | exact version(s), or a semver constraint                      | only for constraints        |
| `--latest`              | the single highest available version                          | yes                         |
| `--all-versions`        | every available version                                       | yes                         |
| *(none)*                | an unversioned build (no `{{version}}` available)             | no                          |

**Enumerable sources** are those pekit can list versions for: a `[source.git]`
source (via `git ls-remote --tags`) or a `[source.url]` source (by fetching the
listing directory). `--latest`, `--all-versions`, and any constraint require one;
against a non-enumerable source they fail with `selected source cannot enumerate
versions`.

### `--version` as an exact selector

The simplest form is one or more exact versions, comma-separated:

```text
pekit build tool --version 2.43.1
pekit build tool --version 2.43.1,2.42.0
```

A comma-separated list without spaces is treated as a set of exact versions. When
the source is reproducible and enumerable, each written version is matched
against the versions the source actually publishes using the trailing-zero ladder
described below.

### `--version` as a constraint

A `--version` value that contains a space or a comparison operator
(`<`, `>`, `=`, `<=`, `>=`) is treated as a **constraint** and takes the
enumeration path. Constraints filter the enumerated set:

```text
pekit build tool --version ">= 2.40"
pekit build tool --version ">= 2.40, < 3.0"
```

Multiple constraints (comma- or space-separated) are ANDed together. The `~` and
`^` operators are **not** supported and produce
`unsupported version constraint operator`. A bare `*` matches everything.

### `--latest` and `--all-versions`

```text
pekit build tool --latest          # highest available version only
pekit package tool --all-versions  # every available version
```

`--latest` picks the single greatest version after enumeration and filtering.
`--all-versions` selects the whole set.

## The trailing-zero ladder

Upstreams are inconsistent about trailing zeros: one project tags `v2.43.0`,
another tags `v2.43`, a third tags `v2`. So when you ask for an exact version
against a reproducible, enumerable source, pekit does not demand a character-exact
tag. It builds a ladder of candidates from your written version, most specific
first, and picks the first candidate the source actually offers:

| You write | Candidates tried, in order |
| --------- | -------------------------- |
| `2.43.0`  | `2.43.0`, then `2.43`      |
| `2.0.0`   | `2.0.0`, then `2.0`, then `2` |
| `2.0`     | `2.0`, then `2`            |
| `2.43.1`  | `2.43.1` only              |

Only trailing **zero** components are dropped — a non-zero patch or minor is never
elided. The ladder is also **skipped entirely** when the version carries a
prerelease or build-metadata tail: `1.21.0-rc.1` is only ever matched as written.
If no candidate is available (or the source is not reproducible/enumerable), the
version you wrote is used verbatim.

The ladder applies to the exact-selector path only. `--latest`,
`--all-versions`, and constraints work on the enumerated set directly and do not
ladder.

## Source version caps

A source can declare a hard ceiling (or floor) on the versions a recipe will ever
build, independent of what the invocation asks for. Set `versions` under the
source table:

```toml
[source.git]
url = "https://github.com/example/tool.git"
ref = "v{{version}}"
versions = ">= 1.0, < 3.0"
```

The cap uses the same constraint grammar as `--version`. It is applied on both
paths:

- On the enumeration path (`--latest`, `--all-versions`, constraints) the cap
  filters the available set *before* the selector runs, so `--latest` returns the
  highest version *within* the cap.
- On the exact-selector path the cap filters the versions you named. If every
  named version falls outside the cap the build fails with `selected exact
  versions were filtered out by source version cap`.

An empty result after capping is always an error — a cap that excludes everything
is treated as a misconfiguration, not a no-op.

## Local builds

When the [source](~pekit/recipes/sources) resolves to a local directory, there is
nothing to enumerate. Local sources therefore require an **exact** `--version`;
`--latest`, `--all-versions`, and constraints fail with `local sources require an
exact --version`.

If you build locally without giving a `--version` at all, pekit stamps the build
with the sentinel version **`0.0.0-localdev`** so that `{{version}}` and the
`PEKIT_VERSION*` variables still resolve. This makes local development builds work
without inventing a version number, while keeping them clearly distinguishable
from real releases.

## Single-version commands

`build`, `package`, and `publish` operate on many versions at once — pass
`--all-versions` and pekit plans one build per version.

`test` and `install` do not. They require the selector to resolve to **exactly
one** version; if it resolves to more, the command fails with `test requires a
single resolved version` (or `install requires ...`). Use an exact `--version` or
`--latest` for these commands.

## Where to go next

For where a selected version's source tree comes from, read [Sources](~pekit/recipes/sources).

For how version components render into package names and metadata, read [Packaging files](~pekit/recipes/packages).

For the full flag surface behind `--version`, `--latest`, and `--all-versions`, read [Invocation and flags](~pekit/using-pekit/invocation).
