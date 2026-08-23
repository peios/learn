---
title: Named Roots
description: A self-contained tree with its own package database — the anchor, the naming grammar, and why nesting is structural.
---

An installation root is a self-contained filesystem tree with its own
package database. The default root is the system root — the **anchor**.
A system may define others; the motivating case is an initramfs image,
built and maintained alongside the main system through the same package
graph.

A package names a root, never a filesystem location. Where a root lives
is the installing system's business, which is what makes a tree
relocatable and what stops a package dictating layout.

## The grammar

A root reference is one or more segments joined by `.`, each matching
`[a-z0-9][a-z0-9_-]*`. Any reference containing `/` is rejected as a
reference.

The grammar is implemented three times — in the manifest decoder, in the
command-line parser, and in the producer toolchain — and all three
agree, all three reject a `/`.

## Nesting is structural

There is no parent field anywhere. A root's registry lives in that
root's own database, so nesting falls out of where the registration is
recorded: `initramfs.subroot` is resolved by reading the anchor's
database for `initramfs`, then reading *that* root's database for
`subroot`.

Registered paths are stored relative to the owning root, which is the
other half of relocatability.
