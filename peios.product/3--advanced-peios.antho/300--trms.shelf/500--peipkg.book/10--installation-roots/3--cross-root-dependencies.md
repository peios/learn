---
title: Cross-Root Dependencies
description: A dependency is satisfied within a root — how routing works, which verbs route, satisfier identity, and cross-root garbage collection.
---

A dependency is satisfied within a root. By default that is the
depending package's root, so a package's closure flows into the root the
package occupies. A dependency's `root` field names a different one.

```json
{ "name": "peiosutils", "root": "initramfs" }
```

declares that the dependency is required in the initramfs root, wherever
the depending package lives.

## Routing

Every placement decision passes through one point: given a dependency
and the depending package's root, choose the target root. An empty
`root` field, or single-root mode, keeps the dependency where the
depender is; otherwise the name is looked up in the live registry.

A `root` naming something not registered is a resolution failure —
unsatisfiable, naming the root — rather than a silent fallback.

Cross-root edges are honoured in plan ordering and in the
reverse-dependency check that decides what a removal breaks.

## Which verbs route

`install` resolves cross-root. `upgrade`, `downgrade`, `uninstall`, and
`undo` resolve single-root, where a dependency's `root` field is inert
and the dependency is evaluated in the depending package's root instead.

So a cross-root dependency is placed correctly when the depending
package is installed, and is evaluated in the wrong root on every later
operation.

## Satisfier identity

A satisfier is identified by the pair (name, root). The same package
name installed in two roots is two independent installations, possibly
at different versions, and a dependency is satisfied only by an
installation in the root it names.

> [!NOTE]
> Cross-root dependencies are what let a root be composed through the
> dependency graph. An initramfs package depends on ordinary packages —
> a shell, core utilities — and has them placed into the initramfs root,
> either implicitly by living there or explicitly through `root`. The
> depended-on package declares no root affinity of its own; where it
> lands is the depender's and the operator's choice. This generalises
> the fixed build-host/target split other systems draw to an open set of
> named roots.

## Top-level placement

Where an operator names a package directly with no explicit `--root`,
the package's `default_root` decides where it lands. peipkg applies it
once, before building the resolver's requests, and only when the
operator did not pass `--root` — a defaulted root does not count as
explicit.

If the named packages declare no default, the current root is used. If
they declare exactly one distinct default, the whole install is
re-rooted there. If they declare two or more different defaults, peipkg
stops and tells the operator to split the command or pass `--root`,
rather than picking one.

A dependency's placement is never governed by its own `default_root`;
only by the depending package's root and the dependency's `root` field.

## Cross-root garbage collection

Removing the last thing in a root that required a cross-root dependency
does not remove that dependency from the other root. Cross-root
autoremoval is not implemented; the dependency stays until something
removes it explicitly.
