---
title: Package Names
description: What a package name can contain, its reverse-DNS structure, and the conventions for related packages.
---

A package's name says who owns the software and what it is: the owner's
domain, backwards, then the product, as in `dev.peios.hello`,
`org.gnu.gcc-c++` and `io.github.eudev-project.eudev`.

## Structure

A package name MUST consist of at least 3 labels separated by `.`, and MUST
be at most 64 characters long.

Each label MUST consist of lowercase ASCII letters `a` to `z`, digits `0` to
`9`, `+` and `-`. It MUST start with a letter or a digit, MUST NOT end with
`-`, and MUST NOT contain `--`.

The first label MUST consist of letters only, and the first two labels MUST
NOT contain `+`.

```text
dev.peios.hello
org.gnu.gcc-c++
se.curl.curl
io.github.eudev-project.eudev
```

## Case

Names are case-sensitive, and since uppercase letters are not permitted,
two names are the same name exactly when they are the same bytes.

## Conventions

Packages holding related but separable content SHOULD add a suffix to the
main package's name:

| Suffix | Content |
|---|---|
| `-devel` | Headers, static libraries, and other build-time files |
| `-libs` | The shared libraries of a program, alone |
| `-static` | Static libraries |

These are conventions. Nothing enforces them, and a name MAY use others.
