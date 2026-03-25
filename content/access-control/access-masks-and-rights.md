---
title: Understanding Access Masks and Rights
type: concept
order: 50
---

Every access request and every access grant on Peios is expressed as an **access mask** — a 32-bit value where each bit represents a specific right. When a thread opens a file, it requests a mask of the rights it needs. When AccessCheck evaluates the request, it computes a mask of the rights granted. If the granted mask covers the requested mask, access succeeds.

## How the mask is organized

The 32 bits are divided into regions, each serving a different purpose:

| Bits | Region | Description |
|---|---|---|
| 0–15 | **Specific rights** | Defined by the object type — different meanings for files, registry keys, processes, etc. |
| 16–20 | **Standard rights** | The same five rights on every object type |
| 24 | **ACCESS_SYSTEM_SECURITY** | The right to read or modify the SACL |
| 25 | **MAXIMUM_ALLOWED** | Requests the maximum rights the token can get (not a real right — a query flag) |
| 28–31 | **Generic rights** | Convenience aliases mapped to specific + standard rights by each object type |

Bits 21–23 and 26–27 are reserved.

## Standard rights

These five rights mean the same thing regardless of what type of object you are accessing:

| Right | Meaning |
|---|---|
| **DELETE** | Delete the object |
| **READ_CONTROL** | Read the object's security descriptor (except the SACL) |
| **WRITE_DAC** | Modify the object's DACL |
| **WRITE_OWNER** | Change the object's owner |
| **SYNCHRONIZE** | Wait on the object (where applicable) |

These appear in ACEs alongside specific rights. An ACE might grant `READ_CONTROL | FILE_READ_DATA` — a standard right and a specific right in the same mask.

## Specific rights

Bits 0–15 are defined by each object type. The same bit position means different things on different objects:

| Bit | File | Registry key |
|---|---|---|
| 0 | `FILE_READ_DATA` | `KEY_QUERY_VALUE` |
| 1 | `FILE_WRITE_DATA` | `KEY_SET_VALUE` |
| 2 | `FILE_APPEND_DATA` | `KEY_CREATE_SUB_KEY` |
| 3 | `FILE_READ_EA` | `KEY_ENUMERATE_SUB_KEYS` |
| 4 | `FILE_WRITE_EA` | `KEY_NOTIFY` |
| 5 | `FILE_EXECUTE` | `KEY_CREATE_LINK` |
| 6 | `FILE_DELETE_CHILD` | — |
| 7 | `FILE_READ_ATTRIBUTES` | — |
| 8 | `FILE_WRITE_ATTRIBUTES` | — |

This is why AccessCheck does not need to know what type of object it is evaluating. The bits are just bits — the meaning is assigned by the object type that calls AccessCheck. The evaluator compares masks; the caller decides what the bits represent.

## Generic rights

Generic rights are convenience aliases for common combinations of specific and standard rights. They allow ACEs to be written in terms of intent — "read access" or "full control" — without listing every individual bit.

| Generic right | Intent |
|---|---|
| **GENERIC_READ** | Read the object's contents and metadata |
| **GENERIC_WRITE** | Modify the object's contents and metadata |
| **GENERIC_EXECUTE** | Execute or traverse the object |
| **GENERIC_ALL** | Full access |

Each object type defines a **generic mapping** that translates generic rights into the appropriate specific and standard rights. For example:

| Generic right | File mapping | Registry key mapping |
|---|---|---|
| GENERIC_READ | `FILE_READ_DATA \| FILE_READ_ATTRIBUTES \| FILE_READ_EA \| READ_CONTROL \| SYNCHRONIZE` | `KEY_QUERY_VALUE \| KEY_ENUMERATE_SUB_KEYS \| KEY_NOTIFY \| READ_CONTROL` |
| GENERIC_WRITE | `FILE_WRITE_DATA \| FILE_APPEND_DATA \| FILE_WRITE_ATTRIBUTES \| FILE_WRITE_EA \| READ_CONTROL \| SYNCHRONIZE` | `KEY_SET_VALUE \| KEY_CREATE_SUB_KEY \| READ_CONTROL` |

Generic rights are resolved into specific rights **before** AccessCheck evaluates. The evaluator only sees specific and standard rights — it never encounters a generic bit in the mask.

## Putting it together

When you see an ACE like:

```
Allow  Domain Users  GENERIC_READ
```

On a file, this resolves to `FILE_READ_DATA | FILE_READ_ATTRIBUTES | FILE_READ_EA | READ_CONTROL | SYNCHRONIZE`. On a registry key, it resolves to `KEY_QUERY_VALUE | KEY_ENUMERATE_SUB_KEYS | KEY_NOTIFY | READ_CONTROL`.

The same ACE, the same intent, but the actual bits depend on the object type. This is how one access control model serves every object type in the system without knowing their specifics.
