---
title: Package Names
description: What a package name may contain, how it is structured and cased, the filename convention, and the sub-package conventions.
---

A package's name identifies it within a repository and across every
repository that may serve it.

## Character set

A package name MUST consist of ASCII characters drawn from:

- lowercase letters `a`–`z`
- digits `0`–`9`
- hyphen `-`
- period `.`
- plus sign `+`

A package name MUST NOT contain uppercase letters, whitespace,
underscores, or any character outside that set.

## Structure

A package name MUST start with a lowercase letter or a digit, and MUST
end with a lowercase letter, a digit, or a plus sign.

The hyphen and the period are **separator** characters. The plus sign is
not a separator but an ordinary name character: it is intrinsic to names
such as `libstdc++` and `g++`, so it MAY repeat and MAY end a name.

A package name MUST NOT contain two consecutive separators — `--`, `..`,
`-.`, or `.-`.

A package name MUST be at least 2 and at most 64 characters long.

> [!NOTE]
> The character set admits the common upstream patterns: library
> suffixes (`libstdc++`), architecture prefixes (`lib32-foo`), and
> dotted module names (`python3.example`). Underscores are excluded so
> that the filename separator below stays unambiguous.

## Case

Package names are case-sensitive. Because uppercase letters are
forbidden, this is equivalent to byte-for-byte equality.

## Filename convention

A package file's name, on disk and in URLs, MUST be:

```
<name>_<version>_<architecture>.peipkg
```

The separator between fields is the underscore, and the extension is
`.peipkg`.

A filename is parsed by splitting at the **first** underscore and then
at the **second**: what precedes the first is the name, what lies
between them is the version, and what follows the second — up to the
`.peipkg` extension — is the architecture. The underscore MUST NOT
appear in the name (§5.3) or in the version (§5.5). It MAY appear in the
architecture (§5.8), and does in `x86_64`, which is why the architecture
field is defined as the remainder rather than as the text after the last
underscore.

Examples:

```
nginx_1.26.2-3_x86_64.peipkg
jq_1.7.1-2_x86_64.peipkg
peios-docs_0.22-1_noarch.peipkg
libstdc++_13.2.1-4_x86_64.peipkg
```

A consumer MUST NOT derive a package's identity from its filename. The
manifest is authoritative (§5.18); the filename is a convenience for
humans and for static hosting.

## Sub-package conventions

Packages shipping related but separable content SHOULD use a
hyphen-suffix convention:

| Suffix | Content |
|---|---|
| `-doc` | Documentation, man pages, examples |
| `-debug` | Debug symbols |
| `-dev` | Headers, static libraries, build-time dependencies |
| `-source` | Corresponding source (§5.14) |

These are advisory. The format does not enforce them, and other suffixes
MAY be used for other purposes.
