---
title: Payload Paths
description: A payload entry's tar path is its install location — the constraints on it, why nothing is canonicalised, and what an empty payload means.
---

A payload entry's tar path is its install location, resolved against the
installation root (§5.19). A tar entry at `usr/bin/nginx` installs to
`/usr/bin/nginx`.

## Constraints

A payload path MUST:

- be relative — it MUST NOT begin with `/`
- contain no segment equal to `.` or `..`, or any encoding thereof
- be valid UTF-8 (RFC 3629)
- contain no NUL byte (`0x00`) and no ASCII control character
  (`0x01`–`0x1F`, `0x7F`)
- contain no backslash (`\`)
- be in Unicode Normalization Form C, per Unicode 16.0
- have every component at most 255 bytes when encoded as UTF-8
- be at most 4096 bytes in total when encoded as UTF-8
- have at most 256 components
- not begin with `.peipkg/`, and not be literally `.peipkg` (§5.12)

A consumer MUST validate every payload path against these constraints
**before any further processing of the entry**. A package containing a
non-conforming payload path MUST be rejected.

## No canonicalisation

Path resolution MUST NOT canonicalise away `..` or `.` segments by
interpretation. Such segments are forbidden above; any appearance is a
format error, not a question of path canonicalisation.

> [!NOTE]
> The distinction matters. A consumer that normalises `a/../b` to `b`
> and proceeds has accepted a path this specification forbids, and has
> done so by a rule the producer never agreed to. Rejecting is the only
> behaviour both sides can predict.

## Empty payloads

A package MAY have zero payload entries. Such a package carries only
metadata; installing it records the package and runs any declared side
effects (§5.24).

> [!NOTE]
> An empty-payload package is useful as a virtual aggregator: it ships
> no binaries of its own and exists to declare dependencies on a curated
> set of other packages.
