---
title: Refresh
description: Bringing a repository's trust state and cached index up to date — the sequence, the freshness gate, maximum trusted age, and what is not checked.
---

A refresh brings a repository's recorded trust state and cached index up
to date.

## The sequence

peipkg fetches the current descriptor and its signature and verifies the
signature against any key that was `active` or `transitioning` in the
*previously trusted* descriptor — not against the new descriptor's own
keys, which would make the update self-certifying. On success it records
the new descriptor, replacing the previous key set, then fetches the
active index and verifies it against the new keys.

A failed refresh leaves the previous trust state entirely intact and is
reported. peipkg does not fall back to unverified state, and does not
silently proceed on a stale cache.

## The freshness gate

An index that verifies is not necessarily current, so a refresh applies
the rollback and freeze checks of PSPU §5.34 before accepting it.

- An index whose version is below the recorded floor is rejected, even
  though it is correctly signed by a still-trusted key.
- An index whose generation timestamp precedes the recorded one is
  rejected.
- An index whose version **and** timestamp both equal the recorded
  values is treated as **no progress**: the fetch succeeded, but the
  last-successful-refresh timestamp is deliberately not advanced.

That third case is the anti-freeze rule, and it is the one that makes
the maximum-trusted-age check below meaningful. An attacker serving the
same signed index indefinitely does not get to keep a consumer's clock
ticking forward.

The checks apply to the active index. The archive index is verified for
signature and identity but is not subjected to the freshness floor.

## Maximum trusted age

peipkg records the time of the last successful refresh per repository.
When that exceeds the repository's maximum trusted age, an install,
upgrade, or downgrade against that repository first attempts a refresh.
If the attempt fails — or succeeds without progress — the operation is
refused unless the operator supplies `--allow-stale`, which is an
elevated authorisation of its own and is audited (§13.4).

Uninstall and undo are deliberately not gated. Removing something, and
reverting a change, are exactly the operations an operator needs while
offline or while a repository is compromised.

A configured age above 180 days produces a warning on every operation,
so that a configuration effectively disabling the check stays visible.

## What is not checked

peipkg gates on how long since it last refreshed. It does not
additionally gate on how old the index itself says it is. A repository
that increments its index version on every publication while stamping an
ancient generation timestamp satisfies the refresh check indefinitely.
