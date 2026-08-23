---
title: Package Files
description: Each emitted package described by its own file layered over a shared base — metadata, relationships, files, symlinks, multipack and publish.
---

Each emitted package is described by its own file, layered over a shared
base.

| Key | Meaning |
|---|---|
| `format` | `tar` (the default) or `peipkg` |
| `clear_out` | Whether to clear the package's stage directory first |
| `builds` | Which build targets to stage; inferred from the file references when omitted |
| `package` | The metadata table |
| `files` | Source reference to destination |
| `symlinks` | Destination to target |
| `excludes` | Patterns removed from the matched set |
| `multipack` | Fan this one definition into several packages |
| `publish` | Where to publish the result |
| `dependencies`, `optional_dependencies`, `conflicts`, `provides`, `replaces` | The manifest relationships |
| `side_effects` | The declared maintenance operations |
| `sd_overrides` | Path to security descriptor |
| `claims` | Role declarations |

The manifest-facing lists are top-level tables in the package file
rather than members of the metadata table.

A `peipkg`-format package additionally requires a version, an
architecture, and a **license** — the last a distribution requirement
stricter than the format's, which treats the license field as optional.

## Metadata

`[package]` carries the name, version, architecture, description,
license, homepage, `default_root`, and `special_system_package`.

`default_root` is validated against the named-root grammar.
`special_system_package` waives the layout check at pack time — but not
the side-effect check — and grants nothing at install or compose time.

## Relationships

Dependencies take either of two forms:

```toml
libfoo = ">= 1.2"
libfoo = { constraint = ">= 1.2", root = "initramfs" }
```

A table with no constraint matches any version. The table form is the
only way to place a dependency in another root; there is no string
sugar for it.

Conflicts, provides, and replaces are plain name-to-string maps.
Conflicts deliberately carry no root: a conflict is root-local by
construction, and the consumer rejects a root on a conflicts entry
outright.

`side_effects` is a list of strings passed through verbatim: pekit does
not check membership of the recognised set, the consumer does. What
pekit *does* check is agreement with the payload, at pack time and in
both directions — see [Building and signing](~peios/producing-packages/building-and-signing).

## Files

`[files]` maps a **source reference** to a destination. The key grammar
is the interesting half:

| Reference | Means |
|---|---|
| `@recipe:<path>` | A literal tree in the recipe directory |
| `@source:<path>` | A literal tree in the fetched source |
| `@workspace:<path>` | A literal tree in the workspace |
| `<target>:<path>` | The staged output of a build target |
| `:<path>` | The staged output of the `main` target |
| `<path>` | Rewritten to the owning layer's prefix |

Globs are supported, and a directory source maps its whole subtree.

A value may be a plain destination string, or a table with a `path` and
an `override` flag. `override` is not a merge flag: it excludes that one
entry from the layout validation, per file, invisibly in the resulting
package.

That is a second producer-side waiver alongside `special_system_package`
— narrower, but undeclared in the artifact, so a consumer sees an
ordinary package that simply fails validation at install time.

## Symlinks and excludes

`[symlinks]` maps a destination to its target, with the same `override`
option. `excludes` is a list of reference-grammar patterns removed from
whatever the file map matched.

## Multipack

`[multipack].enum` fans one package definition into several. It takes a
static list of values, or a derived form naming a path and a pattern to
enumerate from. Each value binds a placeholder available throughout the
definition, so one stanza can emit a package per kernel module, per
locale, or per plugin.

## Publish

`[publish.localdir]` is an array of tables naming a path and whether to
overwrite. It is the local development route; a real repository is
published with the repository tool.
