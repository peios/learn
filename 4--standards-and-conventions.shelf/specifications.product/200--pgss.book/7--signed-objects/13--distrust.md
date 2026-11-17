---
title: Distrust
description: The layout of a distrust entry, how it differs from a
  revocation and from removing a top-level, and when an administrator's
  approval is needed.
---

**Distrust** is the act of an administrator: an unsigned entry that
refuses a certificate or a leaf on one system.

| Field | Type | Description |
|---|---|---|
| header | 6 bytes | `kind` is `0x05` (§7.4) |
| `target_type` | `u8` | `0x01` for a certificate, `0x02` for a leaf |
| `target` | `u8[64]` | The object hash of what is distrusted |

A distrust entry is kept in `/lcl/policy/pso/distrust/`, in a file named
by the hash it distrusts (§7.10). It never leaves the system it was
made on.

## Effect

A chain with a distrusted member is refused (§7.14). Distrust takes
precedence over everything that enables or approves: a distrusted
top-level is not enabled, whatever else the trust store holds.

Distrust and revocation differ in who acts, and in nothing a consumer
can see.

| | Revocation | Distrust |
|---|---|---|
| Made by | An authority above the target | The system's administrator |
| Signed | Yes | No |
| Applies to | Every system that receives it | The system it was made on |
| Can be removed | No | Yes, with approval |

Distrust also differs from removing a top-level from the trust store. A
top-level that is not enabled can still head a chain that a consumer
accepts on its own terms (§7.14). A distrusted one cannot.

## Approval

Adding a distrust entry takes trust away, and a store keeper MAY add one
without the approval §7.10 requires for a top-level.

Removing a distrust entry restores trust. A store keeper MUST obtain the
administrator's approval before it removes one, as it does before it
enables a top-level.
