---
title: Versions
type: concept
description: "The version grammar, the --version/--latest/--all-versions selectors, the trailing-zero ladder, source version caps, and the version template variables."
related:
  - pekit/recipes/sources
  - pekit/recipes/anatomy
  - pekit/recipes/packages
  - pekit/running/invocation
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
NUMERIC_COMPONENT[.NUMERIC_COMPONENT...][SUFFIX][-PRERELEASE][+BUILDMETA]
```

The numeric core contains one or more dot-separated decimal components. An
optional unseparated `SUFFIX` starts with an ASCII letter and continues with
ASCII letters or digits; this covers upstream schemes such as IANA tzdata's
`2026c`. The optional `-PRERELEASE` and `+BUILDMETA` tails may each contain
digits, ASCII letters, dots, and hyphens.

| Written version    | major | minor | patch | complete numeric core | suffix | prerelease | buildmeta |
| ------------------ | ----- | ----- | ----- | --------------------- | ------ | ---------- | --------- |
| `2`                | `2`   |       |       | `2`                   |        |            |           |
| `2026c`            | `2026`|       |       | `2026`                | `c`    |            |           |
| `2.43`             | `2`   | `43`  |       | `2.43`                |        |            |           |
| `2.43.1`           | `2`   | `43`  | `1`   | `2.43.1`              |        |            |           |
| `0.5.13.5`         | `0`   | `5`   | `13`  | `0.5.13.5`            |        |            |           |
| `1.21.0-rc.1`      | `1`   | `21`  | `0`   | `1.21.0`              |        | `rc.1`     |           |
| `1.21.0+build.5`   | `1`   | `21`  | `0`   | `1.21.0`              |        |            | `build.5` |
| `1.21.0-rc.1+bld`  | `1`   | `21`  | `0`   | `1.21.0`              |        | `rc.1`     | `bld`     |

Anything that does not match this grammar is rejected with an `invalid_version`
error. Comparison and ordering use every numeric component, without a
machine-integer size limit. A missing component counts as `0`, so `1.2`,
`1.2.0`, and `1.2.0.0` have equal numeric cores. Suffixes sort after the
matching bare numeric core and lexically among themselves (`2026 < 2026a <
2026b`); the prerelease string then breaks ties. Build metadata does not affect
ordering.

## Version template variables

Nine variables expose the parsed components of the selected version. They render
anywhere pekit expands `{{...}}` templates in a recipe — most importantly in
[source](~pekit/recipes/sources) refs and URLs, and in
[package](~pekit/recipes/packages) version and metadata fields. (These nine are
the version-derived subset of the template engine; the complete variable table,
including the multi-package-only `{{multipack}}`, is in
[Supporting files](~pekit/reference/supporting-files).)

| Variable          | Expands to                       |
| ----------------- | -------------------------------- |
| `{{version}}`     | the version exactly as written   |
| `{{major}}`       | the first numeric component      |
| `{{minor}}`       | the second numeric component     |
| `{{patch}}`       | the third numeric component      |
| `{{revision}}`    | the fourth numeric component, or empty |
| `{{revision_suffix}}` | `-rev` plus the fourth component, or empty |
| `{{suffix}}`      | the unseparated suffix, or empty |
| `{{prerelease}}`  | the prerelease tail, or empty    |
| `{{buildmeta}}`   | the build-metadata tail, or empty |

```toml
[source.git]
url = "https://github.com/example/tool.git"
ref = "v{{version}}"
```

Three rules govern rendering:

- **The fourth numeric component is also available as a corrective revision.**
  The first three component variables retain their compatibility meanings.
  For example, `2026.02.10.1` renders unchanged through `{{version}}`, exposes
  `1` through `{{revision}}`, and renders `-rev1` through
  `{{revision_suffix}}`. Fifth and later components remain available only
  through `{{version}}`.

- **Referencing a component the version does not have is an error.** `{{version}}`
  fails when no version is selected at all; `{{minor}}` and `{{patch}}` fail when
  the selected version stops short of that component (for example `{{patch}}`
  against `2.43`). `{{suffix}}`, `{{prerelease}}`, and `{{buildmeta}}` are the
  exception — they render as empty text when absent rather than erroring.
  `{{revision}}` and `{{revision_suffix}}` behave the same way.
- **Unknown variables are an error.** Any `{{name}}` that is not one of the nine
  above (or the multi-package `{{multipack}}` token) is rejected. There is no
  silent pass-through.

> [!IMPORTANT]
> Version variables do **not** apply to shell target commands. A `command`
> in a build/test/install target receives version data through the
> `PEKIT_VERSION`, `PEKIT_VERSION_MAJOR`, `PEKIT_VERSION_MINOR`,
> `PEKIT_VERSION_PATCH`, `PEKIT_VERSION_SUFFIX`, `PEKIT_VERSION_PRERELEASE`, and
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

**Enumerable sources** are those pekit can list versions for: an ordinary
`[source.git]` source (via `git ls-remote --tags`), a tracked-path git source
(from matching lock history plus a changed blob at its fixed ref), a
`[source.url]` source (by fetching the
listing directory), or a `[source.pypi]` source (from the project's JSON Simple
API page). `--latest`, `--all-versions`, and any constraint require one;
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
| `2.43.7.0.0` | `2.43.7.0.0`, then `2.43.7.0`, then `2.43.7` |

Only trailing **zero** components are dropped — a non-zero component is never
elided. The ladder works across any number of numeric components. It is also
**skipped entirely** when the version carries a
prerelease or build-metadata tail: `1.21.0-rc.1` is only ever matched as written.
If no candidate is available (or the source is not reproducible/enumerable), the
version you wrote is used verbatim.

PyPI and tracked-path git exact selectors are the exceptions: they are used
literally and do not consult the live index or moving ref for ladder matching.
This lets a PyPI version rebuild from its pinned URL and SHA-256, and a tracked
git version rebuild from its pinned commit/path/blob, when upstream is
unavailable. Their automatic selectors already expose exact canonical version
spellings.

Tracked-path git synthesizes numeric versions from the UTC discovery date:
`YYYY.MM.DD`, then `.2`, `.3`, and so on for further changed blobs locked on the
same date. Unchanged bytes create no version. `--all-versions` combines every
matching historical lock with the current changed blob rather than treating
the branch tip as the whole history.

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

For the full flag surface behind `--version`, `--latest`, and `--all-versions`, read [Invocation and flags](~pekit/running/invocation).
