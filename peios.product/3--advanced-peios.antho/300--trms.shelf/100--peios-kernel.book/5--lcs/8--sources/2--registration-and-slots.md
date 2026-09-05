---
title: Registration and Slots
description: Reaching LCS through /dev/pkm_registry — what registration validates, how source slots work, and resuming one that went Down.
---

A source reaches LCS through `/dev/pkm_registry`. The device's `open()`
handler checks the calling thread's effective token for an **enabled**
`SeTcbPrivilege` and returns `EPERM` without it, so an unprivileged
process cannot obtain an fd to the device at all. [*source.register.open-requires-enabled-setcbprivilege]

Having opened it, the source issues `REG_SRC_REGISTER`, naming the
hives it backs, the root GUID of each, the highest sequence number it
has persisted, and per-hive flags and scope GUID. On success it enters
the request loop: `read()` for requests, `write()` for responses.

## What registration validates

- Every hive name is valid and is not the reserved `CurrentUser`
  (§5.2.1). [*source.register.hive-name-valid-and-not-currentuser]
- No route identity — the folded name paired with its scope — collides
  with one held by another **Active** source. [*source.register.no-route-identity-collision]
- Private hive collisions are scoped: the same name in different scopes
  is fine (§5.2.2). [*source.register.private-hive-collisions-are-scoped]
- A hive's root GUID is not nil. [*source.register.root-guid-not-nil]
- The root GUIDs within one request are distinct from each other. [*source.register.root-guids-distinct-within-request]
- A hive without `RSI_HIVE_PRIVATE` carries no scope GUID. [*source.register.scope-guid-only-for-private-hive]
- No unknown flag bits are set. [*source.register.no-unknown-flag-bits]
- The hive count is non-zero and within `MaxHivesPerSource` (64), and
  the source count is within `MaxRegisteredSources` (32). Either is
  `ENOSPC`. [*source.register.hive-and-source-counts-are-enospc]
- The reported maximum sequence can be advanced past without
  overflowing 64 bits, or registration fails `EOVERFLOW` and the source
  is never made Active (§5.3.7). [*source.register.max-sequence-overflow-is-eoverflow]

Root GUIDs are checked for uniqueness within one request, and the
already-registered state is checked for consistency, but an incoming
request's root GUIDs are not compared against those of existing slots. [*source.register.root-guids-not-compared-across-slots]

## Source slots

Successful registration creates a **source slot**: the kernel object
owning one connection and the hive set registered on it. [*source.register.success-creates-a-slot]

Each registered hive has a stable identity — its folded name, its
visibility, its scope GUID for a private hive, and its root GUID. [*source.register.hive-identity-fields]

**Down slots keep their identities reserved.** A crash or an fd close
marks the slot Down; it does not unregister anything and does not
retire any hive identity. [*source.register.down-slot-keeps-its-identities]

Slots are never freed, and collision checks see Down slots as well as
Active ones. [*source.register.collision-checks-see-down-slots]

Status is a property of the slot, not of an individual hive. A source's
hives go Down together. [*source.register.status-is-per-slot]

## Resuming a Down slot

A new process may take over a Down slot if it holds `SeTcbPrivilege`
and registers **exactly the same hive set**: the same folded name,
visibility, scope GUID and root GUID for every hive, and the same
number of them. Partial resume is rejected. [*source.register.resume-requires-exact-hive-set]

The distinction between the failures matters. A request whose only
mismatch is stale identity data — a different root GUID for an
otherwise-matching hive — fails `ESTALE`. [*source.register.stale-root-guid-is-estale]

Other partial or malformed resume attempts fail `EINVAL`. [*source.register.other-resume-mismatch-is-einval]

`EEXIST` is reserved for a collision with an **Active** slot; it never
comes from a Down-slot collision. [*source.register.eexist-only-from-active-collision]

When both an Active collision and a stale Down slot apply, `EEXIST`
wins. [*source.register.eexist-wins-over-estale]

New hives cannot be added by mutating a Down slot during a resume — the
hive set has to match exactly, so a superset simply fails, and a new
hive needs a new slot. There is no implicit retirement of a Down slot;
retiring one would need an explicit administrative operation, and none
exists. [*source.register.no-implicit-down-slot-retirement]

A replacement source is authenticated by `SeTcbPrivilege`, not by
process identity. Nothing records a pid, and nothing could usefully:
process identity does not survive a crash and restart. [*source.register.resume-authenticated-by-privilege-not-pid]

## Coming back

On a successful resume the slot becomes Active, its restart generation
advances, and LCS replays any layer deletions that were pending. [*source.register.resume-activates-slot-and-replays]

LCS then delivers `OVERFLOW` to every armed watch on that source
(§5.6.3).

Existing key fds resume working without being reopened. Each carries
the restart generation it last saw; when it notices a change it
re-reads its key and continues. [*source.register.key-fds-survive-a-resume]

If the key's GUID no longer exists in the restarted source — the
database was restored from an older backup, say — that first operation
returns `ENOENT` and the fd is marked orphaned. [*source.register.missing-guid-after-resume-orphans-fd]
