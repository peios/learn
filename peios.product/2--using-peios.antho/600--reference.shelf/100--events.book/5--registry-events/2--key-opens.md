---
title: LCS_KEY_OPEN_AUDIT
description: The event fired when a key open matches a SACL audit ACE, the SACL that produces nothing, and what happens when emission fails.
---

Fires when a key open matched a SACL audit ACE.

| Key | Meaning |
|---|---|
| `caller` | Caller summary (§2.3). |
| key GUID | The key that was opened. |
| `requested_access` | The mask after registry generic mapping, with `MAXIMUM_ALLOWED` re-added if the caller asked for it. |
| `granted_access` | The mask granted. Forced to zero on a denial. |
| decision | `allowed` or `denied`. |
| `sacl_match_flags` | Bit 0 for a success-audit match, bit 1 for a failure-audit match. No other bits. |

`granted_access` being zero on a denial is **enforced**, not merely
intended: a denied event carrying a non-zero granted mask is rejected as
a malformed payload.

SACL evaluation follows the KACS AccessCheck algorithm — the SACL is
evaluated alongside the DACL, not separately. Reading or modifying a
SACL requires `ACCESS_SYSTEM_SECURITY`, itself gated by
`SeSecurityPrivilege`.

## One matching SACL that produces nothing

A request of `MAXIMUM_ALLOWED` **alone** maps to a desired mask of zero.
AccessCheck's SACL walk tests each audit ACE's mask against the mapped
desired access, and no ACE matches zero.

So an open with a matching audit ACE emits no event, and LCS emits
nothing. This is a real hole in coverage for anyone auditing key opens:
the one request shape that asks for everything is the one that records
nothing.

## When emission fails

The policy is specific to this event, and differs from the bulk ones.

If LCS cannot **construct** a valid payload — corrupt internal state,
allocation failure, anything on the LCS side — the open fails with
`EIO` and no key fd is published. The audit is a precondition of the
access.

If the payload is valid but KMES cannot **retain** it — unavailable,
ring drops, capacity pressure, no consumer — the access decision and the
fd publication are unaffected. Loss accounting is KMES's problem, and
shows up as a `synthetic.gap` (§8.1) rather than as a failed open.
