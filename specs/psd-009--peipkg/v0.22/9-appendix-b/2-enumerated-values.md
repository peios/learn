---
title: Enumerated Values
---

> [!INFORMATIVE]
> This appendix consolidates all enumerated value sets
> defined normatively elsewhere. Where this appendix and
> a normative chapter conflict, the normative chapter
> wins.

## Architecture identifiers

Defined normatively in §2.3.2.

| Identifier | Triplet | Defining section |
|---|---|---|
| `x86_64` | `x86_64-linux-peios` | §2.3.2 |
| `aarch64` | `aarch64-linux-peios` | §2.3.2 |
| `noarch` | (none) | §2.3.3 |

`x86_64` is the primary target. `aarch64` is secondary.
`noarch` is for architecture-independent packages.

## Side-effect identifiers

Defined normatively in §4.3.4.

| Identifier | When required | Tool invoked | Defining subsection |
|---|---|---|---|
| `ldconfig` | Package contains shared libraries | `ldconfig` (no flags) | §4.3.4.1 |
| `depmod` | Package contains kernel modules | `depmod <kernel-version>` | §4.3.4.2 |
| `man-db` | Package contains man pages (SHOULD) | `mandb -q` | §4.3.4.3 |

The set is closed in this version. A v0.22-conformant
implementation MUST reject manifests declaring side-effect
identifiers outside this set.

## Pre-release rank tokens

Defined normatively in §2.2.7.2.

| Token | Rank |
|---|---|
| `dev` | 0 |
| `alpha` | 1 |
| `a` | 1 |
| `beta` | 2 |
| `b` | 2 |
| `pre` | 3 |
| `rc` | 4 |
| (any other alphabetic segment) | 5 |

Rank 0 is lowest (sorts first). Rank 5 tokens are compared
lexically against each other.

Token matching is case-insensitive (`Alpha`, `ALPHA`, and
`alpha` all rank 1).

## Hash algorithms

Defined normatively in §3.5.5.

| Algorithm | Identifier | Status in v0.22 |
|---|---|---|
| SHA-256 | `sha256` | REQUIRED to support; only valid value |
| BLAKE3 | `blake3` | RESERVED for future versions |

A v0.22-conformant implementation MUST reject any algorithm
identifier other than `sha256`.

## Signature algorithms

Defined normatively in §5.2.1.

| Algorithm | Identifier | Status in v0.22 |
|---|---|---|
| Ed25519 | `ed25519` | REQUIRED to support; only valid value |

A v0.22-conformant implementation MUST reject any algorithm
identifier other than `ed25519`.

## Signing key statuses

Defined normatively in §6.1.4.

| Status | Used for new signatures | Acceptable for verification |
|---|---|---|
| `active` | yes | yes |
| `transitioning` | no | yes, until `valid_until` |
| `revoked` | no | no, regardless of cryptographic validity |

A status value other than `active`, `transitioning`, or
`revoked` is INVALID.

`transitioning` keys MUST carry a `valid_until` RFC 3339
timestamp; consumers MUST reject signatures from a
transitioning key after that timestamp.

`revoked` keys MAY remain in the descriptor for at least
one year after revocation as a public compromise
acknowledgement; signatures from revoked keys MUST be
rejected regardless.

## Signature policy

Defined normatively in §6.5.3.

| Policy | Unsigned packages | Description |
|---|---|---|
| `required` | rejected | All content MUST be signed and verify |
| `optional` | accepted with per-operation warning | Signed content verified; unsigned permitted with continuous warning |

The default for newly-added repositories SHOULD be
`required`.

There is no silently-accept-unsigned policy. Consumers
intentionally permitting unsigned content use `optional`,
which always emits a per-operation warning to the
operator.

## Index kind values

Defined normatively in §6.2.2 and §6.3.3.

| Kind | Description | Defining section |
|---|---|---|
| `active` | Current versions only | §6.2 |
| `archive` | All versions ever shipped | §6.3 |

## Constraint operators

Defined normatively in §2.2.8.

| Operator | Meaning |
|---|---|
| `=` | Exactly equal |
| `>` | Strictly greater than |
| `>=` | Greater than or equal |
| `<` | Strictly less than |
| `<=` | Less than or equal |
| `!=` | Not equal |

A bare version string with no operator is equivalent to
`=`. Multiple constraints are combined with comma-AND.

## Reserved metadata paths

Defined normatively in §3.2.1, §3.2.2.

| Path | Required | Section |
|---|---|---|
| `.peipkg/manifest.json` | yes | §3.3 |
| `.peipkg/files.json` | yes | §3.5.1 |
| `.peipkg/signature` | yes (signed packages) | §5.1 |

The `.peipkg/` prefix is reserved; payload entries MUST
NOT use it.

## Permitted top-level install paths

Defined normatively in §3.4.1.

| Path | Purpose |
|---|---|
| `/usr/bin/` | User-facing and system binaries |
| `/usr/lib/<triplet>/` | Architecture-specific libraries and data |
| `/usr/share/` | Architecture-independent data |
| `/usr/include/` | Header files |
| `/etc/` | Default (seed) configuration files |
| `/var/` | Runtime variable state directories |
| `/opt/` | Self-contained third-party software trees |

Payload entries MUST NOT install under any other top-level
path.
