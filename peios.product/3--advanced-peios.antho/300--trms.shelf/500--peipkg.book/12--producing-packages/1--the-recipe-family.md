---
title: The Recipe Family
description: A recipe is a family of TOML documents rather than one file — strict parsing throughout, and how the layers merge.
---

A **recipe** describes how to turn an upstream source tree into one or
more packages. It is not a single file: pekit reads a family of TOML
documents, each with its own role.

| File | Role |
|---|---|
| `pekit.toml` | The recipe: source acquisition, and the build, test, install, clean, and gen targets |
| `workspace.pekit.toml` | Workspace marker: member globs, distro-wide environment, derivation policy |
| `package.pekit.toml` | Shared package metadata — the base layer |
| `<selector>.package.pekit.toml` | One emitted package per file |
| `packages.pekit/` | An alternative directory holding the two above |
| `env.pekit.toml`, `<name>.env.pekit.toml` | A build entry's environment, wrapper, and dependency provider |
| `<name>.keyring.pekit.toml` | A secrets tree exported into the build environment |
| `pekit.lock` | Machine-written source pin |
| `<patches>/series` | The patch series, plain text rather than TOML |

## Strict parsing everywhere

pekit rejects an unknown key at **every** level, including the top level
of every file, and every sub-parser carries its own closed key set.

There is no owner partition and no tolerance for a section pekit does
not recognise, because there is only one tool reading these files.
Adding a section a future version might own makes the recipe fail to
load today.

## The layer merge

A package's definition is assembled from up to five layers, in order:
the workspace base, the fetched source tree's base, the recipe's base,
the source tree's member file, and the recipe's member file.

A scalar from a later layer overrides an earlier one when it is
non-empty. **A map or a slice replaces the earlier one wholesale** — it
does not merge key by key.

That rule has a consequence worth knowing when a base layer declares a
dependency's root. The dependency constraints and the dependency roots
are two separate maps built from one table, and each is replaced only
when the overriding layer's own map is non-empty. A member layer
overriding a dependency with the plain constraint form leaves the roots
map untouched, so the base layer's root survives and is applied to the
new constraint. There is no way to un-set a root a base layer declared.
