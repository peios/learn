---
title: The Manifest
description: The canonical TOML that lists a package's paths and says what else is known about it, its fields, its tables, its entries, and the one form it is written in.
---

A package's **manifest** says what the package is: its ID, its metadata,
and every path it holds with that path's entry. It is TOML, in exactly one
form, and its identity is the package's (§5.11).

## Form

```toml
name = "se.curl.curl"
version = "8.22.0-1"
arch = "x86_64"
description = "Command line tool for transferring data with URLs"
homepage = "https://curl.se/"
license = "curl"
license_class = "free"

[dependencies]
"se.curl.libcurl" = "= 8.22.0-1"

[requires]
"libc.so.6" = ">= 2.34"

[files]
"bin/curl" = { blob = "sha256:3b1f…", exec = true }
"share/man/man1/curl.1" = { blob = "sha256:9a0c…" }
```

A manifest is, in this order:

1. `name`, `version` and `arch`, one line each: the package's ID (§5.3,
   §5.5, §5.8).
2. The descriptive fields that are present (§5.19), one line each, sorted
   by key: `description`, `homepage`, `license`, `license_class`,
   `source_license`.
3. The tables that are not empty, each after an empty line, in this order:
   `[claims]` (§5.23), `[dependencies]`, `[provides]` and `[requires]`
   (§5.21). Each table's keys are sorted by bytes, one `"key" = "value"`
   line each.
4. An empty line, then `[files]`, then one line for each path, sorted by
   the bytes of the path: the path as a TOML string, ` = `, and its entry.

Every key and string is written as §5.9 writes TOML strings. A constraint
is written as §5.7 writes it, with a single space between an operator and
its version and `, ` between expressions, and an empty string for any
version. A provided capability's version is written as its version, or as
an empty string for none.

An absent field and an empty table are left out, so a package with no
metadata has a manifest of its ID and its files alone.

## Entries

An entry is an inline table, with single spaces inside its braces and around
each `=`, and its keys in this order:

| Kind | Entry |
|---|---|
| File | `{ blob = "sha256:<hash>" }`, then `, exec = true` if it is executable, then `, descriptor = "<hex>"` and `, signature = "sha256:<hash>"` if present |
| Symbolic link | `{ symlink = "<target>" }` |
| Directory | `{ dir = true }`, then `, descriptor = "<hex>"` if present |

`exec` is written only when true. A descriptor is lowercase hexadecimal
(§5.20); a signature names the blob holding the file's PIP signature
(§5.16).

## Reading a manifest

A consumer MUST read a manifest as untrusted input. It MUST check that the
manifest's bytes hash to the identity it was asked for, that every path
meets §5.13, and that every field meets its section. It then writes the
manifest it read in this form and MUST refuse it if the bytes differ: that
one comparison refuses unknown keys, unsorted entries and every other
spelling.
