---
title: Well-known SIDs
type: reference
description: Catalog of SIDs whose values are defined by Peios rather than allocated at runtime. Organised by authority — universal, NT Authority, BUILTIN, integrity, PIP trust, confinement, capabilities.
related:
  - peios/constants-and-catalogs/overview
  - peios/identity/well-known-principals
  - peios/identity/sids
  - peios/wire-formats-reference/security-descriptors
---

This page is the catalog. The conceptual material — what each principal means, when to use which SID, how the principals interact with the access check — is in [Well-known principals](~peios/identity/well-known-principals). Use this page when you need a specific SID value.

The catalog is organised by **identifier authority** — the second number in the SID string.

## Universal SIDs (authorities 0, 1, 2, 3)

These authorities are globally-defined; their SIDs mean the same thing on every Peios system.

| SID | Name | Notes |
|---|---|---|
| `S-1-0-0` | Nobody | Matches nothing. Used as a deliberate placeholder. |
| `S-1-1-0` | Everyone | Matches every token, including Anonymous. |
| `S-1-2-0` | Local | Matches tokens from local logons. |
| `S-1-2-1` | Console Logon | Matches tokens from physical/console sessions. |
| `S-1-3-0` | Creator Owner | Placeholder. Substituted with the new object's owner at inheritance. |
| `S-1-3-1` | Creator Group | Placeholder. Substituted with the new object's primary group. |
| `S-1-3-4` | Owner Rights | Special. Suppresses owner implicit rights when present in a DACL. |

## NT Authority SIDs (authority 5)

The largest set of well-known SIDs.

### Logon classifiers and system actors

| SID | Name | Notes |
|---|---|---|
| `S-1-5-2` | Network | Token came from a network logon. |
| `S-1-5-4` | Interactive | Token came from an interactive logon. |
| `S-1-5-6` | Service | Token came from a service start. |
| `S-1-5-7` | Anonymous | Anonymous-level identity. |
| `S-1-5-10` | Principal Self | Placeholder; substituted with the caller-supplied `self_sid` at access check. |
| `S-1-5-11` | Authenticated Users | Every authenticated token. Excludes Anonymous. |
| `S-1-5-18` | Local System (SYSTEM) | The kernel and TCB. |
| `S-1-5-19` | Local Service | Built-in service account, reduced privileges. |
| `S-1-5-20` | Network Service | Built-in service account, network-authenticating. |

### Logon SID pattern

| Pattern | Meaning |
|---|---|
| `S-1-5-5-X-Y` | The session-specific SID for one authentication event. X and Y are derived from the session's LUID (high and low 32 bits). Every token of the session carries this SID with `SE_GROUP_LOGON_ID` set. |

`S-1-5-5-0-0` specifically is the bootstrap SYSTEM session's logon SID. Other sessions get derived values.

### BUILTIN aliases (sub-authority 32)

| SID | Name |
|---|---|
| `S-1-5-32-544` | BUILTIN\Administrators |
| `S-1-5-32-545` | BUILTIN\Users |
| `S-1-5-32-546` | BUILTIN\Guests |
| `S-1-5-32-547` | BUILTIN\Power Users |
| `S-1-5-32-551` | BUILTIN\Backup Operators |
| `S-1-5-32-555` | BUILTIN\Remote Desktop Users |
| `S-1-5-32-559` | BUILTIN\Performance Log Users |
| `S-1-5-32-560` | BUILTIN\Performance Monitor Users |
| `S-1-5-32-562` | BUILTIN\Distributed COM Users |
| `S-1-5-32-568` | BUILTIN\IIS_IUSRS |
| `S-1-5-32-569` | BUILTIN\Cryptographic Operators |
| `S-1-5-32-573` | BUILTIN\Event Log Readers |
| `S-1-5-32-574` | BUILTIN\Certificate Service DCOM Access |
| `S-1-5-32-575` | BUILTIN\RDS Remote Access Servers |
| `S-1-5-32-578` | BUILTIN\Hyper-V Administrators |
| `S-1-5-32-579` | BUILTIN\Access Control Assistance Operators |
| `S-1-5-32-580` | BUILTIN\Remote Management Users |
| `S-1-5-32-583` | BUILTIN\Device Owners |

The full BUILTIN catalog uses values 544 through 583 (with gaps). v0.20 recognises all of them by convention; specific entries beyond Administrators, Users, Guests, and Backup Operators are typically not used in default deployments.

### Domain SIDs

| Pattern | Meaning |
|---|---|
| `S-1-5-21-DA1-DA2-DA3-RID` | A principal in a specific domain. DA1-DA2-DA3 identifies the domain; RID identifies the principal. |

Reserved RIDs within `S-1-5-21-*`:

| RID | Meaning |
|---|---|
| 500 | Domain Administrator |
| 501 | Domain Guest |
| 502 | krbtgt (Kerberos ticket-granting account) |
| 512 | Domain Admins |
| 513 | Domain Users |
| 514 | Domain Guests |
| 515 | Domain Computers |
| 516 | Domain Controllers |
| 517 | Cert Publishers |
| 518 | Schema Admins |
| 519 | Enterprise Admins |
| 520 | Group Policy Creator Owners |
| 521 | Read-only Domain Controllers |
| 522 | Cloneable Domain Controllers |
| 525 | Protected Users |
| 526 | Key Admins |
| 527 | Enterprise Key Admins |

Principals beyond these reserved RIDs get RIDs ≥ 1000.

### Service SIDs

| Pattern | Meaning |
|---|---|
| `S-1-5-80-h1-h2-h3-h4-h5` | Service SID derived from service name. The 5 hash values come from SHA-1 of UTF-16LE-uppercased service name, split into 5 little-endian 32-bit integers. |

## Mandatory integrity labels (authority 16)

These are labels, not principals. The integer RID encodes the integrity level.

| SID | Level RID | Name |
|---|---|---|
| `S-1-16-0` | 0 | Untrusted |
| `S-1-16-4096` | 4096 | Low |
| `S-1-16-8192` | 8192 | Medium |
| `S-1-16-12288` | 12288 | High |
| `S-1-16-16384` | 16384 | System |

The values are spaced by 4096 to leave room for additional levels.

## Process integrity protection labels (authority 19)

PIP labels are also not principals; they encode the (type, trust) pair.

| Pattern | Meaning |
|---|---|
| `S-1-19-T-L` | PIP label. T = PIP type (0, 512, or 1024). L = trust level within the type. |

Specific values used in v0.20:

| SID | Type | Trust | Name |
|---|---|---|---|
| `S-1-19-0-0` | None (0) | 0 | No PIP protection |
| `S-1-19-512-1024` | Protected (512) | 1024 | Authenticode-signed third-party |
| `S-1-19-512-1536` | Protected | 1536 | AntiMalware |
| `S-1-19-512-2048` | Protected | 2048 | Peios-distributed app |
| `S-1-19-512-4096` | Protected | 4096 | Core Peios component |
| `S-1-19-512-8192` | Protected | 8192 | Peios TCB |
| `S-1-19-1024-8192` | Isolated (1024) | 8192 | Reserved — no v0.20 signing key targets Isolated |

## Confinement SIDs (authority 15, sub-authority 2)

| SID | Name |
|---|---|
| `S-1-15-2-1` | ALL_APPLICATION_PACKAGES |
| `S-1-15-2-2` | ALL_RESTRICTED_APPLICATION_PACKAGES |

Plus per-application confinement SIDs:

| Pattern | Meaning |
|---|---|
| `S-1-15-2-h1-h2-h3-h4-h5-h6-h7-h8` | Application-specific confinement SID derived from the application's package identifier. SHA-256 split into 8 little-endian 32-bit integers. |

## Capability SIDs (authority 15, sub-authority 3)

### Well-known capabilities

| SID | Capability |
|---|---|
| `S-1-15-3-1` | internetClient |
| `S-1-15-3-2` | internetClientServer |
| `S-1-15-3-3` | privateNetworkClientServer |
| `S-1-15-3-4` | (reserved) |
| `S-1-15-3-5` | (reserved) |
| `S-1-15-3-6` | (reserved) |
| `S-1-15-3-7` | (reserved) |
| `S-1-15-3-8` | enterpriseAuthentication |
| `S-1-15-3-9` | sharedUserCertificates |
| `S-1-15-3-10` | removableStorage |

### Derived capabilities

| Pattern | Meaning |
|---|---|
| `S-1-15-3-h1-h2-h3-h4-h5-h6-h7-h8` | Capability SID derived from capability name. SHA-256 split into 8 little-endian 32-bit integers. Same name → same SID. |

## SID-and-attributes flags

When a SID appears in a group list (or in restricted SIDs, confinement capabilities, etc.), it carries a 32-bit attributes value. The defined flags:

| Flag | Value | Meaning |
|---|---|---|
| `SE_GROUP_MANDATORY` | 0x00000001 | Group cannot be disabled. |
| `SE_GROUP_ENABLED_BY_DEFAULT` | 0x00000002 | Enabled at token creation. |
| `SE_GROUP_ENABLED` | 0x00000004 | Currently enabled. |
| `SE_GROUP_OWNER` | 0x00000008 | Can be selected as object owner. |
| `SE_GROUP_USE_FOR_DENY_ONLY` | 0x00000010 | Matches only deny ACEs; permanent. |
| `SE_GROUP_INTEGRITY` | 0x00000020 | Identifies an integrity SID (ABI parity; MIC uses `integrity_level` field, not this flag). |
| `SE_GROUP_INTEGRITY_ENABLED` | 0x00000040 | Used with `SE_GROUP_INTEGRITY`. |
| `SE_GROUP_RESOURCE` | 0x20000000 | Domain-local group from resource domain (metadata only in v0.20). |
| `SE_GROUP_LOGON_ID` | 0xC0000000 | The per-session logon SID. Cannot be disabled. |

## SID format constants

For reference:

| Constant | Value | Meaning |
|---|---|---|
| SID revision | `0x01` | Set in byte 0 of every binary SID. |
| Max SubAuthority count | 15 | Maximum value of byte 1. |
| SID min size | 8 bytes | Revision + count + authority, no sub-authorities. |
| SID max size | 68 bytes | Revision + count + authority + 15 × 4-byte sub-authorities. |
