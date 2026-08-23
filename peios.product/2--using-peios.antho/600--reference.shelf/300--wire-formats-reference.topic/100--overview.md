---
title: Wire formats reference
type: reference
description: Where every byte-level layout in Peios is specified — security descriptors, SIDs, conditional-ACE bytecode, claim entries, token and session specs, CAAP, and the KMES event envelope.
related:
  - peios/wire-formats-reference/security-descriptors
  - peios/wire-formats-reference/caap-format
  - peios/wire-formats-reference/token-and-session-specs
  - peios/constants-and-catalogs/overview
---

Byte-level layouts are specified normatively in the PCSA books and in the kernel manual's ABI appendices. This page is the map.

## Security descriptors and their parts

| Structure | Where |
|---|---|
| Security descriptor header, self-relative | PCDS §5.1 |
| ACL header and ACE array | PCDS §5.2 |
| ACE header and per-type body layouts | PCDS §5.4 |
| Access mask layout | PCDS §5.3 |
| Claim entry — `CLAIM_SECURITY_ATTRIBUTE_RELATIVE_V1` | PCDS §5.9 |
| Conditional-ACE bytecode, with the full opcode table | PCDS §5.11 |
| Resource attribute ACEs | PCDS §5.10 |

See also [Security descriptors](~peios/wire-formats-reference/security-descriptors).

## Identifiers

| Structure | Where |
|---|---|
| SID binary format | PCDS §4.1 |
| SID string format | PCDS §4.2 |
| GUID | PCDS §2 |
| LUID | PCDS §3 |

## Kernel interfaces

| Structure | Where |
|---|---|
| Token and session wire specs | Peios Kernel TRM §3.A — see [Token and session specs](~peios/wire-formats-reference/token-and-session-specs) |
| CAAP wire format | See [CAAP format](~peios/wire-formats-reference/caap-format) |
| Registry ABI, including watch record layout | Peios Kernel TRM §5.A |
| Token query class payloads | Peios Kernel TRM §3.A |

## Event stream

| Structure | Where |
|---|---|
| KMES event header, field by field | PSPK §2 |
| Event envelope, in summary | [Events Index](~peios/all-event-types) §1.2 |
| Per-event payload schemas | [Events Index](~peios/all-event-types), chapters 3 to 8 |

## Packages and repositories

The package container, manifest, signature and repository index formats are PSPU §5.
