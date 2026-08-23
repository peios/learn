---
title: Templating and Derivation
description: The two mechanisms that make the shipped manifest more than what the recipe wrote — placeholder substitution and derived capabilities.
---

Two mechanisms mean the shipped manifest is not simply what the recipe
wrote.

## Templating

Placeholders are substituted throughout a package definition:
`{{version}}`, `{{major}}`, `{{minor}}`, `{{patch}}`, `{{prerelease}}`,
`{{buildmeta}}`, and `{{multipack}}`.

They apply to the metadata scalars, to the **keys and values** of every
relationship map, to side effects, to claim paths and targets, to file
references and destinations, to symlink targets, to publish paths, and
to the source ref and URL.

They deliberately do not apply to a dependency's `root`, which names a
registered root rather than something derived from a version.

The components come from pekit's own upstream version model, not from
the package version model. For a package version carrying a Peios
revision, the revision lands in `{{prerelease}}`; for a version carrying
an epoch or a tilde, the model does not parse it and the components
render empty.

The idiom for "this package depends on its sibling at this build's
version" is a templated constraint:

```toml
libpeios = "{{version}}"
```

which pins the upstream version and leaves the revision unconstrained.

## Derivation

pekit derives capabilities from the built payload and merges them on top
of what the recipe declared. A hand-written entry always wins.

**Shared libraries.** Sonames are read from the built objects: a
library's own soname becomes a provide, and a binary's needed sonames
become dependencies. Symlinks are skipped, so a versioned library and
its development link do not both claim the same soname. A
shared-library-shaped file carrying no soname produces a warning.

Where the workspace's symbol-version policy names a soname and a token
prefix, the symbol versions a binary actually references become a
version floor on that soname's dependency — so a binary using a recent
C library symbol depends on a library version that has it.

**pkg-config modules.** Each `.pc` file becomes a provide named for the
module, versioned from its version field. Its required modules become
dependencies with ordered constraints, merged from both the public and
private requirement lists. Variable references are expanded to a fixed
point. An unparseable version or constraint is dropped with a warning
rather than failing the build, and modules the package provides itself
are subtracted from what it requires.

The consequence to hold onto: a shipped manifest routinely declares
dependencies the recipe never wrote. Reading a recipe tells you what was
declared, not what was shipped.
