---
title: Derived Capabilities
description: Capabilities derived mechanically from built contents — shared libraries and pkg-config modules — and why derivation is the producer's job.
---

Some capabilities are derived mechanically from a package's built
contents rather than declared by hand. So that a producer and a consumer
agree on the name whichever way it arrived, the conventions below are
normative for the capability `name`.

| Capability | Virtual name | Version |
|---|---|---|
| Shared library | The ELF soname, verbatim — `libssl.so.3`. | None by default. |
| ELF symbol-version node | `elfver(<soname>:<token>)`, for example `elfver(libstdc++.so.6:GLIBCXX_3.4.30)`. | None: the whole name is an exact capability. |
| pkg-config module | `pkgconfig(<module>)`, where `<module>` is the `.pc` file's base name — `pkgconfig(glib-2.0)`. | The `.pc` file's `Version:` field, matched as an ordered constraint per §5.7. |

## Shared libraries

A shared-library dependency is the soname listed in a binary's
`DT_NEEDED`; the corresponding provide is the soname in the providing
library's `DT_SONAME`.

The soname's ABI-version field is part of the name and is matched by
exact equality: `libssl.so.3` is never satisfied by `libssl.so.4`. A
version MAY be carried on a soname provide when the library's symbol
versions are commensurable with the providing package's own version, as
they are for a C library shipping versioned symbols.

## ELF symbol-version nodes

A strong GNU ELF version need is represented by `elfver(<soname>:<token>)`;
the matching provide comes from that SONAME's non-base version definition.
Both components preserve case and exact bytes. The colon separates components;
it is not permitted within either component. Tokens use ASCII letters, digits,
underscores, dots, plus and minus characters; the complete capability obeys the
normal capability-name length bound. Weak version needs do not impose a mandatory
dependency. A producer must reject unrepresentable metadata rather than omit a
selected version requirement.

These capabilities supplement SONAME identity and are independent of the
provider package's version. All required nodes must be present; defining a
numerically greater node alone is insufficient. A token from another SONAME
does not satisfy the dependency. Producer policy selects the libraries to which
this derivation applies; Peios selects libstdc++ to cover GLIBCXX and CXXABI.

## pkg-config modules

A pkg-config dependency is a module named in a `.pc` file's `Requires:`
or `Requires.private:`; the corresponding provide is the `.pc` file
itself.

## Derivation is a producer concern

Whether a producer derives these automatically is its own business. This
section fixes only the names, so that a hand-written entry and a derived
entry for the same capability are byte-identical.

> [!NOTE]
> A producer that derives from ELF metadata will encounter cases this
> section does not name: a symlink that carries no `DT_SONAME` of its
> own, a shared-library-shaped file with no soname at all, symbol
> version tokens from `DT_VERNEED` that could be turned into a version
> constraint. Any additional constraint a producer synthesises is a
> constraint like any other and is evaluated by §5.7; what this section
> forbids is inventing a different *name* for a capability that has one.
