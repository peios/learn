---
title: Document Conventions
description: The rules every file this chapter defines obeys, its encoding, its one canonical form, its identities and its names.
---

## Encoding

Every file this chapter defines is UTF-8 text, with LF line endings and a
newline at the end of its last line, except the signature of a pointer file
(§5.33) and the content of blobs (§5.12), which are bytes.

## One form

A manifest (§5.18), an inventory (§5.25), a tree node (§5.31) and a pointer
file (§5.32) are hashed, so each has exactly one spelling. Each section
that defines one says how it is written. A consumer MUST refuse one that is
not in that form, even if it means the same: it reads the file, writes it
again, and refuses it if the bytes differ.

Manifests and profiles are TOML. A TOML string in a file this chapter
defines is a basic string, with `"` and `\` escaped by a backslash, every
ASCII control character written `\uXXXX` with uppercase hexadecimal digits,
and everything else as literal UTF-8.

The other files are line formats: one record a line, its fields separated
by single spaces, no other whitespace, and lines sorted by bytes where the
section says they are sorted.

## Identities

An identity is `sha256:` and the 64 lowercase hexadecimal digits of the
SHA-256 hash of some bytes. SHA-256 is the only hash algorithm of this
version. Where a file is named by its hash, the name is the 64 digits alone.

## Names of closures, indexes, channels, and repositories

A closure name (§5.27), an index or channel name (§5.30) and a repository
name (§5.35) are each 1 to 64 ASCII letters, digits, `-`, `.` and `_`, not
starting with `.`. A closure name MUST also not end with `.manifest`, and
MUST NOT be 64 hexadecimal digits, so that it can't be taken for a closure.

## Keywords

The key words MUST, MUST NOT, REQUIRED, SHOULD, SHOULD NOT, RECOMMENDED,
MAY and OPTIONAL are to be read as BCP 14 describes, when they appear in
capitals.
