---
title: A Broken Claim
description: A claim path missing, dangling or pointing at the wrong thing — what each state means, and how to repair it.
---

A claim path is missing, dangling, or pointing at the wrong thing.

## Missing

The role may simply be unheld — its holder was uninstalled and nothing
was promoted (§9.7). `peipkg claim <role>` reports the holder and the
remaining eligible providers, and granting to one of them restores the
link.

The role may be held with no consumer declaring a path, in which case
there is nothing to materialise and nothing is wrong.

Or a package payload may have been installed over the link. peipkg does
not prevent that: the link is renamed aside, the payload file takes the
path, and the claim-link record survives. Reconciliation then compares
its record against its own desired set, finds them equal, and never
notices. The link does not come back on its own.

## Dangling

The holder's target does not exist. Either the target names a path the
holding package does not ship — which peipkg does not check at install
time (§9.2) — or something removed it.

## Pointing at the wrong thing

A claim path cannot land outside the managed tree: the manifest decoder
confines it to the permitted install destinations, `/run/` and `/init`
(§9.2). Inside that tree it can still displace a file no package owned.
The claim link is placed with the same replace-then-commit sequence as
a repoint, and the displaced file went to a backup that the commit
discarded; the unowned-file rule that would have refused a payload
entry there (§5.7) is not applied to a claim link.

## Repairing

Granting a role to a provider repoints every one of its links from
current state, so a grant — even a grant to the current holder's
alternative and back — is the blunt instrument that rebuilds a role's
links.

Where the database's record disagrees with the filesystem,
reconciliation will not detect it, because it diffs the recorded set
against the desired set rather than against disk. Reinstalling the
holder is what refreshes both.
