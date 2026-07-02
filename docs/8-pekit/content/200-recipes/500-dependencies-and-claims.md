---
title: Dependencies and claims
type: concept
description: "How a pekit package declares what it needs, how pekit derives more from the built binaries, and how a package participates in shared filesystem names through claims."
related:
  - pekit/recipes/packages
  - pekit/recipes/environments-and-keyrings
  - pekit/workspaces/workspaces
  - peios/package-management/dependency-resolution
  - peios/package-management/claims
---

A finished `.peipkg` carries a manifest that says what the package **needs** (its
dependencies), what shared names it **fills**, and how it plugs into names other
packages share. Pekit builds that manifest from three sources, in order of
increasing automation:

1. **Declared package dependencies** — `[dependencies]` and
   `[optional_dependencies]` you write in a package file.
2. **Derived dependencies** — sonames and pkgconfig capabilities pekit reads out
   of the staged binaries at pack time, added on top of what you declared.
3. **Claims** — the `[claims]` table, wiring a package's provides and
   dependencies into the peipkg "exactly one holder of a shared name" mechanism.

A separate, unrelated mechanism — **build dependencies** exported to the build
command — is also covered here because it shares the word "dependency". It never
touches the package manifest.

## Declared package dependencies

Package dependencies live in a **package file** (`package.pekit.toml` or a
`<name>.package.pekit.toml` member), not in the recipe. Two tables produce them:
`[dependencies]` for hard requirements and `[optional_dependencies]` for soft
ones. Both parse identically.

```toml
[dependencies]
libssl              = ">= 3.0"
"libc.so.6"         = "*"
"pkgconfig(zlib)"   = ">= 1.2.11"

[optional_dependencies]
bash-completion = "*"
```

Each entry maps a **name** to a **version constraint** string. The name is a
peipkg capability name — either a real package name or a virtual capability such
as a soname (`libc.so.6`) or a `pkgconfig(...)` token. The constraint is any
peipkg constraint expression (`">= 1.2"`, `"< 2"`, and so on). Both `"*"` and the
long form below with the constraint omitted mean **any version**.

### The table form: placing a dependency in a named root

An entry may instead be a table, which is the only way to attach a **placement
root** — the named root the dependency should be installed into, when it differs
from the depender's own root:

```toml
[dependencies]
# short form: constraint only, depender's own root
zlib = ">= 1.2"

# table form: constraint + explicit root
[dependencies.libfoo]
constraint = ">= 3"
root       = "system.lib"
```

A dependency table accepts exactly two keys, `constraint` and `root`; any other
key is an error. Omitting `constraint` matches any version. The `root` is a
**named** root reference (dotted lowercase segments, e.g. `system.lib`), never a
filesystem path — a `/` in it is rejected at build time. Roots are not carried
for `conflicts`, which stay root-local. There is no in-string `IN root` sugar;
the table is the only spelling.

These entries become the manifest's `Dependencies` and `OptionalDependencies`.
How they are matched to concrete packages at install time — capability lookup,
version satisfaction, root placement — is
[dependency resolution](~peios/package-management/dependency-resolution) in
peipkg; pekit only records the requirement.

## Derived dependencies: ELF and pkgconfig scanning

At **pack time**, after staging the payload and before writing the archive,
pekit scans the files it is about to pack and **adds** derived provides and
dependencies on top of whatever the package declared by hand. Two derivations
run, both operating purely over the staged files:

- **ELF derivation** (`DeriveELFDeps`) — reads the built binaries and shared
  objects.
- **pkgconfig derivation** (`DerivePkgConfigDeps`) — emits `pkgconfig(<name>)`
  capabilities from any `.pc` files in the payload.

The results are merged additively: a derived provide or dependency whose name
already appears in the hand-declared set is skipped, so declaring something by
hand always wins. Non-fatal problems (see below) are printed to stderr as
`warning:` lines; they do not stop the build.

### What ELF derivation detects

For every ELF object in the payload, pekit reads two dynamic-section fields:

| ELF field | Becomes | Meaning |
| --- | --- | --- |
| `DT_SONAME` | a **provides** entry | the object's own ABI name, e.g. `libfoo.so.3` |
| `DT_NEEDED` | a **dependency** entry | each shared library the object loads |

The **whole soname** is the capability name. ABI-version identity lives in the
string and is matched by equality, so a dependency on `libfoo.so.3` is never
satisfied by `libfoo.so.4` — a soname bump is a different capability.

Two refinements keep the result honest:

- **Self-provided sonames are subtracted from the needs.** A package that ships
  both a library and something that links against it does not end up depending
  on itself.
- **Symlinks are skipped.** A `-devel` package's `libfoo.so -> libfoo.so.3`
  development symlink is not opened; following it would read the target's
  `DT_SONAME` and mis-attribute the provide to the package shipping the alias.
  The real object is derived where it actually lives.

If a file whose name looks like a shared library (`lib*.so`, `lib*.so.N…`)
carries no `DT_SONAME`, pekit warns that "nothing can depend on it" — such a
library is unusable as a dependency target.

Derivation is entirely automatic and takes **no configuration** beyond the
symbol-version policy below. In particular it has nothing to do with the
`dependency_provider` / `PEKIT_DEPENDENCIES*` mechanism described later — that is
a different feature that shares a word.

### Symbol version policy

By default a soname dependency is derived at **soname granularity only**: the
name must match exactly, with no version constraint. That is always safe but
coarse — it cannot express "needs at least the glibc that introduced
`GLIBC_2.34`".

A **workspace** may opt specific sonames into finer, version-aware derivation
through the `[policy.symbol_versions]` table in the workspace file. It maps a
soname to the **symbol-version token prefix** whose tokens are numbered on the
same scale as the providing package's version:

```toml
# in the workspace file
[policy.symbol_versions]
"libc.so.6"   = "GLIBC_"
"libfoo.so.1" = "FOO_"
```

For a soname listed here, ELF derivation is refined on both sides:

- **Consumer side** — pekit reads the object's versioned symbol needs, takes the
  highest token carrying the prefix (e.g. `GLIBC_2.34`), and turns it into a
  `>= 2.34` constraint on that dependency. Reserved, non-numeric tokens such as
  `GLIBC_PRIVATE` are ignored.
- **Provider side** — the soname's own provides entry is stamped with the
  building package's own version, so consumers have something to match against.

A soname **absent** from the policy is derived at soname granularity only, as
above. The policy is a distro-wide assertion and lives **only** in the workspace
file — `[policy]` currently accepts just the one sub-table, and any other key
under it is an error. Recipes and package files cannot set it. When no workspace
policy is configured, every soname is derived at name granularity.

## Build dependencies exported to the build command

Distinct from everything above, a **build** target in a recipe may declare
`[build.<target>.dependencies.<provider>]` — a set of dependencies grouped under
one or more **provider** names. These never enter the package manifest. Instead,
pekit renders them and hands them to the build command through the environment,
so a build script can fetch or pin its build-time inputs.

```toml
[build.main]
command = "make"

[build.main.dependencies.peipkg]
gcc  = ">= 13"
zlib = "*"        # "*" means any version; a build dep constraint may not be empty

[build.main.dependencies.system]
gcc = "*"
```

`dependencies` is only valid on **build** targets. Each provider block maps a
capability name to a non-empty constraint (use `"*"` for any). Names and
constraints are templated, so `{{version}}` and friends work.

**Which provider is active** is chosen by the `dependency_provider` key in the
selected [environment file](~pekit/recipes/environments-and-keyrings):

```toml
# in env.pekit.toml (or a named <env>.env.pekit.toml)
dependency_provider = "peipkg"
```

For every target run, pekit writes a JSON payload to
`$PEKIT_ROOT/.pekit/dependencies/<command>.<target>.json` and exports three
variables into the build environment (with no provider selected,
`PEKIT_DEPENDENCY_PROVIDER` and `PEKIT_DEPENDENCIES` are empty strings and the
payload still carries `all_providers`):

| Variable | Contents |
| --- | --- |
| `PEKIT_DEPENDENCY_PROVIDER` | the selected provider name |
| `PEKIT_DEPENDENCIES_FILE` | absolute path to the JSON payload |
| `PEKIT_DEPENDENCIES` | the selected provider's deps, one `name constraint` per line |

The JSON payload carries the `command`, `target`, `provider`, the resolved
`version`, the selected provider's `dependencies`, and `all_providers` (every
declared provider block, so a script can inspect alternatives). If
`dependency_provider` names a provider the target does not declare, the build
fails with a clear error. If no provider is selected, the exported dependency
list is empty but the payload still lists `all_providers`.

Pekit does not resolve or install these — it only renders the declared list and
passes it through. Consuming it is the build script's job. `dependency_provider`
is a **name selector**, not a command or hook.

## Claims

A **claim** is how a package plugs into a shared filesystem name that at most one
installed package may hold at a time — the peipkg mechanism where several
packages can supply a name like `/usr/bin/cc`, but exactly one **holder** owns
the real file and the rest defer. See
[claims](~peios/package-management/claims) for what this means at install time.

> Terminology: these are **claims**. Do not call them "roles" — in Peios
> operator documentation "role" is a different, reserved concept.

A package declares claims in the top-level `[claims]` table of a package file.
It has two sides:

- **`[claims.provides]`** — the provider side: slots a `[provides]` entry fills.
- **`[claims.dependencies]`** — the consumer side: slots a dependency expects.

Under each side, the next key is the **name of the provides or dependency entry
the claim attaches to**, and under that is one or more freely-named **slots**.
Each slot is a table with just two possible fields:

| Field | Set by | Meaning |
| --- | --- | --- |
| `target` | provider | the holder file this package ships that the shared name resolves to |
| `path` | consumer (or a provider default) | the shared filesystem location — where the claim symlink is materialised |

A worked example — a compiler package that offers to hold `/usr/bin/cc`, and a
consumer that expects `cc` to exist:

```toml
# provider: gcc.package.pekit.toml
[provides]
cc = "1"

[claims.provides.cc.default]
target = "/usr/bin/gcc"   # a file this package ships
path   = "/usr/bin/cc"    # provider default for the shared name

# consumer: some-toolchain.package.pekit.toml
[dependencies]
cc = "*"

[claims.dependencies.cc.default]
path = "/usr/bin/cc"      # the shared name this package needs present
```

Claim `path` and `target` values are run through the template engine, so a
recipe may parameterise them (an arch triplet in a library path, for instance)
like any other manifest value.

At pack time pekit validates the provider side: **every provider slot's `target`
must name a file the package itself ships.** A target pointing outside the
package's own payload is a packaging error — the materialised symlink would
dangle or point at another package's file — and all offenders are reported
together. Consumer-side slots and provider slots that set only a `path` own no
target and are exempt from this check.

## Where to go next

For the package files these tables live in, read [Packaging files](~pekit/recipes/packages).

For the environment file that selects a build dependency provider, read [Environments and keyrings](~pekit/recipes/environments-and-keyrings).

For the workspace `[policy]` table that refines soname derivation, read [Workspaces](~pekit/workspaces/workspaces).
