---
title: Recipe format reference
type: reference
description: "The complete schema for pekit's pekit.toml and package.pekit.toml: every section, key, type, default, and the exact strictness rules the loader enforces."
related:
  - pekit/recipes/anatomy
  - pekit/recipes/sources
  - pekit/recipes/packages
  - pekit/recipes/dependencies-and-claims
  - pekit/recipes/multi-package
  - pekit/reference/supporting-files
---

This is the normative schema for the two TOML files at the heart of a pekit
recipe: `pekit.toml` (the recipe proper) and `package.pekit.toml` (what to
package). It enumerates every section, every key, its type, whether it is
required, and its meaning. Behaviour that a key merely *triggers* is
cross-linked to the concept pages; this page is the field-by-field contract.

Two strictness rules hold throughout and are called out per-section below:

- **Unknown keys are hard errors.** Every table the loader owns has a fixed
  set of accepted keys. Any other key — including a camelCase spelling of a
  known snake_case key, such as `outDir` — is rejected with an
  `unknown_key` diagnostic. There is no lenient/forward-compatible mode.
- **Types are checked on decode.** A key declared here as a string must be a
  string, a table must be a table, and so on; a mismatch is an `invalid_type`
  error.

## `pekit.toml`

### Worked example

```toml
out_dir = "dist"

[env]
CFLAGS = "-O2"
PREFIX = "/usr"

[wrap]
command = ["pesb", "run", "--", "{{command}}"]

[source.git]
url = "https://github.com/example/tool.git"
ref = "v{{version}}"
versions = ">=1.0"
tag_regex = "^v(?P<version>[0-9.]+)$"

[build]
command = "make PREFIX=$PREFIX"

[build.docs]
command = ["make", "docs"]
needs = ["main"]

[build.linked]
command = "make link"
dependencies.pesb-dev.libc = ">=2.38"

[test]
command = "make check"

[install]
command = "make install DESTDIR=$PEKIT_OUT"

[clean]
command = "make clean"
```

### Top-level keys

The recipe file accepts exactly these top-level keys. Anything else is an
`unknown recipe key` error.

| Key | Type | Required | Meaning |
| --- | --- | --- | --- |
| `out_dir` | string | no | Output directory name, relative to the recipe root. Default `"out"`. |
| `env` | table | no | Environment variables exported to every target command. See [`[env]`](#env). |
| `wrap` | table | no | Command wrapper applied to every target. See [`[wrap]`](#wrap). |
| `source` | table | no | Where the recipe's source tree comes from. See [`[source]`](#source). |
| `delegate` | bool or table | no | Borrow build/env/wrap/package definitions from the source tree. See [`[delegate]`](#delegate). |
| `source_package` | table | no | Corresponding-source package emission control. See [`[source_package]`](#source_package). |
| `build` | table | no | Build target(s). See [`[build]` / `[test]` / `[install]` / `[clean]`](#targets). |
| `test` | table | no | Test target(s). |
| `install` | table | no | Install target(s). |
| `clean` | table | no | Clean target(s). |
| `gen` | table | no | Source-generating target(s). See [`[gen]`](#gen). |

### `[env]`

A flat table of environment-variable name → value. Every entry is exported
into each target command's environment (layered on top of the `PEKIT_*`
contract; see [Anatomy of a recipe](~pekit/recipes/anatomy)).

| Key | Type | Required | Meaning |
| --- | --- | --- | --- |
| *&lt;NAME&gt;* | string | — | Value for variable *NAME*. |

Each *NAME* must match `^[A-Za-z_][A-Za-z0-9_]*$`; anything else is an
`invalid_env` error. Values must be strings. Declaration order in the file is
preserved, so a later entry may reference an earlier one via shell expansion
in the target command.

### `[wrap]`

Wraps every target command in another command (for example, running it inside
a sandbox launcher).

| Key | Type | Required | Meaning |
| --- | --- | --- | --- |
| `command` | string or array of strings | no | The wrapper. Must contain the placeholder `{{command}}` exactly once. |

No other key is permitted under `[wrap]`. The `{{command}}` rules mirror a
target `command`:

- **String form:** the whole string is run through a shell; it must contain
  the substring `{{command}}` exactly once.
- **Array form:** `{{command}}` must appear as a *complete* argument (not a
  substring of a larger argument) exactly once, and never as the first element
  (element `0` is the wrapper program itself).

An omitted `command` yields an empty wrap (no wrapping).

### `[source]`

Selects and configures the source tree. It has three sub-tables. At most one
**reproducible** source (`git` or `url`) may be present — declaring both is a
`mixed_source` error. A `local` source may be combined with a reproducible one
(the local path acts as an override). Unknown keys directly under `[source]`
are rejected.

| Sub-table | Meaning |
| --- | --- |
| `[source.git]` | Clone from a git repository. |
| `[source.url]` | Download from a URL (optionally an archive). |
| `[source.local]` | Use a directory on disk. |

One direct key is accepted alongside the sub-tables:

| Key | Type | Required | Meaning |
| --- | --- | --- | --- |
| `patches` | string | no | Name of a recipe-root directory (a single path segment) whose `series` file pekit applies to the materialised source tree before any target runs. Requires a reproducible source (`patches_source` otherwise). See [Patches](~pekit/recipes/sources#patches). |

See [Sources](~pekit/recipes/sources) for materialisation, caching, and
provenance behaviour. Resolved git and url sources are pinned
trust-on-first-use in the recipe's machine-written
[`pekit.lock`](~pekit/reference/supporting-files#pekitlock).

#### `[source.git]`

| Key | Type | Required | Meaning |
| --- | --- | --- | --- |
| `url` | string | **yes** | Git remote URL to clone. |
| `ref` | string | no | Ref (tag/branch/commit) to check out. Templated. Default `"{{version}}"`. |
| `versions` | string | no | Version **cap**: a constraint string filtering enumerated or requested versions (see [Versions](~pekit/recipes/versions)). |
| `tag_regex` | string | no | Regex extracting version numbers from tag names during enumeration. |

#### `[source.url]`

| Key | Type | Required | Meaning |
| --- | --- | --- | --- |
| `url` | string | **yes** | URL to download. Templated with the version. |
| `extract` | bool | no | Treat the download as an archive and extract it. Default `false`. |
| `root` | string | no | Sub-directory within the extracted tree to use as the source root. Default `"."`. |
| `versions` | string | no | Version **cap**: a constraint string filtering enumerated or requested versions (see [Versions](~pekit/recipes/versions)). |
| `file_regex` | string | no | Regex extracting version numbers when enumerating from a listing. |
| `checksum` | string **or** table | no | Expected checksum. A bare string applies to all versions; a table maps version → checksum. |
| `signature` | table | no | Upstream signature verification — see `[source.url.signature]` below. |

#### `[source.url.signature]`

Optional sub-table of `[source.url]`. Its presence makes upstream signature
verification **required**: the detached signature is fetched and verified
against the pinned keys before a version is locked or built. A missing
signature is `signature_missing`; a failed verification is
`signature_invalid`; either aborts the run and writes no lock entry.
Verification is in-process OpenPGP — no host `gpg` is involved.

| Key | Type | Required | Meaning |
| --- | --- | --- | --- |
| `key_files` | string array | **yes** | Committed public key files (armoured or binary OpenPGP), resolved relative to the recipe root. Must be non-empty. |
| `url` | string | no | Signature URL template. `{{source_url}}` expands to the rendered artifact URL; version variables are also available. Default `"{{source_url}}.sig"`. |
| `of` | string | no | What the signature covers: `"artifact"` (the published file, default) or `"decompressed"` (its decompressed content — kernel.org's `.tar.sign` signs the uncompressed tar). Any other value is `invalid_signature`. |
| `fingerprints` | string array | no | Allowlist of signer fingerprints (hex; spaces and `0x` ignored, case-insensitive). When set, a valid signature by any other pinned key is `signature_untrusted_key`. |

#### `[source.local]`

| Key | Type | Required | Meaning |
| --- | --- | --- | --- |
| `path` | string | **yes** | Path to the source directory, resolved relative to the recipe root. |

### `[delegate]`

Lets a recipe borrow definitions that live *inside* the fetched source tree
rather than in the recipe directory. May be written as a bare boolean
(`delegate = true`, equivalent to `all = true`) or as a table.

| Key | Type | Required | Meaning |
| --- | --- | --- | --- |
| `all` | bool | no | Delegate everything (build, env, wrap, packages). |
| `build` | bool | no | Delegate build targets. |
| `env` | bool | no | Delegate `[env]`. |
| `wrap` | bool | no | Delegate `[wrap]`. |
| `packages` | bool | no | Delegate package definitions. |

Any other key is an `unknown delegate key` error. A category is delegated when
either its own flag or `all` is set.

### `[source_package]`

Controls the **corresponding-source package** a recipe emits alongside its
binary packages. Emission is automatic — the table exists only to opt out or
rename. A recipe emits one when both of these hold: it has a reproducible
`[source]` (`git` or `url`; local overrides and bare branch refs never
qualify), and it produces at least one `peipkg`-format package.

| Key | Type | Required | Meaning |
| --- | --- | --- | --- |
| `name` | string | no | Package name. Default `<recipe-dir>-source`. |
| `enabled` | bool | no | Set `false` to emit no source package. Default `true`. |

Any other key is an `unknown source_package key` error.

The emitted package is `noarch`, versioned identically to the recipe's package
members (members that disagree on version are a
`source_package_version_conflict` error), licensed as the conjunction of the
members' licenses, and installs under `/usr/src/dist/<name>-<version>/`
(with any `-source` suffix stripped from `<name>`):

- `upstream/` — the pristine source input: a url source's downloaded artifact
  byte-for-byte, so its hash matches the committed `pekit.lock`, or a
  `git archive` export of the locked commit.
- `patches/` — the recipe's patch series, when a `patches/` directory exists.
- `recipe/` — the build-controlling files from the recipe directory:
  `pekit.toml`, package definitions (including `packages.pekit/`), env files,
  `pekit.lock`, and `keys/`. `*.keyring.pekit.toml` files are never included.

Every `peipkg`-format member the recipe emits carries the source package's
name in its manifest's `build.source_package` field, linking each binary to
its corresponding source.

### `[build]` / `[test]` / `[install]` / `[clean]` {#targets}

These four sections define **targets** — the commands pekit runs. Each section
takes one of two shapes, distinguished by whether a `command` key is present
directly in the section:

- **Bare target:** `command` (and the other target keys) sit directly under
  the section, e.g. `[build]` with `command = "make"`. This defines a single
  target named `main`.
- **Named targets:** the section contains sub-tables, e.g. `[build.docs]` and
  `[build.linked]`, each a target. Each name must be a valid selector.

Mixing the two — a bare `command` alongside a named sub-table in the same
section — is a `mixed_targets` error. (A sub-table whose key is itself a target
key, such as `[build.dependencies]`, is read as part of the bare target, not as
a named target.)

Fields of a single target:

| Key | Type | Required | Meaning |
| --- | --- | --- | --- |
| `command` | string or array of strings | **yes** | The command. String form runs through a shell; array form is an argv executed directly. An empty array is rejected. |
| `needs` | array of strings | no | Names of other targets in the same section that must run first. |
| `clear_out` | bool | no | Wipe this target's output directory before running. Default `true`. |
| `dependencies` | table | no | **Build targets only.** Build-time dependencies the target needs provisioned. See below. |
| `sign` | table | no | **Build targets only.** Files in the target's output to sign after the command succeeds, by signature kind. See [`sign`](#target-sign) below. |

Any other key in a target table is an `unknown target key` error. `dependencies`
and `sign` are accepted only in `[build]` targets; using either in
`test`/`install`/`clean` is an unknown key.

The `dependencies` table is keyed by **provider** (a selector), each mapping
dependency names to version constraints:

```toml
[build.linked.dependencies]
pesb-dev.libc = ">=2.38"
pesb-dev."pkgconfig(zlib)" = "*"
```

| Level | Type | Meaning |
| --- | --- | --- |
| provider | table | A dependency-provider selector. |
| provider.*&lt;name&gt;* | string | Version constraint for the capability *name*. Must be non-empty; use `"*"` for any version. |

Dependency names may be real package names or virtual capabilities (sonames,
`pkgconfig(...)`, etc.) and are validated against peipkg's capability grammar.
See [Commands and targets](~pekit/running/commands-and-targets).

#### `[build.<name>.sign]` {#target-sign}

The `sign` table is keyed by **signature kind**. Each kind is a table mapping
a path or glob, relative to the target's `$PEKIT_OUT`, to the dotted path of
the keyring entry holding the signing key:

```toml
[build.main.sign.pip]
"bin/peinit"  = "tcb.priv"
"lib/*.so.*"  = "tcb.priv"
```

The kind decides the signature format and where it is stored; the keyring
entry is resolved through the ordinary [keyring mechanism](~pekit/recipes/environments-and-keyrings#keyrings)
when the target runs. Signing happens after the target's command exits 0 and
before any dependent target or package sees the output.

| Level | Type | Meaning |
| --- | --- | --- |
| kind | table | A signature kind. The only kind is `pip` — the Peios binary signature that confers a [Process Integrity Protection](~peios/binary-signing-and-pip/process-integrity-protection) tier. Any other name is `unknown_key`. |
| kind.*&lt;pattern&gt;* | string | A relative path or glob (the same glob syntax as `[files]`). The value is a keyring leaf path such as `tcb.priv` whose value is the path to the private key. Must be non-empty. |

For `pip`, the key is an ML-DSA-65 private key — PKCS#8 PEM as produced by
`openssl genpkey -algorithm ML-DSA-65`, or a raw 32-byte seed — and every
matched file must be a 64-bit little-endian ELF. A pattern that matches
nothing (`sign_target_missing`), a keyring entry that is absent or does not
load (`signing_key`), a file that cannot carry the signature (`sign_failed`),
and two patterns naming different keys for one file (`sign_conflict`) are all
errors; pekit never leaves a listed file unsigned. The mechanism is described
in [Signing and provenance](~pekit/running/signing-and-provenance#signing-binaries-for-pip).

### `[gen]` {#gen}

A `[gen]` section defines **source-generating** targets: they run at the recipe
root and write generated source *into the tree* rather than producing an
`out_dir` artifact. Bare/named shapes work exactly as for the target sections
above (`[gen]` is `gen.main`; `[gen.<name>]` names a target). Gen targets have
their own fields — they take **no** `needs` or `clear_out`:

| Key | Type | Required | Meaning |
| --- | --- | --- | --- |
| `command` | string or array of strings | **yes** | The generator. Runs at the recipe root; writes generated source in place. |
| `verify_command` | string or array of strings | no | The drift gate: exit 0 = in sync, non-zero = stale. Run by `pekit verify` and by the consuming-command pre-flight. |
| `verify_on_build` | array of strings | no | Build target names this gate applies to. **Absent** gates every build; **`[]`** gates none; a list gates only those. |
| `verify_on_test` | array of strings | no | As `verify_on_build`, for the `test` namespace. |
| `dependencies` | table | no | Build-time dependencies for `command` (and for `verify_command`, unless overridden). Same shape as a build target's `dependencies`. |
| `verify_dependencies` | table | no | When present, **fully replaces** `dependencies` for the `verify_command` run. |

Any other key is an `unknown target key` error. Setting `verify_on_build`,
`verify_on_test`, or `verify_dependencies` without a `verify_command` is an
`invalid_gen` error (there is nothing to gate).

A gen target's `$PEKIT_OUT` is a pekit-managed scratch directory
(`<out_dir>/.scratch/gen/<name>`) outside the artifact area, cleaned on success
and retained on failure — a convenient place for `verify_command` to regenerate
into for comparison. For the command surface, the pre-flight, and `--no-verify`,
see [Commands and targets](~pekit/running/commands-and-targets#generating-source-gen-and-verify).

## `package.pekit.toml`

The package file describes one or more package artifacts to emit from the built
source. The same schema applies to the base file (`package.pekit.toml`) and to
per-member member files (`<name>.package.pekit.toml`); see
[Multi-package recipes](~pekit/recipes/multi-package) and
[Supporting files](~pekit/reference/supporting-files) for how the files are
discovered and layered.

### Worked example

```toml
format = "peipkg"
builds = ["main"]

[package]
name = "tool"
version = "{{version}}"
architecture = "x86-64-v3"
description = "An example tool"
license = "MIT"
homepage = "https://example.com/tool"
default_root = "opt.tool"

[dependencies]
libc = ">=2.38"
zlib = { constraint = ">=1.3", root = "opt.tool" }

[optional_dependencies]
libcurl = ">=8.0"

[provides]
tool = "{{version}}"

[files]
"main:bin/tool" = "usr/bin/tool"
"@recipe:share/" = { path = "usr/share/tool/", override = true }

[symlinks]
"usr/bin/t" = "tool"

excludes = ["@recipe:share/*.tmp"]

[claims.provides.editor.default]
path = "usr/bin/editor"
target = "usr/bin/tool"

[[publish.localdir]]
path = "dist"
overwrite = false
```

### Top-level keys

The package file accepts exactly these top-level keys; anything else is an
`unknown package key` error.

| Key | Type | Required | Meaning |
| --- | --- | --- | --- |
| `format` | string | no | Artifact format: `"tar"` or `"peipkg"`. Default `"tar"`. |
| `clear_out` | bool | no | Wipe the package stage directory before building. Default `true`. |
| `builds` | array of strings | no | Names of build targets this package requires before staging. |
| `package` | table | no | Package metadata. See [`[package]`](#package). |
| `files` | table | no | Payload file mappings. See [`[files]`](#files). |
| `symlinks` | table | no | Symlinks to embed in the payload. See [`[symlinks]`](#symlinks). |
| `excludes` | array of strings | no | Refs/globs to drop from directory payloads. See [`excludes`](#excludes). |
| `multipack` | table | no | Expand into a family of instances. See [`[multipack]`](#multipack). |
| `publish` | table | no | Where to copy finished artifacts. See [`[publish]`](#publish). |
| `dependencies` | table | no | Runtime dependencies. See [`[dependencies]`](#dependencies). |
| `optional_dependencies` | table | no | Optional runtime dependencies (same schema as `dependencies`). |
| `conflicts` | table | no | name → constraint of packages this one conflicts with. |
| `provides` | table | no | name → version of capabilities this package provides. |
| `replaces` | table | no | name → constraint of packages this one replaces. |
| `side_effects` | array of strings | no | Declared install-time side effects. |
| `sd_overrides` | table | no | path → SDDL security-descriptor overrides. |
| `claims` | table | no | Claim slots on provides/dependencies. See [`[claims]`](#claims). |

> [!IMPORTANT]
> The `tar` format carries payload only: it **cannot express manifest
> metadata**. If a `tar` package sets `version`, `architecture`,
> `description`, `license`, `homepage`, or any of `dependencies`,
> `optional_dependencies`, `conflicts`, `provides`, `replaces`,
> `side_effects`, or `sd_overrides`, the build fails with
> `unsupported_manifest_field`. The `peipkg` format requires
> `[package].version`, `[package].architecture`, and `[package].license` —
> the license is optional at the format level, but pekit requires it so every
> package states its redistribution terms and the corresponding-source
> package can derive its own.

Most string-valued fields (metadata, dependency names/constraints, file refs
and destinations, claim paths/targets) are run through the template engine,
where `{{version}}` and `{{multipack}}` are available. See
[Versions](~pekit/recipes/versions) and
[Multi-package recipes](~pekit/recipes/multi-package).

### `[package]`

Package metadata. Accepts exactly these keys; any other is an
`unknown package metadata key` error. All values are strings.

| Key | Type | Required | Meaning |
| --- | --- | --- | --- |
| `name` | string | no | Package name. Defaults to the package selector (suffixed with the multipack value for multipack instances) when omitted. |
| `version` | string | no | Package version. Required for `peipkg`. |
| `architecture` | string | no | Target architecture. Required for `peipkg`. |
| `description` | string | no | Human-readable description. |
| `license` | string | no | License identifier. Required for `peipkg`. |
| `homepage` | string | no | Project homepage URL. |
| `default_root` | string | no | Preferred [named root](~peios/package-management/claims) for a top-level install. Must be a dotted named reference matching `[a-z0-9][a-z0-9_-]*` per segment, never a filesystem path (a `/` is rejected). |
| `special_system_package` | boolean | no | Declares the package exempt from the payload layout rules, for the rare package whose job is to lay down the structure those rules protect — the base-filesystem package that mints the mountpoint tree is the archetype. Setting it disables pekit's layout validation for this package. It grants nothing at install time: whoever installs or composes the result must *also* pass `--dangerously-bypass-path-restrictions`, so a recipe can propose its own exemption but never grant one. Defaults to `false`. |

Note that `dependencies`, `provides`, `conflicts`, and the rest are **top-level
tables**, not sub-keys of `[package]`.

### `[dependencies]`

Runtime dependency constraints. `[optional_dependencies]` has the identical
schema. Each entry is either a bare constraint string (the short form) or a
table that additionally places the dependency in a named root.

| Form | Type | Meaning |
| --- | --- | --- |
| *&lt;name&gt;* `= "constraint"` | string | Version constraint; the dependency lands in the depender's own root. |
| *&lt;name&gt;* `= { constraint, root }` | table | Table form (below). |

Table form keys — only these two are accepted (`unknown_key` otherwise):

| Key | Type | Required | Meaning |
| --- | --- | --- | --- |
| `constraint` | string | no | Version constraint. Omitting it matches any version. |
| `root` | string | no | Named root to place the dependency in. Same grammar as `default_root`. |

Dependency names may be real or virtual capabilities. See
[Dependencies and claims](~pekit/recipes/dependencies-and-claims).

### `[files]`

Maps a **source ref** (the key) to a destination path within the package
payload (the value). The value is either a string destination or a table.

| Value form | Meaning |
| --- | --- |
| `"ref" = "dest/path"` | Copy the ref to `dest/path`. |
| `"ref" = { path, override }` | Table form (below). |

Table form keys — only these are accepted:

| Key | Type | Required | Meaning |
| --- | --- | --- | --- |
| `path` | string | **yes** | Destination path in the payload. Must be non-empty. |
| `override` | bool | no | Mark the payload as an override entry (skips manifest payload validation for `peipkg`). Default `false`. |

The source ref selects where the file is read from. A bare path with no prefix
is resolved against the recipe root (or the layer's owner). Explicit forms:
`@recipe:<path>`, `@source:<path>`, `@workspace:<path>`, and
`<build-target>:<path>` (reading a build target's output; `:<path>` alone uses
the `main` build target). Destinations ending in `/` and glob patterns are
supported. See [Packages](~pekit/recipes/packages) for ref resolution and glob
semantics.

### `[symlinks]`

Maps a destination path within the payload (the key) to a symlink target (the
value).

| Value form | Meaning |
| --- | --- |
| `"usr/bin/x" = "target"` | Create a symlink at `usr/bin/x` pointing at `target`. |
| `"usr/bin/x" = { target, override }` | Table form (below). |

Table form keys — only these are accepted:

| Key | Type | Required | Meaning |
| --- | --- | --- | --- |
| `target` | string | **yes** | Symlink target text. Must be non-empty. |
| `override` | bool | no | Mark as an override entry. Default `false`. |

### `excludes`

An array of refs/globs. During directory payload expansion, files matching an
exclude pattern (resolved against the same root as the file mapping being
expanded) are dropped from the payload. Patterns use the same ref forms as
`[files]` keys.

### `[multipack]`

Expands one definition into a family of package instances, one per enumerated
value. The only accepted key is `enum`, which takes one of two shapes:

**Explicit list:**

```toml
[multipack]
enum = ["gtk3", "gtk4"]
```

Each value must be a valid selector, non-empty, and unique.

**Enumerated from files:**

```toml
[multipack.enum.files]
path = "@source:themes/*/theme.ini"
regex = "^(?P<value>.+)$"
```

`[multipack.enum.files]` accepts exactly `path` and `regex`, both **required**:

| Key | Type | Required | Meaning |
| --- | --- | --- | --- |
| `path` | string | **yes** | A ref glob (templated) whose matches are enumerated. |
| `regex` | string | **yes** | Regex applied to each match's basename. Must have exactly one capture group, or a single named `value` group, which supplies the instance value. |

See [Multi-package recipes](~pekit/recipes/multi-package).

### `[publish]`

Where finished artifacts are copied. The only accepted target is `localdir`,
written as an **array of tables**:

```toml
[[publish.localdir]]
path = "dist"
overwrite = false
```

Each entry accepts only `path` and `overwrite`:

| Key | Type | Required | Meaning |
| --- | --- | --- | --- |
| `path` | string | **yes** | Destination directory, relative to the workspace root (or recipe root outside a workspace). Templated. The artifact keeps its own filename. |
| `overwrite` | bool | no | Allow replacing an existing file at the destination. Default `true`. |

### `[claims]`

Attaches **claim** slots to provides and dependency entries (a claim is a
symlink slot a provider fills or a consumer expects). The `[claims]` table has
two sides — `provides` and `dependencies` — each keyed by the provides or
dependency name, then by slot, then to a descriptor. Any side other than
`provides`/`dependencies` is an `unknown_key` error.

```toml
[claims.provides.<name>.<slot>]
path = "usr/bin/editor"
target = "usr/bin/tool"

[claims.dependencies.<name>.<slot>]
path = "usr/bin/editor"
```

A slot descriptor accepts exactly these two keys (anything else is rejected);
both are strings and both are templated:

| Key | Type | Required | Meaning |
| --- | --- | --- | --- |
| `path` | string | no | The symlink location (set on a consumer, or as a provider default). |
| `target` | string | no | The holder file within this package (set on a provider). A provider's target must point at a file the package ships. |

Provider-side slots (`claims.provides`) attach to matching `[provides]`
entries by name; consumer-side slots (`claims.dependencies`) attach to matching
`[dependencies]`/`[optional_dependencies]` entries. See
[Dependencies and claims](~pekit/recipes/dependencies-and-claims) and the Peios
[claims](~peios/package-management/claims) model for the resolution behaviour.

## See also

- [Supporting files](~pekit/reference/supporting-files) — the workspace, env, keyring, lockfile, and patch-series schemas.
- [Anatomy of a recipe](~pekit/recipes/anatomy) — the narrative walk-through of these files.
- [Packaging files](~pekit/recipes/packages) — how `[files]` refs and destinations resolve.
