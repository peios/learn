---
title: Environments and keyrings
type: concept
description: "The [env] layers, env files and --env, [wrap] wrappers, dependency_provider, and worker isolation and explicit keyring inputs."
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
| User | `[env]` in the workspace, selected workspace env file, recipe, and selected recipe env file | Any valid shell name |

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

`[env]` may appear in these places, each contributing to the user layer:

- the **workspace** file (applies to every member),
- the selected env file at the **workspace root** (applies to every member),
- the **recipe** (`pekit.toml`),
- the selected env file beside the **recipe** (see below).

### Composition and override

Within the user layer the sources are applied in this order, and a later source
overrides an earlier one on the same variable name:

1. workspace `[env]`, then the selected workspace env file
2. delegated source recipe `[env]`, then that source's env file (only when the
   recipe delegates env — see [Recipe anatomy](~pekit/recipes/anatomy))
3. recipe `[env]`
4. the selected recipe env file's `[env]`

So a variable set in the recipe overrides the same variable inherited from the
workspace profile, and the selected recipe env file has the final say.

### Shell expansion of `[env]` values

For the common case — a shell target, or any target run under a `[wrap]` wrapper —
pekit emits the user variables as `export` lines in a shell script that runs before
your command, using double quotes that preserve spaces. This means `[env]` values are
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

An **env file** is a supporting file at the workspace root or beside a recipe. It
carries an `[env]` block, a `[wrap]` wrapper, a `dependency_provider`, a
`[sandbox]` root preparer, a `[lint]` table, or any combination of them. It
lets you keep environment- or profile-specific settings out of the recipe
proper. An env file must declare at least one of `env`, `wrap`,
`dependency_provider` and `sandbox` (see
[Isolated production jobs](#isolated-production-jobs)). The only other
recognised top-level key is `lint`, which adds rule exceptions that belong to
the environment rather than to any package.

Which env file is loaded is controlled by `--env <name>`. The default is `main`,
so `env.pekit.toml` is picked up automatically when present and silently skipped
when absent. Any other name selects a profile such as `release.env.pekit.toml`
(`--env release`). In a workspace, pekit loads that file from the workspace root
and then from the recipe directory; either may be absent, but a named profile
must exist in at least one location. A recipe-local file overlays the workspace
profile. Outside a workspace, the recipe-local file retains the same semantics.
If both paths resolve to the same underlying file (for example through a legacy
member symlink), pekit applies it only once. Passing `--env none` disables both
layers.

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
2. selected workspace env file `[wrap]`
3. delegated source env file `[wrap]` (only when the recipe delegates wrap)
4. recipe `[wrap]`
5. selected recipe env file `[wrap]`

So a recipe wrapper overrides the workspace profile's, and the selected recipe
env file's wrapper overrides the recipe's.

## `dependency_provider`

Env files may also set `dependency_provider`, a single string naming which of a
target's declared `[build.<target>.dependencies.<provider>]` blocks is exported
to the build environment (`PEKIT_DEPENDENCIES`, `PEKIT_DEPENDENCY_PROVIDER`,
`PEKIT_DEPENDENCIES_FILE`). It is not an environment variable; it selects a
declared provider block by name. The precedence is the same as for wrappers:
selected workspace profile, delegated source env file, then selected recipe env
file. The last non-empty value wins. See [Dependencies and
claims](~pekit/recipes/dependencies-and-claims) for what the selection exports.

## Keyrings

Keyrings supply keys to the coordinator. Targets receive **no keyring entries by
default**. A target requests specific public or acquisition inputs with
`keyring_inputs`, and the operator's keyring must separately grant the matching
access. Private signing keys remain coordinator-only. Keyring files and inline
literals continue to resolve through the same precedence rules.

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
# coordinator-only; never exported to the target
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

The well-known package-signing entry is read by Pekit itself:
`signing.package_key` names the Ed25519 private key that signs every
peipkg-format artifact a `package` or `publish` run produces. Because it rides
the keyring mechanism, the key path stays in a per-developer, gitignored file —
or arrives inline as `--keyring.signing.package_key=<path>` — and private key
material never enters a recipe. Without a key, `publish` refuses peipkg
packages unless you pass `--allow-unsigned`. The exact behaviour and the
accepted key encodings are in
[Supporting files](~pekit/reference/supporting-files#well-known-entries).

A `[publish.peipkg]` target may similarly select any keyring leaf with a
`keyring:<dotted.entry>` `signing_key` value. The leaf contains the path to the
Ed25519 private key used to sign repository metadata; the conventional name is
`signing.repository_key`. This is target-selected rather than a second
well-known entry because different publish destinations may use different
repository keys.

### Binary signing

A build target's [`sign` table](~pekit/reference/recipe-format#build-name-sign-target-sign)
also reads the keyring, but through entries the recipe names rather than a
fixed one: `"bin/peinit" = "tcb.priv"` signs that output file with the key
whose path the `tcb.priv` leaf holds. Any leaf will do; the convention in
Peios' own recipes is `[tcb] priv = "<path>"`. See
[Signing binaries for PIP](~pekit/running/signing-and-provenance#signing-binaries-for-pip).

### Keyring file format

Legacy string leaves remain supported as coordinator-only values. To expose a
value to a worker, use a typed entry with `value` and `access`:

```toml
# prod.keyring.pekit.toml — operator-controlled and gitignored
[tcb]
priv = "/secure/tcb.pem"
pub = { value = "PUBLIC_KEY_HEX", access = "public" }

[sources]
registry_token = { value = "TOKEN", access = "acquisition" }
```

```toml
# pekit.toml
[build.main]
keyring_inputs = ["tcb.pub"]
command = 'generate-header "$PEKIT_KEYRING_TCB_PUB"'

[build.vendor]
keyring_inputs = ["sources.registry_token"]
command = 'fetch-sources'
```

`public` inputs are available to requesting targets. `acquisition` inputs are
restricted to `build.vendor`. `signing` entries and legacy strings cannot be
requested by workers. An inline override resets the entry to coordinator-only,
so it cannot accidentally inherit a public grant from an earlier keyring file.
Values are literal strings, including public certificate PEM content; a path
value does not grant filesystem access. Typed `path` and `content` entries remain
unsupported. Colliding normalized entry names are rejected.

### A note on secrets in output

Explicitly granted worker inputs are exported like other environment variables.
pekit does **not** redact them from a target's stdout/stderr — if your command
prints a secret, pekit streams it verbatim. pekit's own diagnostics and its
`--verbose` environment summary log variable **names** only, never values, but you
are responsible for not echoing secrets from inside your commands. Prefer writing
secrets to files or consuming them directly rather than printing them.

## Isolated production jobs

A workspace can require Pekit-controlled isolation:

```toml
# workspace.pekit.toml
[isolation]
enabled = true
inputs = ["_pybuild_"]
```

The selected **workspace** environment profile prepares a dependency root. Put
the profile most jobs use in the workspace's `env.pekit.toml`, so commands run
isolated without `--env`, and keep named profiles such as `debian.env.pekit.toml`
for the exceptions:

```toml
# env.pekit.toml
dependency_provider = "peipkg"
[sandbox]
command = 'exec "$PEKIT_WORKSPACE_ROOT/_peiroot_/enter.sh"'
network_targets = ["build:vendor"]
entry = ["/usr/libexec/peiroot/entry"]
```

The preparer receives `PEKIT_SANDBOX_ROOT`, a fresh destination path, and
`PEKIT_JOB_STATE`, coordinator-only job storage. It installs declared dependencies
and exits. It receives managed variables, not recipe environment expansions or
keyring values. Pekit then runs the target through Bubblewrap with a private PID,
mount and user namespace, a cleared environment, and no network by default.
A profile may set `network_targets = ["build:vendor"]`; this shares
the host network for acquisition, including its DNS configuration, without
mounting the host root or home. Other target names cannot enable network access.
The worker receives its dependency manifest through a read-only file at
`PEKIT_DEPENDENCIES_FILE`.

A profile may also name an `entry` program, which the preparer places in the
root. Pekit runs it inside the sandbox ahead of each target command and it
`exec`s the command, so a profile can start job-scoped services that the
isolated root needs; anything it leaves running ends with the job. The Peios
default profile uses this for name resolution during acquisition. Peios glibc
resolves hosts only through resolvd's socket, which no sandbox runs, so a
native acquisition root gets resolvd's NSS module and a small build-root
resolver that answers on that socket from the copied `resolv.conf`.

That profile acquires in a native root built from the vendor target's `peipkg`
dependency set, adding only a shell, Python for the resolver, the NSS module
and TLS trust; recipe constraints take precedence. A vendor target with an
empty `peipkg` set is rejected.

Delegated and member `[env]` layers still apply inside the worker. Their wrappers
cannot replace workspace isolation or its dependency provider. `--env none` or a
profile without a root preparer fails before target outputs are cleared. Sandbox
profiles outside an isolation-enabled workspace are rejected rather than run
unprotected.

Authenticated source caches remain outside the worker. The source receives a
writable copy by default, at the same visible path: no `allow_write` toggle is
needed. Job outputs retain their paths across stages, and completed stages in the
same job may be modified by later stages and tests. Sibling recipes, repository
indexes, signing keys, host home and completion records are not mounted. Shared
workspace inputs must be named explicitly and are copied into read-only mounts.
Copies exclude Git databases, keyrings, configured key files and common local
credential files; source trees must still contain only intended build inputs.

Pekit serializes invocations of the same recipe. A worker's descendants are gone
before signing starts. PIP and module signatures are applied by the coordinator;
package/publish reapplies signatures after gates that may have rebuilt outputs.
Signing paths that escape the stage through symlinks are rejected.

`--no-build` retains both staged outputs and the private source copy. Outputs
created before isolation was enabled must first be rebuilt; their old stages may
contain leaked signing material and are not exposed to new workers. An explicit
`gen` runs against a private copy and applies its source changes through a bounded
filesystem root after successful completion. Concurrent source edits cause it to
abort. `verify` never writes the source checkout back.

The Peios root preparer snapshots signed repository metadata once per job and
records each resolved dependency closure. Debian preparation records installed
package versions and its base image identity. This is automatic build provenance:
recipes can continue selecting current upstream releases and wildcard dependency
versions. A new job selects current inputs again; no hand-maintained version pins
are required.

## Where to go next

For the managed `PEKIT_*` variables these layers sit on top of, read the
[environment contract in the command-line reference](~pekit/reference/cli).

For the exact env-file and keyring schemas, read
[Supporting files](~pekit/reference/supporting-files).

For the signing key that rides the keyring mechanism, read
[Signing and provenance](~pekit/running/signing-and-provenance).
