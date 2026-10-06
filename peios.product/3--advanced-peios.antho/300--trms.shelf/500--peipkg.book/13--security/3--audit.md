---
title: Audit
description: Every package operation, repository change, claim change, recovery and elevated authorisation writes an event through KMES — what a record carries, and what emission depends on.
---

Every package peipkg installs, upgrades or uninstalls writes an audit
record, and so does every repository add, removal and refresh, every claim
grant or revoke, every run of `peipkg recover`, and every elevated action
put to the operator. Appendix A2 lists the types and their fields; the
records are defined in peipkg's evman fragment, installed as
`/usr/share/evman/peipkg.evman`.

Events go into the kernel event subsystem, KMES, through the `kmes_emit`
system call. Because emission is a local kernel call rather than a
message to a userspace daemon, it has no unreachable-destination failure
mode: there is no reachability probe, no fail-closed rule, and no
retention journal.
Whether and when events are drained and persisted is the historian's
concern, not peipkg's.

## What a record carries

| Field | Where it lives |
|---|---|
| Operation | The event's type |
| Time | **The kernel-stamped header** |
| The caller's token, true token and process | **The kernel-stamped header**, as GUIDs |
| The acting principal | The payload: `subject.token.sid` |
| The package | The payload: name, version, previous version, architecture |
| Source repository | The payload: `source.repository.name` |
| Transaction identifier | The payload: `transaction.id` |
| Outcome, with an error code and the error text | The payload |

A record's fields follow the platform's event conventions: a field path is
a chain of nested maps, and a value that does not apply is left out rather
than written as an empty string or zero. A removal carries no architecture
or source repository, a package installed from a local file carries no
repository, and a request refused before any transaction opened carries no
transaction identifier.

**The acting principal** is the user SID of the token peipkg runs under,
read from that token. It is peipkg's own word, written so that "who
installed this" can be answered from the record alone. The kernel also
stamps the caller's effective token, its true token and its process
identity onto every emission, as GUIDs, where they cannot be forged or
suppressed by the emitting program. If peipkg cannot read its own token,
the record is still written without the SID, and peipkg warns.

**One record per package.** A transaction writes one record for each
package it touched, typed by what happened to that package rather than by
the command: an upgrade that pulls in a new dependency writes
`peipkg.package.installed` for the dependency, and undoing an install
writes `peipkg.package.uninstalled`. A downgrade and an undo that moves a
package backward are recorded as `peipkg.package.upgraded`; the record's
two versions show the direction.

**The source repository** is per package, because one plan can draw from
several repositories. It is how a bad install is traced back to the
repository that served it.

**The transaction identifier** joins a record to the transaction ledger.
In a cross-root transaction each package's record carries the transaction
of the root the package went into, so every record joins to its own root's
ledger.

## Successes and failures

A committed transaction writes one successful record per package. One that
fails writes one failed record per package its plan held, with
`outcome.reason` set to the same stable error code the driven mode reports
(`stale`, `busy`, `denied`, `unowned`, `alternate-upgrade`, `unresolvable`,
`untrusted` or `failed`) and the error text in `outcome.detail`. A failure
that carries a transaction identifier was rolled back; one without was
refused before it began. A request refused before a plan existed writes one
failed record for each package it named, and an upgrade of everything,
which names none, writes one record without a package name.

A failed repository add or removal, and a failed `peipkg recover`, are
recorded as failed. An operator who declines an elevated action is
recorded too, as `peipkg.action.authorised` with a false outcome.

An operator who declines the routine proceed prompt writes nothing: the
transaction never started.

An automatic recovery at the head of an ordinary operation writes nothing.
The same rollback performed deliberately through the recover command does,
and so does every run of it, one with nothing to recover included.

`peipkg-compose` writes nothing at all.

## Tiers and the emission policy

The package records, the repository add, removal and reconfiguration
records, and the authorisation record are essential: they are always
written. `peipkg.claim.changed`, `peipkg.repository.refreshed` and
`peipkg.transaction.recovered` are standard, so the system's emission
policy can switch them off; peipkg consults it before building their
payload.

## What emission depends on

Emitting requires an audit privilege on the caller's token. peipkg warns
and continues when emission fails, so an operator with write access to
the payload destinations but without that privilege installs packages
with no peipkg audit record, essential types included.

On a kernel without the emit call at all, emission is silently treated
as a successful no-op, so "audit is working" and "audit is absent" look
the same.

> [!NOTE]
> peipkg's own events are a semantically meaningful summary of an
> operation. They are not the security boundary. The authoritative
> record of what changed on disk is the kernel's own audit of the
> underlying file operations, which the calling operator cannot
> suppress. A forged or omitted peipkg event cannot conceal a file
> operation from the kernel's record — which is why the gaps above are
> gaps in *diagnosis*, not in accountability.
