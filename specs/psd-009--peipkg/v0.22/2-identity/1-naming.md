---
title: Naming
---

A package's name identifies it within a repository and across
all repositories that may serve it. Two packages with the same
name installed simultaneously is a conflict (§4.1).

## Character set

Package names MUST consist of ASCII characters from the
following set:

- Lowercase letters `a` through `z`
- Digits `0` through `9`
- Hyphen `-`
- Period `.`
- Plus sign `+`

Package names MUST NOT contain uppercase letters, whitespace,
underscores, or any character outside the set above.

## Structural constraints

Package names MUST start with a lowercase letter or digit.

Package names MUST end with a lowercase letter or digit.

Package names MUST NOT contain two consecutive separator
characters (`--`, `..`, `++`, `-.`, `.+`, etc.).

Package names MUST be at least 2 characters long.

Package names MUST NOT exceed 64 characters.

> [!INFORMATIVE]
> The character set permits common upstream naming patterns
> including library suffixes (`libstdc++`), architecture
> prefixes (`lib32-foo`), and dotted module names
> (`python3.example`). Underscores are excluded to keep the
> filename separator (§2.1.4) unambiguous.

## Case sensitivity

Package names are case-sensitive. Because uppercase letters
are forbidden, this is equivalent to byte-for-byte equality.

## Filename convention

A package file's name on disk and in URLs MUST follow the
format:

```
<name>_<version>_<architecture>.peipkg
```

Where:

- `<name>` is the package name.
- `<version>` is the full version string (§2.2).
- `<architecture>` is the architecture identifier (§2.3).
- The separator between fields is the underscore (`_`).
- The file extension is `.peipkg`.

Examples:

```
nginx_1.26.2-3_x86_64.peipkg
jq_1.7.1-2_x86_64.peipkg
peios-docs_0.22-1_noarch.peipkg
libstdc++_13.2.1-4_x86_64.peipkg
```

The underscore separator is REQUIRED and MUST NOT appear within
any field. This makes filenames unambiguously parseable: the
first underscore separates name from version, the last
underscore separates version from architecture.

## Sub-package conventions

Packages that ship related but separable content SHOULD be
named using a hyphen-suffix convention:

| Suffix | Purpose |
|---|---|
| `-doc` | Documentation, man pages, examples |
| `-debug` | Debug symbols |
| `-dev` | Headers, static libraries, build dependencies |

These conventions are advisory. The package format does not
enforce them, and other suffixes MAY be used for other purposes.

