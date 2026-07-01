---
title: POSIX Projection (uid/gid)
---

Every principal that can own or access a Linux-visible object projects to
a single POSIX integer id. The projection exists only for Linux
application and filesystem compatibility: **uid/gid carry no authority in
Peios** — KACS decides access by SID (PSD-004). The id is the value Linux
apps see via `getuid()`/`stat()` and the owner stored on Linux
filesystems; the compatibility layer maps an inbound id back to a SID to
apply KACS. Because ownership is stored as a SID in the security
descriptor, the id is a *cosmetic* projection — the authoritative owner is
always the SID.

## The unified id invariant

The id space is **unified**: an integer identifies **at most one
principal** and is used as a uid **xor** a gid — never both, and never for
two different principals. A single `rid_counter` (§3.1) makes every
`base + rid` id unique across users and groups, and the well-known and
allocated assignments are likewise disjoint. An implementation MUST NOT
maintain separate uid and gid counters. The benefit is **context-free
reverse mapping**: an integer resolves to one SID regardless of the slot
it appeared in. (This matches a Samba `autorid` member's unified-xid
model.) Peios therefore does **not** use Linux user-private-groups: a
user's primary gid is its real primary group's id, not a copy of its uid.

## Three allocators, one address space

The bands of §9 are a **shared allocation contract**. Three allocators
assign ids within it, each authoritative for, and storing, its own part;
they never collide because each draws only from its assigned bands:

- **lpsd** — local accounts and groups. lpsd assigns the id in the local
  band at creation and stores it on the principal record
  (`posix_uid`/`posix_gid`, §3.5). lpsd is the source of truth for local
  principals and returns their ids in the resolved principal (§4).
- **adpsd / AD** (deferred — §8) — domain principals. The directory is
  authoritative (an explicit `uidNumber`-style attribute, or an
  `autorid`-style per-domain computation); adpsd returns the id.
- **authd** — the **ephemeral / sourceless** SIDs that are not directory
  accounts: service SIDs (`S-1-5-80-…`), virtual identities, and
  orphan/foreign SIDs. authd allocates these next-free in their bands and
  persists them in its **idmap** store (§2.1). SIDs on the no-id list (§9)
  are not object-owning principals and are never allocated an id — they are
  omitted from the projection entirely. authd also caches the
  mappings the directories report, so its idmap is the single point the
  compatibility layer queries to reverse-resolve any id.
- **well-known** SIDs are **computed** by arithmetic (§9), need no
  storage, and are seeded into the idmap on demand.

Assignment happens at a SID's **first projection** (commonly token-mint,
also file-ownership assignment), performed by the owning allocator, and is
frozen thereafter. Forward (`SID → id`) and reverse (`id → SID`) are both
served from authd's idmap; on a miss in a **computable** band the id is
derived arithmetically and backfilled.

authd's idmap is **low-criticality**: the cached directory mappings
rebuild from the directories, and a lost ephemeral assignment only causes
a service's files to show a *different cosmetic uid* (the SID-native owner
is unchanged). It holds no accounts and no secrets (§2.1).

Reverse-resolution is **not** cosmetic on the setuid-bit transition path
(PSD-004 — a setuid binary's `id → SID` lookup decides which principal it
becomes): for any id that can be a setuid target, the mapping MUST be
authoritative and stable. The `0xFFFFFFFF` wire sentinel (§6.4) means "the
source assigns no id"; authd MUST resolve it to a real allocated id before
minting — `0xFFFFFFFF` MUST NOT appear in a token spec or be treated as a
literal uid/gid (it equals `(uid_t)-1`, the "no-change" sentinel).

## Bands and reverse mapping

The full band layout is §9. Reverse-resolution is a range check:

| Range | Resolves to | Allocator |
|---|---|---|
| `0`; `1–999`; `1000–1999`; `65200–65299`; `65530`; `65534` | well-known / fixed sentinels (computed — §9) | computed |
| `1,000,000 – 4,999,999` | fallback / service / package / capability (idmap lookup) | authd |
| `5,000,000 – 9,999,999` | local: `rid = id − 5,000,000` | lpsd |
| `≥ 10,000,000` | domain: `dn = id ÷ 5,000,000 − 1`, `rid = id mod 5,000,000`, then `dn → domain SID` | adpsd |

All ids MUST be below 2³¹ (2,147,483,648). Within a namespace, `rid` MUST
be < 5,000,000 (the slice width). `65534` is the overflow/unmapped
sentinel (`S-1-0-0`); `65535` is reserved. Any id with no assignment — a
reserved hole (e.g. `18`) or an unallocated gap — also reverse-maps to
`S-1-0-0`. A namespace whose slice would reach 2³¹ MUST be refused at join
(domain support is deferred — §8).

A principal's stored projection is a single id. **Supplementary gids are
not stored** — they are the projection of the principal's expanded group
set (§3.2, §5.2) to gids at token-mint time.

> [!INFORMATIVE]
> §9 enumerates the complete well-known band assignments (the named
> `S-1-5-N`, the `S-1-5-32` aliases, the `S-1-2`/`S-1-1`/`S-1-0` SIDs, and
> the service/virtual-host family roots) and the SID families that receive
> **no id** — integrity labels (`S-1-16-*`), Creator placeholders
> (`S-1-3-*`), logon-session SIDs (`S-1-5-5-X-Y`), authorization-context
> markers (`S-1-5-64-*`, `S-1-18-*`, `S-1-5-1000`), and bare
> authority/domain prefixes — none of which are object-owning principals.
