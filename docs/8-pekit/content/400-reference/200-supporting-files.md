---
title: Supporting files and reference tables
type: reference
description: "Exact schemas for pekit's non-recipe files (workspace.pekit.toml, env.pekit.toml, *.keyring.pekit.toml) plus reference tables for template variables, source-ref roots, and publish targets."
related:
  - pekit/reference/recipe-format
  - pekit/recipes/environments-and-keyrings
  - pekit/recipes/packages
  - pekit/workspaces/workspaces
  - pekit/recipes/multi-package
  - pekit/reference/cli
---

# Supporting files and reference tables

This page documents the TOML files that sit *alongside* a recipe — the
workspace file, env files, and keyring files — and gives exhaustive reference
tables for the three substitution systems used throughout pekit: template
variables, source-ref roots, and publish targets.

All files are TOML. Every loader rejects unknown top-level keys with an
`unknown_key` diagnostic, so the key tables below are complete: any key not
listed is an error.

For the recipe file itself (`pekit.toml` / `*.pekit.toml`), see
[recipe-format](~pekit/reference/recipe-format).

---

## `workspace.pekit.toml`

A workspace file marks a directory as a pekit workspace and declares
distro-wide defaults. Loaded by `LoadWorkspace`.

| Key | Type | Required | Meaning |
| --- | --- | --- | --- |
| `include` | array of strings | **yes** | Member patterns the workspace builds. Must be present and non-empty, or the load fails (`missing_key`). |
| `exclude` | array of strings | no | Patterns removed from the `include` set. |
| `[env]` | table | no | Workspace-level environment variables. See [env table](#env-table). |
| `[wrap]` | table | no | Workspace-level command wrapper. See [wrap table](#wrap-table). |
| `[policy]` | table | no | Distro-wide derivation policy. See below. |

### `[policy]`

The `[policy]` table currently carries exactly one sub-table. Any other key
under `[policy]` is rejected.

| Key | Type | Required | Meaning |
| --- | --- | --- | --- |
| `[policy.symbol_versions]` | table (string → string) | no | Maps a shared-library soname to the symbol-version **token prefix** whose tokens are commensurable with the providing package's version. Governs which sonames get a symbol-version floor during dependency derivation. |

Each entry in `[policy.symbol_versions]` is `soname = "PREFIX_"`:

```toml
[policy.symbol_versions]
"libc.so.6"     = "GLIBC_"
"libstdc++.so.6" = "GLIBCXX_"
```

---

## `env.pekit.toml`

An env file provides a *named, selectable* layer of environment variables,
command wrapper, and dependency-provider override. Loaded by `LoadEnvFile`.

An env file must declare **at least one** of `[env]`, `[wrap]`, or
`dependency_provider`; a file with none of them is rejected (`missing_key`).

| Key | Type | Required | Meaning |
| --- | --- | --- | --- |
| `[env]` | table | one of the three | Environment variables. See [env table](#env-table). |
| `[wrap]` | table | one of the three | Command wrapper. See [wrap table](#wrap-table). |
| `dependency_provider` | string | one of the three | Selector naming which of a build target's declared dependency-provider blocks (`[build.<target>.dependencies.<provider>]`) is exported as the `PEKIT_DEPENDENCIES*` variables. Validated as a [selector](#selectors). |

### `--env <name>` selection

The active env file is chosen from the `--env <name>` flag (default `main`),
resolved relative to the recipe root:

| `--env` value | File loaded | Must exist? |
| --- | --- | --- |
| *(unset)* or `main` | `env.pekit.toml` | no (silently absent) |
| `none` | *(no env file loaded)* | n/a |
| any other `<name>` | `<name>.env.pekit.toml` | **yes** — a missing file is an error |

So `--env prod` loads `prod.env.pekit.toml`, and it must exist. The default
`env.pekit.toml` is optional.

### `[env]` table

Shared by `workspace.pekit.toml`, `env.pekit.toml`, and the recipe's own
`[env]`. It is a flat table of `NAME = "value"` string pairs.

| Rule | Detail |
| --- | --- |
| Value type | Every value must be a string. |
| Name grammar | Names must match `^[A-Za-z_][A-Za-z0-9_]*$`. |
| Reserved prefix | User env may not set any `PEKIT_*` name — those are pekit-managed. A `PEKIT_`-prefixed name is rejected at build time (`reserved_env`). |
| Layering | Applied workspace → (delegated source) → recipe → env file, later layers overriding earlier ones. |

```toml
[env]
CC = "clang"
CFLAGS = "-O2 -pipe"
```

### `[wrap]` table

Shared by `workspace.pekit.toml`, `env.pekit.toml`, and the recipe. Wraps every
target command in another command (sandbox, `nice`, a toolchain shim, etc.).

| Key | Type | Required | Meaning |
| --- | --- | --- | --- |
| `command` | string or array of strings | no | The wrapper. Must contain exactly one `{{command}}` placeholder. |

`{{command}}` rules (enforced by `validateWrapCommand`):

- **String form** — the string must contain `{{command}}` exactly once.
- **Array form** — exactly one element must be the literal `{{command}}` (as a
  *complete* argument, not a substring), and it may not be element `0` (the
  program). An element that merely contains `{{command}}` inside other text is
  rejected.

```toml
[wrap]
command = ["bwrap", "--ro-bind", "/usr", "/usr", "{{command}}"]
```

Note: `{{command}}` here is a wrap-only placeholder handled by the wrap
machinery. It is **not** one of the [template variables](#template-variables)
below and is not available in ordinary recipe strings.

---

## `*.keyring.pekit.toml`

A keyring file supplies secrets to the build environment as `PEKIT_KEYRING_*`
variables. Keyrings are opt-in per invocation (`--keyring`); a keyring named
`<name>` resolves to `<name>.keyring.pekit.toml`, searched in the workspace
root then the recipe root (a path-like value is used verbatim).

### Schema

The file is a tree of nested TOML tables whose **leaves are strings**. Each
leaf's dotted path is converted into an environment-variable name:

- Prefix `PEKIT_KEYRING_`, then the dotted path uppercased.
- Every run of non-alphanumeric characters (including the `.` separators)
  collapses to a single `_`.
- Trailing `_` is trimmed.

| Leaf path | Exported variable |
| --- | --- |
| `token` | `PEKIT_KEYRING_TOKEN` |
| `github.token` | `PEKIT_KEYRING_GITHUB_TOKEN` |
| `registry.api-key` | `PEKIT_KEYRING_REGISTRY_API_KEY` |

```toml
# placeholders only — never commit real secrets
token = "REPLACE_ME"

[github]
token = "REPLACE_ME"

[registry]
api-key = "REPLACE_ME"
```

### Restrictions

| Rule | Detail |
| --- | --- |
| Leaf type | Every leaf must be a string. A non-string leaf is an error. |
| Nesting | Sub-tables nest arbitrarily; each nesting level adds a segment to the exported name. |
| Typed entries | A table containing a `path` or `content` key is a *typed* entry and is **not supported yet** (`unsupported_keyring_entry`). |
| Collisions | A keyring export that collides with a normal or managed env variable is an error (`env_collision`). |

---

## Template variables

Recipe and package **value strings** (source refs, `ref`, package metadata,
file/symlink paths, excludes, claims, multipack `enum.files.path`, publish
`path`) are run through the template engine before use. The syntax is
`{{name}}`, where `name` matches `[A-Za-z0-9_]+`. An unknown name is an error.

| Variable | Source | Availability |
| --- | --- | --- |
| `{{version}}` | the selected version, verbatim (`Raw`) | Errors when no version is selected. |
| `{{major}}` | major component | Available once a version is selected. |
| `{{minor}}` | minor component | Errors if the selected version has no minor component. |
| `{{patch}}` | patch component | Errors if the selected version has no patch component. |
| `{{prerelease}}` | pre-release component (after `-`) | Empty string when absent. |
| `{{buildmeta}}` | build-metadata component (after `+`) | Empty string when absent. |
| `{{multipack}}` | the current multipack instance value | Only available while expanding a multipack package's per-instance values; errors in any non-multipack context. |

A version string parses as `major[.minor[.patch]][-prerelease][+buildmeta]`, so
`{{minor}}` / `{{patch}}` are only present when the version actually carries
them.

### Shell targets use `$PEKIT_*` instead

The `{{...}}` engine applies to recipe *configuration* strings, not to the shell
bodies of build/test/install/clean commands. Target commands instead read the
pekit-managed environment. The version equivalents are:

| Template variable | Environment variable |
| --- | --- |
| `{{version}}` | `$PEKIT_VERSION` |
| `{{major}}` | `$PEKIT_VERSION_MAJOR` |
| `{{minor}}` | `$PEKIT_VERSION_MINOR` |
| `{{patch}}` | `$PEKIT_VERSION_PATCH` |
| `{{prerelease}}` | `$PEKIT_VERSION_PRERELEASE` |
| `{{buildmeta}}` | `$PEKIT_VERSION_BUILDMETA` |

Alongside these, the managed environment also exports `PEKIT_RECIPE_ROOT`,
`PEKIT_SOURCE_ROOT`, `PEKIT_LITERAL_ROOT`, `PEKIT_ROOT`, `PEKIT_OUT_BASE`,
`PEKIT_OUT`, `PEKIT_COMMAND`, `PEKIT_TARGET`, `PEKIT_WORKSPACE_ROOT`,
`PEKIT_BUILD_TIMESTAMP`, `PEKIT_SOURCE_TIMESTAMP`, a `PEKIT_<DEP>_OUT` per
declared `needs` dependency, and any `PEKIT_KEYRING_*` from active keyrings. The
full environment contract is documented in
[recipe-format](~pekit/reference/recipe-format).

---

## Source-ref roots

Package `files` sources, `excludes`, and `multipack.enum.files.path` are
*references* whose leading token selects which root the path is resolved
against. A reference is `ROOT:path` (or a bare path, which normalises to the
owner's default root).

| Reference form | Root | Meaning |
| --- | --- | --- |
| `target:path` | the build target's output stage | Reads from the output of build target `target`. |
| `:path` | build target `main`'s output stage | Same as above with the target name defaulted to `main`. |
| `@source:path` | the materialised source tree (`LiteralRoot`) | Reads from the checked-out / extracted source. |
| `@recipe:path` | the recipe directory | Reads a file shipped next to the recipe. |
| `@workspace:path` | the workspace root | Reads a file from the workspace. Errors if used outside a workspace. |
| bare `path` | owner default | A path with no `:` normalises to the owning layer's root: `@recipe:` for recipe packages, `@source:` for source packages, `@workspace:` for workspace packages. |

Any reference containing a `:` that is not one of the `@`-prefixed roots is a
**build** reference; the token before the `:` is the target name. See
[packages](~pekit/recipes/packages) for how these are used in a package's
`[files]` table.

---

## Publish targets

The `publish` command copies a package's built artifact to declared destinations. There is
exactly one publish kind: `localdir`. Any other `[publish.*]` key is rejected
(`unknown_key`). A package selected for publishing that declares no target is an
error.

Targets are an array of tables:

```toml
[[publish.localdir]]
path = "dist/{{version}}"
overwrite = false
```

| Key | Type | Required | Meaning |
| --- | --- | --- | --- |
| `path` | string | **yes** | Destination **directory**, relative to the base root. Templated with `{{version}}` and `{{multipack}}`. The artifact keeps its own filename. |
| `overwrite` | bool | no (default `true`) | Whether an existing destination file may be replaced. When `false`, an existing destination is an error (`publish_exists`). |

Resolution details:

| Aspect | Behaviour |
| --- | --- |
| Base root | The workspace root when building in a workspace, otherwise the recipe root. `path` is joined onto it. |
| Final destination | `<base>/<path>/<artifact-filename>`. |
| Collisions | Two instances resolving to the same destination is an error (`publish_collision`) unless they are the same artifact. |

<a id="selectors"></a>

## Selectors

Several names above are validated as **selectors**: target names, package
selectors, multipack values, and `dependency_provider`. A selector must match
`^[A-Za-z0-9_.+-]+$`, must not be empty, must not start with `-`, and must not
contain `/` or `:`.
