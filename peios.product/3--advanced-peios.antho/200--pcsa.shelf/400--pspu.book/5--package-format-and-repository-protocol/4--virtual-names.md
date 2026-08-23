---
title: Virtual Names
description: A capability expressed as a name rather than a package — the grammar, and why virtual and real names share one namespace.
---

The `name` of a `dependencies`, `optional_dependencies`, or `provides`
entry (§5.21) MAY be a **virtual name** rather than a real package name.
A virtual name expresses a capability that is required or provided but
is not itself a package — most importantly a machine-derived capability
such as an ELF soname or a pkg-config module (§5.22).

`conflicts` and `replaces` entries target real packages, and so MUST use
the package-name grammar of §5.3, not the grammar below.

## Grammar

The virtual-name grammar is a strict superset of the package-name
grammar, in two respects.

**Uppercase letters are permitted.** A virtual name often mirrors an
exact machine identifier — `libGL.so.1`, `libICE.so.6`, a foreign module
name — which is case-sensitive. Case MUST be preserved: folding it would
be unsound, because a case-sensitive dynamic loader treats `libGL.so.1`
and `libgl.so.1` as distinct.

**A namespaced form `namespace(argument)` is permitted**, for
capabilities drawn from a foreign namespace. The `namespace` is
lowercase letters and digits, beginning with a letter. The `argument` is
bracketed by parentheses, is non-empty, and may contain letters, digits,
the separators `-`, `.`, `+`, and additionally `_`, `:`, and `/` — so
that `pkgconfig(gtk+-3.0)`, `perl(Foo::Bar)`, and
`python3dist(ruamel.yaml)` are all well-formed.

Outside the namespaced form, a virtual name uses the package-name
character set extended with the underscore `_`, which is common in real
sonames (`libgcc_s.so.1`, `libnss_files.so.2`). It MUST start with a
letter or a digit and MUST end with a letter, a digit, or `+`. Unlike a
package name, a virtual name MAY contain consecutive separators, so that
`libstdc++.so.6` is well-formed.

A virtual name MUST be at least 2 and at most 128 characters long.

## One namespace

Virtual names share a namespace with real package names. A dependency on
`libssl` is satisfied by a package literally named `libssl`, or by any
package whose `provides` includes `libssl`.

The namespaced form exists to keep machine-derived capabilities from
colliding with package names: `pkgconfig(zlib)` is unambiguously the
pkg-config module, never a package.
