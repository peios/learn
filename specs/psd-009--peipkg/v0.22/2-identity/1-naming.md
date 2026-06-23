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

Package names MUST end with a lowercase letter, digit, or plus
sign (`+`).

The hyphen `-` and period `.` are separator characters. The plus
sign `+` is NOT a separator but a regular name character — it is
intrinsic to names such as `libstdc++` and `g++`, so it MAY repeat
(`++`) and MAY end a name.

Package names MUST NOT contain two consecutive separator
characters (`--`, `..`, `-.`, `.-`).

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

## Virtual (capability) names

The `name` of a `dependencies`, `optional_dependencies`, or
`provides` entry (§4.1) MAY be a **virtual name** rather than a
real package name. Virtual names express capabilities a package
provides or requires that are not themselves package names —
most importantly machine-derived capabilities such as ELF
sonames and pkg-config modules (§4.1.5).

A virtual name uses a grammar that is a strict SUPERSET of the
package-name grammar above, in two respects:

1. **Uppercase letters are permitted.** A virtual name often
   mirrors an exact machine identifier — an ELF soname
   (`libGL.so.1`, `libICE.so.6`) or a foreign module name —
   that is case-sensitive. Folding case would be unsound (a
   case-sensitive dynamic loader treats `libGL.so.1` and
   `libgl.so.1` as distinct), so case MUST be preserved.

2. **A namespaced form `namespace(argument)` is permitted**, for
   capabilities drawn from a foreign namespace. The `namespace`
   is lowercase letters and digits beginning with a letter; the
   `argument` is bracketed by parentheses, is non-empty, and may
   contain letters, digits, the separators `- . +`, and
   additionally `_ : /` (so that `pkgconfig(gtk+-3.0)`,
   `perl(Foo::Bar)`, and `python3dist(ruamel.yaml)` are
   well-formed).

Outside the namespaced form, a virtual name uses the
package-name character set extended with the underscore `_`
(common in real sonames such as `libgcc_s.so.1` and
`libnss_files.so.2`). It MUST start with a letter or digit and
MUST end with a letter, digit, or `+` (real identifiers such as
`g++` and `libstdc++` end in a plus). Unlike package names, a
virtual name MAY contain consecutive separators
(`libstdc++.so.6`). A virtual name MUST be 2 to 128 characters
long.

`conflicts` and `replaces` entries target real packages and so
MUST use the package-name grammar (§2.1), not the virtual-name
grammar.

> [!INFORMATIVE]
> Virtual names share a namespace with real package names: a
> dependency on `libssl` is satisfied by a package literally
> named `libssl` or by any package whose `provides` includes
> `libssl`. The namespaced form keeps machine-derived
> capabilities from colliding with package names —
> `pkgconfig(zlib)` is unambiguously the pkg-config module, not
> a package.

