---
title: Enumerated Values
description: Every closed set in this version — architectures, pre-release ranks, constraint operators, side-effect identifiers and hash algorithms.
---

Every set below is **closed** in this version. A conforming
implementation MUST reject a value outside it, and a new value requires
a `schema_version` bump (§5.38).

## Architecture identifiers

| Identifier | Triplet | Notes |
|---|---|---|
| `x86_64` | `x86_64-linux-peios` | primary target |
| `aarch64` | `aarch64-linux-peios` | secondary target |
| `noarch` | none | architecture-independent |

Defined in §5.8.

## Pre-release rank tokens

| Token | Rank |
|---|---|
| `dev` | 0 |
| `alpha` | 1 |
| `a` | 1 |
| `beta` | 2 |
| `b` | 2 |
| `pre` | 3 |
| `rc` | 4 |
| any other alphabetic segment | 5 |

Rank 0 sorts lowest. Rank-5 tokens compare lexically against each other.
Recognition is case-insensitive. Defined in §5.6.

## Constraint operators

| Operator | Meaning |
|---|---|
| `=` | exactly equal |
| `>` | strictly greater than |
| `>=` | greater than or equal |
| `<` | strictly less than |
| `<=` | less than or equal |
| `!=` | not equal |

A bare version with no operator means `=`. Comma is the AND separator.
Defined in §5.7.

## Side-effect identifiers

| Identifier | Declared when | Invoked as |
|---|---|---|
| `ldconfig` | the payload contains shared libraries (MUST) | the tool, with no operand |
| `depmod` | the payload contains kernel modules (MUST) | once per affected kernel release, naming it |
| `man-db` | the payload contains man pages (SHOULD) | the tool, in quiet mode |

Defined in §5.24.

## Hash algorithms

| Algorithm | Identifier | Status |
|---|---|---|
| SHA-256 | `sha256` | REQUIRED; the only valid value |
| BLAKE3 | `blake3` | RESERVED for a future version |

Defined in §5.25.

## Signature algorithms

| Algorithm | Identifier | Status |
|---|---|---|
| Ed25519 | `ed25519` | REQUIRED; the only valid value |

Defined in §5.29.

## Signing key statuses

| Status | Signs new content | Accepted for verification |
|---|---|---|
| `active` | yes | yes |
| `transitioning` | no | until `valid_until` |
| `revoked` | no | never, regardless of cryptographic validity |

Defined in §5.32.

## Index kinds

| Kind | Content |
|---|---|
| `active` | the current version of each package |
| `archive` | every version ever shipped |

Defined in §5.33 and §5.35.

## Signature policies

| Policy | Unsigned content |
|---|---|
| `required` | rejected |
| `optional` | accepted with a per-operation warning |

There is no silently-accept-unsigned policy. Defined in §5.37.

## Reserved metadata paths

| Path | Required |
|---|---|
| `.peipkg/manifest.json` | yes |
| `.peipkg/files.json` | yes |
| `.peipkg/signature` | in every signed package |

The `.peipkg/` prefix is reserved; a payload entry MUST NOT use it.
Defined in §5.12.

## Permitted entry types

| Type | Typeflag |
|---|---|
| Regular file | `0` or `\0` |
| Directory | `5` |
| Symbolic link | `2` |

Every other type MUST cause the package to be rejected. Defined in
§5.12.

## Permitted top-level install destinations

`/usr/bin/`, `/usr/sbin/`, `/usr/lib/<triplet>/`, `/usr/lib/debug/`,
`/usr/lib/modules/<release>/`, `/usr/lib/firmware/`,
`/usr/lib/os-release`, `/usr/libexec/`, `/usr/share/`, `/usr/include/`,
`/usr/src/debug/`, `/usr/src/dist/`, `/usr/etc/`, `/usr/conf/`, `/var/`,
`/boot/`, `/hooks/`, `/++/`.

A payload entry MUST NOT install under any other top-level path, unless
the package declares itself a special system package **and** the
operator has separately opted in. `/lcl/policy` is unreachable under
every circumstance. Defined in §5.14.

## Permitted claim path locations

The destinations above, plus `/run/` and the well-known root-level name
`/init`. Defined in §5.23.
