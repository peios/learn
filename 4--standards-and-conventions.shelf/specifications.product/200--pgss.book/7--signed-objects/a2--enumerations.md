---
title: Enumerations
description: Every enumerated value of PSO, covering object kinds, key
  types, certificate roles, warrant types, warrant flags, hash forms,
  target types, and results. Every enumeration is closed.
---

Every enumeration here is closed (§7.15).

## Object kinds

The `kind` field of the header (§7.4).

| Value | Object | Defined in |
|---|---|---|
| `0x01` | Certificate | §7.6 |
| `0x02` | Leaf | §7.7 |
| `0x03` | Bundle | §7.8 |
| `0x04` | Revocation | §7.12 |
| `0x05` | Distrust | §7.13 |
| `0x06` | Store image | PSPK §6.3 |

## Key types

The `key_type` field of a certificate, and the type of a root (§7.4).

| Value | Algorithm |
|---|---|
| `0x01` | ML-DSA-65 |
| `0x02` | ML-DSA-87 |

## Certificate roles

The `role` field of a certificate (§7.6).

| Value | Role |
|---|---|
| `0x01` | Top-level |
| `0x02` | Intermediary |

## Warrant types

Bits 6 through 4 of a warrant's `flags` (§7.5).

| Value | Type |
|---|---|
| `0` | Set |
| `1` | Namespace |
| `2` | Limit |

## Hash forms

The `hash_form` field of a leaf (§7.9).

| Value | Form |
|---|---|
| `0x01` | Whole file |
| `0x02` | ELF, with signature sections zeroed |

## Target types

The `target_type` field of a revocation and of a distrust entry (§7.12,
§7.13).

| Value | Target |
|---|---|
| `0x01` | Certificate |
| `0x02` | Leaf |

## Results

The results a verifier reports are listed in §7.14 and are not repeated
here.
