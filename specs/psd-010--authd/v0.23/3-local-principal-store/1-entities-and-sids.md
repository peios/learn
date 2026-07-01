---
title: Entities and the SID Namespace
---

lpsd is a flat, RID-keyed store. It holds three kinds of entity: the
domain object, users, and groups. It is not a directory: it has no
hierarchy of containers, no distinguished names, and no replication
metadata.

## The domain object

lpsd holds exactly one **domain object**, the root of the local
namespace. It records:

- **`machine_sid`** — the `S-1-5-21-X-Y-Z` identifier that is the prefix
  of every local principal's SID. Generated once per installed instance
  (§7.1); its three sub-authorities are drawn from a **seeded** CSPRNG —
  generation MUST block on available entropy (e.g. `getrandom` without
  `GRND_NONBLOCK`) — each non-zero (§9). The same seeded-CSPRNG requirement
  applies to `object_guid`s and argon2id salts.
- **`rid_counter`** — the next RID to allocate for a new principal; RIDs
  are allocated monotonically and are never reused (§9).
- **the password and lockout policy** — minimum length, complexity,
  history depth, maximum age, lockout threshold, and lockout duration
  (§3.4).
- creation metadata.

The domain object is the analogue of the SAM/AD "domain" object. There
is exactly one; lpsd MUST refuse to operate without it (§7.1, §7.3).

## Users and groups

**Users** are the account records (§3.2). **Groups** are local security
groups (aliases) with a membership list (§3.2). Both are security
principals identified by a SID.

Computer/machine accounts and managed service accounts are domain-join
and later concerns and are out of scope for this version (§8).

## The SID namespace

A standalone machine's namespace root is its **machine SID**
(`S-1-5-21-X-Y-Z`). This is structurally identical to a domain SID: a
local principal's SID is `machine_sid` + a relative identifier (RID).

lpsd MUST allocate RIDs for new principals from `rid_counter`, starting
at **1000**. RIDs below 1000 are reserved for well-known and built-in
principals and MUST follow the established conventions:

| RID | Principal |
|---|---|
| 500 | built-in Administrator (created disabled — §7.1) |
| 501 | built-in Guest (created disabled) |

The `S-1-5-32` BUILTIN aliases (Administrators 544, Users 545, and the
rest defined by PSD-004) are represented in lpsd as group entities so
that membership can be recorded against them, but their SIDs are the
fixed well-known values, not `machine_sid`-relative.

> [!INFORMATIVE]
> Adopting the SID-and-RID conventions means the namespace is already
> domain-shaped: joining a domain later simply adds a *second*
> namespace (the domain SID) alongside the machine SID, and local
> principals keep their machine-SID identity unchanged.

## SID generalisation

A shipped system image MUST NOT contain a machine SID or any
`machine_sid`-relative principal. The machine SID is generated on first
boot, per installed instance (§7.1). This avoids SID collisions across
clones of the same image, which would break local-principal identity
and (later) domain trust.
