---
title: Multi-package recipes
type: concept
description: "How one pekit recipe emits several packages: base and member package files, the packages.pekit/ directory, layer merge and precedence, selecting members on the CLI with positional selectors and --all, and the [multipack] fan-out that turns one definition into many instances."
related:
  - pekit/recipes/packages
  - pekit/using-pekit/commands-and-targets
  - pekit/recipes/versions
  - pekit/recipes/sources
  - pekit/workspaces/workspaces
---

A recipe rarely produces exactly one artifact. The same build tree is often
split into a runtime package, a `-doc` package, and a `-dev` package; a single
build sometimes fans out into one package per locale, per font family, or per
plugin. pekit expresses both shapes without repeating the build: **member**
package files split one definition into several named packages, and the
`[multipack]` block expands a single definition into many **instances**.

This page covers where package definitions live, how their layers merge, how
you select which packages a run emits, and how multipack fan-out works.

## Package files and layers

pekit discovers package definitions from files whose names follow a fixed
convention, relative to a **root** (the recipe directory, and — under a
workspace or a delegated source — the workspace and source directories too).
Discovery is done by `LoadPackageLayers`, which recognises two kinds of file:

| Kind | Location | Selector |
|------|----------|----------|
| **Base** | `package.pekit.toml`, or `packages.pekit/package.pekit.toml` | `main` |
| **Member** | `<name>.package.pekit.toml`, or `packages.pekit/<name>.package.pekit.toml` | `<name>` |

Both the root itself and a `packages.pekit/` subdirectory are searched, so you
can keep package files beside the recipe or gather them in one folder.

- **At most one base** may exist. Defining `package.pekit.toml` in both the
  root and `packages.pekit/` is an error (`duplicate_package_base`).
- A member's selector is its filename with the `.package.pekit.toml` suffix
  removed. A file literally named `package.pekit.toml` is the base, never a
  member; an empty member name is skipped. Each member name must be a valid
  selector, and a name may not be defined twice across the two search
  locations (`duplicate_package`).

Every file becomes a **layer**. Each layer records its **owner** — `recipe`,
`workspace`, or `source` — which fixes how bare payload references in that file
are qualified: an unqualified file source or exclude in a recipe-owned layer is
read as `@recipe:`, in a workspace-owned layer as `@workspace:`, and in a
source-owned layer as `@source:` (already-qualified refs and `target:path`
build refs are left untouched). See [Package sources and
refs](~pekit/recipes/sources) for the ref grammar.

### How many packages a recipe emits

The base file is a shared foundation, not a package of its own once members
exist. The rule is:

- **No member files** — the base alone produces a **single** package with
  selector `main`. (With no base and no members at all, there is nothing to
  build: `missing_package`.)
- **One or more member files** — the recipe emits **one package per member**.
  The base is merged underneath every member as shared defaults; it does *not*
  additionally produce a standalone `main` package.

So to emit a runtime package plus a `-doc` package you write two member files;
the base carries what they share.

### Merge and precedence

For each emitted package, pekit stacks the applicable layers and merges them in
order, later layers overriding earlier ones. The order is:

1. workspace base
2. source base (only when the recipe [delegates](~pekit/workspaces/workspaces)
   packages to a materialised source and the source root differs from the
   recipe root)
3. recipe base
4. source member(s) with this selector
5. recipe member(s) with this selector

Merge is **field-level, not deep**, and two fields behave differently:

- Scalars and metadata (`format`, `clear_out`, `[package]` fields such as
  `version`, `architecture`, `license`, `homepage`, `default_root`) override
  only when the later layer sets them; an unset field leaves the earlier value
  in place.
- `builds`, `[files]`, `[symlinks]`, `excludes`, `[multipack]`, `[publish]`,
  and the constraint maps (`dependencies`, `provides`, …) are **replaced
  wholesale** when the later layer defines them. In particular a member's
  `[files]` table does not merge key-by-key with the base's — if the member
  declares `[files]` at all, it replaces the base's `[files]` entirely. Put
  shared payload in whichever single layer owns it.

One special case governs names: a member that does **not** set its own
`[package].name` does not inherit the base's name. Its name is cleared, which
lets it fall back to the selector-derived default (see
[Instance naming](#instance-naming-and-artifacts) below). The base's
`[package].name` therefore only ever names the lone `main` package.

## Selecting packages on the CLI

Two commands select packages: **`package`** (stages the builds a package needs,
then writes its artifacts under `out_dir`) and **`publish`** (does the same,
then copies each artifact to a configured `localdir`). See
[Commands and targets](~pekit/using-pekit/commands-and-targets).

Selection works like target selection:

- **Positional selectors** name members: `pekit package hello hello-doc`.
- **No selector, one package** — that package is used.
- **No selector, several members** — the run is ambiguous and pekit lists the
  members (`ambiguous_package`).
- **`--all`** selects every member.

`--all` cannot be combined with positional selectors; doing so is rejected
before any work runs:

```text
invalid_flags: --all cannot be combined with package selectors
```

An unknown selector reports the available members (`missing_package`). A
selector may carry an `:instance` suffix to pick a single multipack instance —
covered next.

## Multipack: one definition, many instances

A single package definition fans out into several packages with the
`[multipack]` block. Each expansion is an **instance**, identified by a
**multipack value**; the value is available to the definition through the
`{{multipack}}` template variable. There are two enumeration modes.

### Static enumeration

List the values inline. `[multipack]` accepts exactly one key, `enum`; as an
array it is a fixed list of values (each a valid selector, no duplicates, and
the list may not be empty):

```toml
[package]
name = "fonts-{{multipack}}"
version = "{{version}}"
architecture = "any"

[multipack]
enum = ["serif", "sans", "mono"]

[files]
"build:share/fonts/{{multipack}}/**" = "usr/share/fonts/{{multipack}}/"
```

This one definition emits three packages: `fonts-serif`, `fonts-sans`, and
`fonts-mono`, each packing its own subtree.

### Enumeration from files

To derive the value set from what the build actually produced, give `enum` a
`files` sub-table with a `path` glob and a `regex` (both required):

```toml
[package]
name = "locale-{{multipack}}"
version = "{{version}}"
architecture = "any"

[multipack.enum.files]
path  = "build:usr/share/locale/*"
regex = '^(?P<value>[a-z]{2})$'

[files]
"build:usr/share/locale/{{multipack}}/**" = "usr/share/locale/{{multipack}}/"
```

pekit globs `path`, applies `regex` to each match's **basename**, and takes the
captured text as the multipack value. The regex must expose the value through
either a named `(?P<value>…)` group or a single unnamed capture group; anything
else is rejected (`invalid_regex`). Values are de-duplicated and each must be a
valid selector. If the glob resolves but nothing matches, that is
`empty_multipack`.

Note the phasing: the `path` template is rendered with `{{version}}` only —
`{{multipack}}` is **not** available while enumerating, because that is the very
value being discovered.

### The `{{multipack}}` variable

`{{multipack}}` is available **only in the package-instance phase** — once a
concrete instance and its value exist. That covers the rendered manifest
metadata (`[package]` name, version, description, dependencies, provides,
claims, …), the `[files]` source and destination templates, `[symlinks]`, and
the `[publish]` destination. Using `{{multipack}}` anywhere it is not bound —
including a non-multipack definition or the `enum.files` `path` — fails:

```text
{{multipack}} is not available in this context
```

`{{version}}` and its parts are available throughout; see
[Versions](~pekit/recipes/versions).

### Selecting one instance

A positional selector may target a single instance with `member:instance`:

```text
pekit package fonts:serif      # only fonts-serif
pekit package fonts            # all instances of fonts
```

The `:instance` suffix is valid only on a multipack definition; applying it to
an ordinary package is an error, as is naming an instance the enumeration never
produces (`missing_package`).

### Instance naming and artifacts

Each instance is named from its rendered `[package].name`. When a definition
has no name, the name defaults to the member selector, and for a multipack
instance the value is appended: a nameless multipack member `plugins` with value
`png` becomes `plugins-png`. The artifact filename follows the format:
`<name>_<version>_<arch>.peipkg` for `format = "peipkg"`, or `<name>.tar` for a
plain `tar` package.

Across everything a single run emits, pekit checks that no two instances write
the same artifact path (`artifact_collision`) or the same
name/version/architecture (`package_name_collision`).

## Dry runs and unresolved instances

`--dry-run` plans without executing. Because a dry run does not actually run the
build targets, a multipack that enumerates **from build output** (an
`enum.files` `path` pointing at a `build:` ref) has nothing to glob yet: its
instances cannot be resolved before the build exists. Rather than fail, pekit
reports each such definition as `unresolved`:

```text
unresolved  fonts  multipack enumeration found no instances for build:...
```

A dry run whose only shortfall is unresolved instances still succeeds — the
enumeration will resolve for real once the build runs. (Similarly, when package
discovery is delegated to a source that has not been materialised, a dry run
reports the packages as unresolved instead of erroring.) A real run performs the
builds first, so enumeration sees the produced files.

## Worked example: runtime plus docs

A recipe that emits two packages from one build, sharing metadata through the
base:

`packages.pekit/package.pekit.toml` — the shared base:

```toml
format = "peipkg"
builds = ["main"]

[package]
version      = "{{version}}"
architecture = "x86_64"
license      = "MIT"
homepage     = "https://example.org/hello"
```

`packages.pekit/hello.package.pekit.toml` — the runtime member:

```toml
[package]
name        = "hello"
description = "The hello program"

[files]
"build:usr/bin/hello" = "usr/bin/hello"
```

`packages.pekit/hello-doc.package.pekit.toml` — the docs member:

```toml
[package]
name        = "hello-doc"
description = "Documentation for hello"

[files]
"build:usr/share/doc/**" = "usr/share/doc/"
```

`pekit package --all` writes both `hello_<version>_x86_64.peipkg` and
`hello-doc_<version>_x86_64.peipkg`, each inheriting `format`, `version`,
`architecture`, `license`, and `homepage` from the base. `pekit package hello`
writes only the runtime package.

## Where to go next

For the `[files]`, `[symlinks]`, and metadata fields each member defines, read [Packaging files](~pekit/recipes/packages).

For the `package` and `publish` commands and their selectors, read [Commands and targets](~pekit/using-pekit/commands-and-targets).

For driving the packages of many recipes at once, read [Workspaces](~pekit/workspaces/workspaces).
