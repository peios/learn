---
title: Registration and Resolution
description: Named children as rows in the owning root's database, and how a root reference is resolved.
---

## The registry

A root's named children are rows in that root's own package database:
name, path relative to the owning root, and creation time.

The registry is runtime fact rather than configuration. It records where
a root actually is, so it lives with the rest of what the system knows
about itself, not in the operator's configuration tree.

`peipkg root add`, `remove`, `list`, and `show` manage it. The composer
registers roots declaratively from its manifest.

## Resolving a reference

The `--root` option accepts either form, and the discriminator is
explicit:

- A reference **containing `/`** is a literal filesystem path, used
  unchanged.
- A reference **without `/`** is a name. It is split on `.` and walked
  segment by segment: open the current root's database, look up the
  segment, join its relative path, and recurse into that root's own
  database for the next segment.

An unregistered segment is a hard error. peipkg never creates a root
implicitly.

A visited set of resolved absolute paths rejects cycles, so a registry
that points a root at one of its own ancestors fails rather than
looping.

A manifest may never carry the path form. The discriminator exists only
at the command line, where an operator legitimately wants to install
into a directory that is not a registered root — a mounted target, a
scratch tree.
