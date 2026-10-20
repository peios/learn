---
title: Freshness and Rollback Protection
description: An index that verifies is not necessarily current — monotonic versions, staleness limits, and the defences against rollback and freeze.
---

An index that verifies is not necessarily current. This section defends
against **rollback** — replaying an older signed index to hide newer
packages — and **freeze** — holding a consumer at a current-but-stale
index while its clock runs on.

Every requirement here applies to **both** the active index and the
archive index. An attacker who can replay one can replay the other, and
the archive index is the candidate source for every downgrade and pin.

## Monotonic index versions

Each publication of an index MUST set `index_version` to a value
strictly greater than any previously published value for the same
repository.

A consumer MUST record, per repository, the highest `index_version` it
has ever observed. On each fetch it MUST reject an index whose
`index_version` is less than that recorded value, **even when the index
is correctly signed by a still-trusted key**.

A consumer MUST also record the `generated_at` of the last index it
trusted, and MUST reject an index whose `generated_at` is older than the
recorded value.

## No progress is a failed fetch

A fetch returning an index whose `index_version` **and** `generated_at`
both equal the recorded values is a **failed** refresh, not a successful
one. A consumer MUST NOT advance its "last successful refresh" timestamp
on such a fetch.

> [!NOTE]
> This is the anti-freeze rule, and it is the one most often skipped.
> Without it, an attacker who can serve the same signed index
> indefinitely keeps every consumer's refresh timestamp advancing while
> the content never changes, so the maximum-trusted-age check of §5.37
> never fires and the consumer never notices it has been pinned.

## The initial floor

Adding a repository bootstraps the consumer's recorded floor. To defend
against an attacker serving a stale-but-signed index at that moment, a
repository SHOULD distribute a **minimum acceptable `index_version`**
alongside its trust anchors, through the same out-of-band channel. A
consumer SHOULD use that minimum as its initial floor, and MUST refuse
the add when the first index fetched falls below it.

A consumer MUST NOT reset a recorded floor as a side effect of any
operation other than removing the repository. In particular, re-adding
an already-configured repository MUST NOT lower the floor: the operation
either applies the recorded floor as a refresh would, or is refused.

> [!NOTE]
> Repository-add reads as idempotent, and configuration-management
> convergence loops treat it that way. If adding an already-known
> repository rewrites the floor unconditionally, a rollback that the
> refresh path correctly refuses becomes permanent and invisible the
> next time that loop runs. Removing the repository first is the
> sanctioned reset (§5.37), because it discards the trust state too.

## Maximum index staleness

A consumer MUST enforce a maximum staleness window on the index itself,
measured from its `generated_at`. An index older than **90 days** MUST
trigger a refresh attempt before any install operation proceeds.

The 90-day default MAY be tuned by operator configuration; a value
greater than 365 days SHOULD generate a warning each time it is
exercised.

> [!NOTE]
> This is a different measurement from the maximum trusted age of §5.37,
> and both are needed. Trusted age asks "how long since I successfully
> refreshed"; index staleness asks "how old is the metadata I am acting
> on". A repository that bumps `index_version` on every publication
> while stamping an ancient `generated_at` satisfies the first check
> forever and fails the second immediately.

## What these checks buy

Per-package signing and index signing both still verify under a
rollback: the attacker is replaying genuine, correctly signed content.
What changes is the *set* of packages the consumer believes is current.
The monotonic version check is what makes that set unable to move
backwards, and the no-progress rule is what stops it from being frozen
in place.
