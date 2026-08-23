---
title: The Layer Model
description: A named collection of registry writes managed as a unit — precedence tiers, caps, and why layers are global while entries are per-source.
---

A layer is a named collection of registry writes that can be managed as
a unit. Layers have precedence, and the highest-precedence entry wins.
They are how role installation, Group Policy and configuration revert
all work, and they are the reason removing a role does not leave its
settings behind.

| Field | Mutable | Description |
|---|---|---|
| Name | No | The layer's identity — not a GUID, not an integer. Case-preserving, compared with Unicode Simple Case Folding. Bounded by `MaxPathComponentLength`. |
| Precedence | Yes | Higher wins. Default 0. |
| Enabled | Yes | A disabled layer is invisible during resolution unless it is attached to the resolving thread's credentials (§5.3.5). Default true. |
| Owner | — | The SID of the principal that created the layer. Informational only. |

The name being the identity is deliberate. Layer names are
code-generated and meaningful by construction —
`role-jellyfin`, `gpo-security-baseline` — so there is nothing an
opaque identifier would add.

`Owner` is never used for an access check; authorisation is the
descriptor on the layer's metadata key (§5.3.4). It is also not quite
immutable as a field: a refresh re-reads the `Owner` value and
re-selects it, so rewriting the value does change what is cached.
Because nothing consults it, that has no effect on anything.

## Precedence tiers

The base layer and role layers all sit at precedence 0. Within one
tier, the most recent write wins — the highest sequence number. Group
Policy layers sit above 0 and override both.

Establishing or raising a layer's precedence above 0 requires
`SeTcbPrivilege` (§5.3.4). That is what keeps the tier boundary
meaningful.

## Caps

`MaxTotalLayers`, default 1024, bounds the in-memory layer table.
Creating a layer when it is full returns `ENOSPC`.

The table itself is a fixed array sized at compile time for 1023
dynamic layers plus the base layer. `MaxTotalLayers` is configurable up
to 65536, and a value above 1024 validates and publishes, but the table
still runs out at 1023 dynamic entries. Values below 1024 bind
correctly.

`MaxLayersPerValue`, default 128, bounds how many layers may write to
the same `(key GUID, value name)` pair. It is a guard against
amplification — every read of that value has to resolve every entry —
not an access control boundary.

It is enforced at `REG_IOC_SET_VALUE` time, before the source is
contacted, by querying the source for the current entry count. A write
that replaces an existing entry in the *same* layer does not increase
the count and is not checked. Exceeding the cap is `ENOSPC`.

The check is deliberately **best-effort admission control**, not a
storage invariant. It queries and then dispatches without holding
anything, so concurrent writers can both observe room and both proceed.
Sources are not required to enforce it atomically. Once LCS observes a
count at or above the cap, further new-layer writes are refused.

Blanket tombstones and value deletions are not subject to it.

## Layers are global; entries are per-source

There is one authoritative layer table, held by the kernel. Each source
stores layer *entries* — path entries and value writes tagged with
layer name strings — for its own hives. Layer *metadata* is global and
lives in one place.

A source never needs the layer table. It stores what it is told, tagged
with whatever name it is given, and returns everything on request. A
source that has never seen a particular layer name simply stores
entries carrying it. Resolution — precedence, enabled state, tombstone
evaluation — happens entirely in the kernel, and the layer snapshot is
passed into each operation rather than pushed to sources. There is no
RSI operation that hands a source the layer list.
