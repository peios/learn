---
title: The Channel
description: Attaching to /dev/pkm_trust, the privilege and the TrustStore
  warrant the open handler demands, the single connection, and what
  survives a store keeper that exits.
---

## The device

A store keeper attaches by opening the character device
`/dev/pkm_trust`.

The `open()` handler requires both of the following, and fails `EPERM`
otherwise:

- The calling thread's effective token holds `SeTcbPrivilege`, and the
  privilege is enabled, not merely present.
- The calling process's executable verified as Rooted (PGSS §7.14), and
  its leaf holds the `TrustStore` warrant.

The device has one connection. While a store keeper has it open,
another `open()` fails `EBUSY`.

## The TrustStore warrant

`TrustStore` is a warrant in the sense of PGSS §7.5.

| Name | Type | Allow Equal | `flags` | Meaning |
|---|---|---|---|---|
| `TrustStore` | Set, empty | Set | `0x80` | The holder can change the kernel's trust store |

> [!NOTE]
> Privilege alone would let any program an administrator can run with
> that privilege enable a trust anchor. The warrant ties the power to
> a program that a root vouches for, so that changing what the system
> trusts takes more than being the administrator.

## Lifetime

Closing the descriptor, or the store keeper exiting, ends the
connection and nothing else. The kernel keeps the store exactly as it
is, and continues to apply it. A store keeper that attaches afterward
finds the store as the last one left it.

The kernel authenticates each store keeper by the two conditions of
this article, and keeps no record of which process held the connection
before.
