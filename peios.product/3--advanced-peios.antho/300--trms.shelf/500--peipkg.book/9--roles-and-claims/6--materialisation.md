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
owns the claim path — judged against the state the transaction will
**produce**, not the state it started from.

The distinction is load-bearing in both directions. An in-flight
package's ownership rows are not written until commit, so reading the
table directly would let a transaction that installs both a package
owning a path and a provider claiming it see no owner, queue a payload
operation and a claim operation for one destination, and commit both.
And it would refuse the legal case: uninstalling the owner in the same
transaction that materialises the claim.

That freed-path case works. The removal's own file operation is dropped
and the claim's takes over the displacement, because two operations on
one path would journal two rows for one destination and contend for one
backup name.

A package owning a **directory** at the claim path is a hard collision.
A link cannot occupy a directory path, and treating it as permissible
meant renaming the package's directory aside to make room — relocating
it and its contents, after which the non-empty backup could not be
removed at commit and was left behind.

The reverse direction is guarded too. A package payload whose
destination is a live claim path is refused, naming the role. Allowing
it would have been unrepairable: reconciliation compares its record of
the link set against its own desired set, finds them equal, and never
looks at disk, so a link displaced by a payload was gone permanently
with the database still asserting it. The link belongs to the manager,
placed because a role names it; a package that wants the path is in
conflict with the role rather than entitled to take it.

## Repointing

A holder swap repoints every one of the role's links, within a single
transaction, and **each repoint is atomic**. The new link replaces the
old in one step, and the displaced link is then moved to the backup path
a rollback restores from.

> [!NOTE]
> Atomic repoint matters because a claim path is typically on the
> critical path of a running system — a contended daemon binary may be
> executed at any moment. Two renames leave the path absent for a full
> rename round-trip, on every link of the role, which is long enough for
> a supervisor to get ENOENT from an exec.
>
> The payload path deliberately keeps backup-by-rename instead. There
> the displacement has to happen *before* the new content lands, because
> the displaced original is what a rollback restores.
