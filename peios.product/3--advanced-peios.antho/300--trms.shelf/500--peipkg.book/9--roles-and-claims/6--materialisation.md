---
title: Materialisation
description: Recomputing a role's links from current state and applying the difference — when it runs, held but unmaterialised, collisions and repointing.
---

Materialisation is reconciliation: peipkg recomputes what the role's
links should be from current state, and applies the difference.

## When it runs

Every transaction recomputes the desired link set over **all**
post-transaction manifests and **all** holders — not only for roles
whose holder it changed.

That is what makes retroactive materialisation work. Installing a
package that merely declares a consumer-side path for a role another
package already holds creates the link against the existing holder, and
does not re-open the question of who holds it. Removing such a package
removes the links only it declared, leaving paths other packages still
declare in place.

Reconciliation is idempotent: reconciling against unchanged state
produces no filesystem change.

## Held but unmaterialised

Holder state lives in its own table, keyed by role, and is never
inferred from whether a link exists.

A role whose computed claim-path set is empty materialises no links and
remains held. Installing a package that declares a path for it later
materialises the link retroactively, against the holder already on
record.

> [!NOTE]
> A sole provider installed before any consumer is held but
> unmaterialised: it holds the role, but until some package declares a
> dependency-side path — or the provider itself declares a default —
> there is no path to point anywhere. Tracking holder state
> independently of link existence is what lets the later install create
> the link without re-deciding the holder.

## Collisions

Before materialising a link, peipkg checks that no installed package
owns the claim path.

The check reads the ownership table as it stands *before* the
transaction's own rows are written, which happens at commit. So a
transaction that installs both a package owning a path and a provider
claiming that same path sees no owner, queues both a payload operation
and a claim operation for one destination, and commits both — leaving
the database holding an ownership row and a claim-link row for one path.

A package that owns a **directory** at the claim path is waved through
rather than treated as a collision, and the directory is renamed aside
and replaced with the link.

The reverse direction is unguarded: nothing stops a package payload
installing over an existing claim link. The link is renamed aside, the
payload file takes the path, and the claim-link row survives — after
which reconciliation compares its record against its own desired set,
finds them equal, and never notices the link is gone.

## Repointing

A holder swap repoints every one of the role's links, within a single
transaction.

Each repoint is performed as two renames: the old link is renamed aside
as a backup, then the new link is renamed into place. The path is absent
between the two.

> [!NOTE]
> Atomic repoint matters because a claim path is typically on the
> critical path of a running system — a contended daemon binary may be
> executed at any moment. A single rename that replaces the old link
> outright closes the window; two renames leave it open for a full
> rename round-trip, on every link of the role.
