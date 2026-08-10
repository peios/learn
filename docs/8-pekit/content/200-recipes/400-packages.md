---
title: Packaging files
type: concept
description: "How a pekit recipe maps built output into a package payload: the [files] and [symlinks] tables, source-ref syntax (build outputs, rooted refs, owner-relative paths), globs, excludes, and the destination and collision rules that produce a .peipkg."
related:
  - pekit/recipes/anatomy
  - pekit/recipes/multi-package
  - pekit/recipes/dependencies-and-claims
  - pekit/recipes/sources
  - pekit/reference/recipe-format
  - pekit/reference/supporting-files
---

A package definition answers one question: **which files, from where, go where in
the package?** Everything else — metadata, dependencies, claims, multi-package
fan-out — hangs off that payload. This page is about the payload itself: the
`[files]` and `[symlinks]` tables, how source references resolve, and the rules
that decide the final layout of the `.peipkg`.

Package definitions live in their own files, not in the recipe:
`package.pekit.toml` (the base definition) and `<name>.package.pekit.toml`
(named members). How those layer together, and how `[multipack]` expands one
definition into many packages, is covered in
[Multi-package recipes](~pekit/recipes/multi-package). Manifest metadata,
dependencies, and claims are covered in
[Dependencies and claims](~pekit/recipes/dependencies-and-claims). This page
assumes a single definition and concentrates on the file mapping.

## The `[files]` table

`[files]` maps sources to package destinations. The mapping direction is
**source on the left (the key), package destination on the right (the value)**:

```toml
[files]
":bin/hello"        = "usr/bin/hello"
"@recipe:default.conf" = "etc/hello/hello.conf"
```

The left side is a **source ref** naming what to copy; the right side is the
path the file takes **inside** the package. Destinations are always relative
(see [Destination rules](#destination-rules) below).

Each value may also be a table, which adds an `override` flag:

```toml
[files]
"@recipe:layout.json" = { path = "usr/share/hello/layout.json", override = true }
```

`path` is the package destination (required; an empty destination is an error),
and `override` — default `false` — exempts the entry from the package format's
layout policy (see [`override`](#override)). The bare-string form
`"src" = "dest"` is exactly `"src" = { path = "dest" }`. The field-by-field
schema is in the [recipe format reference](~pekit/reference/recipe-format).

## Source refs

A source ref names *where a file comes from*. There are three families.

### Build-output refs — `target:path`

A ref containing a colon is a **build ref**. The part before the colon is a
build target name; the part after is a path inside that target's staged output:

```toml
[files]
"tools:bin/hc" = "usr/bin/hc"   # from build target "tools"
":bin/hello"   = "usr/bin/hello" # empty target = "main"
```

`:path` is shorthand for `main:path` — an empty target name resolves to the
target `main`. Referencing a build target in `[files]` automatically pulls that
build into the package's build plan, so you do not have to list it separately.

### Rooted refs — `@source:`, `@recipe:`, `@workspace:`

A ref beginning with `@<root>:` is anchored to a named root rather than a build
output:

| Prefix | Root |
|---|---|
| `@source:` | The materialised source tree (the checked-out / extracted source). |
| `@recipe:` | The directory containing the recipe (and its package files). |
| `@workspace:` | The workspace root. Used outside a workspace, this is an error (`missing_workspace`). |

```toml
[files]
"@source:LICENSE"      = "usr/share/licenses/hello/LICENSE"
"@recipe:hello.service" = "usr/lib/systemd/system/hello.service"
```

The [reference table of source-ref roots](~pekit/reference/supporting-files)
gathers every ref form — build refs, the rooted prefixes, and bare paths — in
one place.

### Plain paths are owner-relative

A ref with **no** prefix and **no** colon is a plain path — and its meaning is
set by the file that *declared* it, not by any global default. At decode time,
pekit rewrites each plain path to a rooted ref based on the file's **owner**:

| The ref was declared in… | A plain path becomes… |
|---|---|
| a recipe-side package file | `@recipe:` |
| a delegated source-side package file | `@source:` |
| a workspace-side package file | `@workspace:` |

So in a recipe's own `package.pekit.toml`:

```toml
[files]
"README.md" = "usr/share/doc/hello/README.md"
```

`"README.md"` is normalised to `"@recipe:README.md"` — it resolves against the
recipe directory. The identical line in a source-delegated package file would
normalise to `"@source:README.md"` and resolve against the source tree instead.
This normalisation is what lets the same package file mean the right thing
whether it ships beside the recipe or is discovered inside a delegated source.

Refs that are already rooted (`@…:`) or already build refs (contain a `:`) are
left untouched by this rewrite.

> The owner-relative rule also applies to the source path of `[multipack]` file
> enumeration and to every entry in `excludes` — both are normalised the same
> way.

### Path cleaning

The path portion of every rooted ref is cleaned: `.` and duplicated slashes are
collapsed, and a path that escapes its root with `..` (or is absolute) is
rejected:

```text
invalid_ref: "@recipe:../secrets" escapes its root
```

## Globs

A source ref's path may contain glob metacharacters — `*`, `?`, or a `[...]`
character class — and `**` for recursive matching:

```toml
[files]
"@source:share/icons/*.png" = "usr/share/hello/icons/"
"tools:lib/**/*.so"         = "usr/lib/"
```

Rules:

- Matching happens **only within the ref's source root**. A glob never reaches
  outside the root it is anchored to.
- Matches are **sorted**, and a match already covered by a matched parent
  directory is dropped (the directory carries its contents).
- By default a glob that matches **nothing** is an error:

  ```text
  missing_payload: file source /…/share/icons has no matches
  ```

- Placement is **relative to the non-glob prefix**. Everything up to the first
  segment containing a glob metacharacter is the base; matched paths are re-rooted under
  the destination from there. So `share/icons/*.png` → `usr/share/hello/icons/`
  places `foo.png` at `usr/share/hello/icons/foo.png`, and
  `lib/**/*.so` preserves the sub-directory structure below `lib/` under the
  destination.

A plain (non-glob) ref that names a **directory** copies the whole tree; empty
directories are emitted as explicit entries (so a pure directory skeleton is not
lost).

## Excludes

`excludes` prunes files after expansion. Each entry uses the **same source-ref
syntax** as `[files]` (and is owner-normalised the same way), so an exclude is
scoped to a root:

```toml
[files]
"@source:share/**" = "usr/share/hello/"

excludes = [
  "@source:share/**/*.tmp",
  "@source:share/internal/**",
]
```

An exclude is applied only to expansions that share its root; it is matched
against each candidate with the same glob engine. Unlike `[files]`, an exclude
that matches **nothing is allowed** — it is a filter, not a required input.

## Destination rules

The right-hand side of a `[files]` entry (and every symlink destination) is a
path **inside** the package. It must be relative and stay in-bounds:

- **No leading `/`** and **no `..`** — an absolute or escaping destination is
  rejected.
- **No NUL** bytes; an empty destination is an error.
- `.` segments and duplicate slashes are normalised away.

### Directory vs single-file destinations

For a **single, non-glob** match, the trailing slash on the destination decides
the shape:

| Ref | Destination | Result |
|---|---|---|
| `":bin/hello"` | `"usr/bin/hello"` | Renamed to `usr/bin/hello`. |
| `":bin/hello"` | `"usr/bin/"` | Placed as `usr/bin/hello` (basename kept). |

For a **glob** or a **multi-match** source, the destination is always treated as
a directory prefix and matched paths are re-rooted beneath it.

### Collisions are errors

Two payload inputs that resolve to the **same** package path is a hard error —
pekit will not silently let one input overwrite another:

```text
payload_collision: multiple package inputs map to usr/bin/hello: …
```

(Sibling checks catch two package instances writing the same artifact file, or
emitting the same package name.)

### `override`

`override = true` exempts an entry from the **package format's layout policy**
only. The peipkg format validates that non-override payload paths obey its
layout rules; an override entry skips that validation, letting you place a file
somewhere the policy would otherwise reject.

Override does **not** relax the safety rules above: destinations are still
cleaned, still may not escape the package with `..`, and collisions are still
errors. It only opts out of format-level layout policy.

## `[symlinks]`

`[symlinks]` adds symbolic links to the payload. Here the **key is the package
destination** (where the link lives) and the **value is the link's target text**:

```toml
[symlinks]
"usr/bin/hello-latest" = "hello"
"usr/lib/libhello.so"  = { target = "libhello.so.1", override = true }
```

The target text is stored **literally** — it is the exact string the symlink
points at and is *not* resolved through any source root. It may be relative or
absolute as a link target; pekit only checks that it is non-empty and contains
no NUL. The bare-string form is `"dest" = "target"`; the table form adds
`override`, which behaves as for files.

The destination key follows the same [destination rules](#destination-rules) as
`[files]`.

## The result

Packaging stages the resolved payload and writes one package artifact per
package instance under the recipe's output directory (`out_dir`). The format is
chosen by the package's `format` (defaulting to `tar`); a `peipkg` package emits
a file named `<name>_<version>_<architecture>.peipkg`, with the name,
architecture, and other manifest fields coming from `[package]`.

The rest of the manifest — version, architecture, dependencies, provides,
claims, and so on — is documented in
[Dependencies and claims](~pekit/recipes/dependencies-and-claims), and the
`.peipkg` on-disk format itself in
[Package management](~peios/package-management/overview). Full key-by-key syntax
lives in the [recipe format reference](~pekit/reference/recipe-format).
