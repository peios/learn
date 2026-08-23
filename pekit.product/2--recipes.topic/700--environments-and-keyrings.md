---
title: Environments and keyrings
type: concept
description: "The [env] layers, env files and --env, [wrap] wrappers, dependency_provider, and how keyrings inject secrets as PEKIT_KEYRING_* variables."
related:
  - pekit/recipes/anatomy
  - pekit/recipes/dependencies-and-claims
  - pekit/reference/supporting-files
  - pekit/reference/cli
  - pekit/running/workspaces
---

Every target pekit runs — a `build`, `test`, `install`, or `clean` command —
executes inside an environment pekit assembles for it. That environment has three
distinct layers: the **managed** `PEKIT_*` variables pekit sets automatically, the
**keyring** values that carry secrets and keys, and the **user** variables you
declare in `[env]` and env files. This page describes how those layers are built,
how they compose and override, how `[wrap]` wrappers change the way the command is
launched, and how keyrings resolve and inject values.

For the exhaustive list of managed `PEKIT_*` variables and what each one means, see
the [environment contract in the command-line reference](~pekit/reference/cli);
[Recipe anatomy](~pekit/recipes/anatomy) walks through the ones you will use most.
This page covers everything you add on top of that contract.

## The three layers

When a target runs, pekit composes three maps and overlays them in a fixed order:

| Layer | Source | Naming |
| --- | --- | --- |
| Managed | Set by pekit (recipe/source roots, output paths, version parts, dependency outputs) | `PEKIT_*` |
| Keyring | Keyring files and `--keyring.x.y=` literals | `PEKIT_KEYRING_*` |
| User | `[env]` in the workspace, recipe, and selected env file | Any valid shell name |

The overlay order is **managed, then keyring, then user** — so in principle a later
layer overwrites an earlier one on a key collision. In practice the three
namespaces are kept disjoint by hard rules:

- User `[env]` **may not** set any variable beginning with `PEKIT_`. Doing so is a
  `reserved_env` error.
- A keyring export that collides with a user `[env]` variable or with a managed
  variable is an `env_collision` error, not a silent override.

So the layers never actually collide: managed owns `PEKIT_*`, keyrings own
`PEKIT_KEYRING_*`, and the user layer owns everything else.

## The `[env]` block

`[env]` declares plain environment variables as a TOML table. Each key is the
variable name and each value is a string:

```toml
[env]
CC = "clang"
CFLAGS = "-O2 -pipe"
PREFIX = "/usr"
```

Keys must be valid environment-variable names — they match
`^[A-Za-z_][A-Za-z0-9_]*$`. A non-string value, or a name outside that grammar, is
a parse error. Declaration order is preserved from the file.

`[env]` may appear in three places, each contributing to the user layer:

- the **workspace** file (applies to every member),
- the **recipe** (`pekit.toml`),
- the **selected env file** (see below).

### Composition and override

Within the user layer the sources are applied in this order, and a later source
overrides an earlier one on the same variable name:

1. workspace `[env]`
2. delegated source recipe `[env]`, then that source's env file (only when the
   recipe delegates env — see [Recipe anatomy](~pekit/recipes/anatomy))
3. recipe `[env]`
4. the selected env file's `[env]`

So a variable set in the recipe overrides the same variable inherited from the
workspace, and the selected env file has the final say.

### Shell expansion of `[env]` values

For the common case — a shell target, or any target run under a `[wrap]` wrapper —
pekit emits the user variables as `export` lines in a shell script that runs before
your command, and it does **not** quote them. That means `[env]` values are
expanded by the shell and may reference other variables:

```toml
[env]
PATH = "$PEKIT_OUT/bin:$PATH"
LD_LIBRARY_PATH = "$PEKIT_OUT/lib"
```

Managed `PEKIT_*` and keyring `PEKIT_KEYRING_*` values are exported *before* the
user block, so `[env]` can build on them. (A bare argv command — an array-form
command with no wrapper — receives the composed environment directly from the
process, where these values are literal rather than shell-expanded. Keep `[env]`
values literal if your target uses the array form without a wrapper.)

## Env files and `--env`

An **env file** is a supporting file that lives next to the recipe and carries an
`[env]` block, a `[wrap]` wrapper, a `dependency_provider`, or any combination of
the three. It lets you keep environment- or profile-specific settings out of the
recipe proper. An env file must declare at least one of those keys; the only
recognised top-level keys are `env`, `wrap`, and `dependency_provider`.

Which env file is loaded is controlled by `--env <name>`. The default is `main`,
so `env.pekit.toml` is picked up automatically when present and silently skipped
when absent. Passing `--env none` disables env-file loading entirely. Any other
name selects a named profile such as `release.env.pekit.toml` (`--env release`),
which **must** exist — a missing named file is an error.

```toml
# release.env.pekit.toml
dependency_provider = "peipkg"

[env]
CFLAGS = "-O3 -DNDEBUG"
```

For the exact env-file schema and the selection table, see
[Supporting files](~pekit/reference/supporting-files).

## `[wrap]` wrappers

A **wrapper** changes *how* the target command is launched: instead of running your
command directly, pekit substitutes it into a wrapper command at a `{{command}}`
placeholder. This is how you run a build inside a sandbox, a container shim, a
`nice`/`taskset` prefix, or any other launcher.

`[wrap]` takes a single `command`, written either as a shell string or as an argv
array. Exactly one `{{command}}` placeholder is required:

```toml
# String form — {{command}} appears once in the shell string
[wrap]
command = "firejail --quiet -- {{command}}"
```

```toml
# Array form — {{command}} must be a complete argument (never argv[0])
[wrap]
command = ["nice", "-n", "10", "sh", "-euc", "{{command}}"]
```

At run time pekit assembles the export prelude plus your target command into a
script, and:

- **String wrapper:** the script is shell-quoted and spliced in at `{{command}}`,
  then executed with `sh -euc`.
- **Array wrapper:** `{{command}}` is replaced by the script; the wrapper's first
  element is the program that is executed.

Only one wrapper is active per run. Like `[env]`, `[wrap]` may be declared in
several places, and the **last non-empty one wins**, in this order (lowest to
highest precedence):

1. workspace `[wrap]`
2. delegated source env file `[wrap]` (only when the recipe delegates wrap)
3. recipe `[wrap]`
4. the selected env file's `[wrap]`

So a recipe wrapper overrides the workspace's, and the selected env file's wrapper
overrides the recipe's.

## `dependency_provider`

Env files may also set `dependency_provider`, a single string naming which of a
target's declared `[build.<target>.dependencies.<provider>]` blocks is exported
to the build environment (`PEKIT_DEPENDENCIES`, `PEKIT_DEPENDENCY_PROVIDER`,
`PEKIT_DEPENDENCIES_FILE`). It is not an environment variable; it selects a
declared provider block by name. When both a delegated source env file and the
recipe's own env file set it, the recipe's env file wins. See
[Dependencies and claims](~pekit/recipes/dependencies-and-claims) for what the
selection exports.

## Keyrings

Keyrings supply secrets and keys to targets. Every keyring value is exported to the
target as a `PEKIT_KEYRING_*` environment variable. There are two ways to provide
them: keyring **files** and inline **literals**.

### `--keyring=<value>` (keyring files)

`--keyring` names a keyring file and is repeatable. The value is resolved like
this:

1. If the value is **path-like**, it is treated as a path immediately. A value is
   path-like when it is absolute, begins with `.`, begins with `~`, or contains a
   `/`. The path is resolved relative to the current directory; if the file does
   not exist, that is a `missing_keyring` error.
2. Otherwise the value is treated as a **name**: pekit looks for
   `<value>.keyring.pekit.toml` in each search root in turn. For a plain recipe the
   search root is the recipe directory; inside a workspace the workspace root is
   searched first, then the recipe directory.
3. If no named file is found in any search root, pekit falls back to treating the
   value as a path relative to the current directory; if that does not exist
   either, it is a `missing_keyring` error.

In a `pekit workspace` run, named keyrings are resolved once, against the
workspace root, and the resulting values are shared with every member.

```bash
# Resolved by name → looks for prod.keyring.pekit.toml in the search roots
pekit build --keyring=prod

# Path-like → loaded directly
pekit build --keyring=./secrets/prod.keyring.pekit.toml
```

When several `--keyring` files are given, they are loaded in command-line order and
each overlays the previous — so a **later keyring file overrides an earlier one** on
the same key.

### `--keyring.<dotted.path>=<value>` (literals)

To inject a single value without a file, use `--keyring.<dotted.path>=<value>`. The
dotted path is sanitised into an exported variable name — upper-cased, prefixed
with `PEKIT_KEYRING_`; the exact sanitisation rules are in
[Supporting files](~pekit/reference/supporting-files).

```bash
pekit build --keyring.tcb.priv=<value>
# exported to the target as PEKIT_KEYRING_TCB_PRIV
```

Literals are keyed by their dotted path, so repeating the same path replaces the
earlier value with the later one.

### Precedence

Keyring sources combine in this order, lowest to highest precedence:

```text
earlier --keyring file  <  later --keyring file  <  --keyring.x.y= literal
```

That is: keyring files overlay in command-line order, and all inline literals are
applied last, so a `--keyring.x.y=` value always overrides whatever a keyring file
provided for the same exported name. Any resulting `PEKIT_KEYRING_*` name that
would collide with a managed `PEKIT_*` variable or with a user `[env]` variable is
an `env_collision` error.

### Package signing

One keyring entry is read by pekit itself rather than merely exported:
`signing.package_key` names the Ed25519 private key that signs every
peipkg-format artifact a `package` or `publish` run produces. Because it rides
the keyring mechanism, the key path stays in a per-developer, gitignored file —
or arrives inline as `--keyring.signing.package_key=<path>` — and private key
material never enters a recipe. Without a key, `publish` refuses peipkg
packages unless you pass `--allow-unsigned`. The exact behaviour and the
accepted key encodings are in
[Supporting files](~pekit/reference/supporting-files#well-known-entries).

### Keyring file format

A `*.keyring.pekit.toml` file is a TOML document whose leaves are strings. Each
string leaf becomes one `PEKIT_KEYRING_*` variable, named from its full dotted key
path using the same sanitisation as inline literals. Nested tables are flattened:

```toml
# prod.keyring.pekit.toml
token = "<value>"          # -> PEKIT_KEYRING_TOKEN

[tcb]
priv = "<value>"           # -> PEKIT_KEYRING_TCB_PRIV
pub  = "<value>"           # -> PEKIT_KEYRING_TCB_PUB
```

A leaf that is not a string is rejected, and typed entries — a sub-table carrying a
`path` or `content` key — are reserved and currently rejected as
`unsupported_keyring_entry`. The full schema is documented in
[Supporting files](~pekit/reference/supporting-files).

### A note on secrets in output

Keyring values are exported to the target like any other environment variable.
pekit does **not** redact them from a target's stdout/stderr — if your command
prints a secret, pekit streams it verbatim. pekit's own diagnostics and its
`--verbose` environment summary log variable **names** only, never values, but you
are responsible for not echoing secrets from inside your commands. Prefer writing
secrets to files or consuming them directly rather than printing them.

## Where to go next

For the managed `PEKIT_*` variables these layers sit on top of, read the
[environment contract in the command-line reference](~pekit/reference/cli).

For the exact env-file and keyring schemas, read
[Supporting files](~pekit/reference/supporting-files).

For the signing key that rides the keyring mechanism, read
[Signing and provenance](~pekit/running/signing-and-provenance).
