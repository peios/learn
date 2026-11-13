---
title: Capabilities
description: Names that a package provides or requires besides package names, such as sonames, their grammar, and the one namespace they share with package names.
---

A **capability** is a name that a package provides and another requires,
such as the soname `libc.so.6`, the command `sh`, or the pkg-config module
`pkgconfig(zlib)`. A requirement names a capability (§5.21); a provide
offers one at a version, or at none. Capabilities derived from a package's
own files are §5.22's.

## Grammar

A capability is 2 to 128 characters long, and is one of:

- **A plain name:** ASCII letters of either case, digits, `-`, `.`, `+` and
  `_`, starting with a letter or a digit and ending with a letter, a digit,
  or `+`. Case MUST be preserved: a dynamic loader treats `libGL.so.1` and
  `libgl.so.1` as two libraries.
- **A namespaced name**, `namespace(argument)`: the namespace is lowercase
  letters and digits starting with a letter, and the argument is not empty
  and holds what a plain name can, and `:` and `/`, as in
  `pkgconfig(gtk+-3.0)`, `perl(Foo::Bar)` and
  `elfver(libstdc++.so.6:GLIBCXX_3.4.32)`.

## One namespace

Capabilities and package names share one namespace: every package provides
its own name, at its own version, as a capability. A requirement on
`dev.peios.hello` is satisfied by that package, or by any package that
provides that capability.

The namespaced form keeps capabilities from foreign naming schemes from
colliding with package names: `pkgconfig(zlib)` is the pkg-config module,
never a package.
