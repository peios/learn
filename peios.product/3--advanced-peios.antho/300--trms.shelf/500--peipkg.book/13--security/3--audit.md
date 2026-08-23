---
title: Audit
description: Every install, upgrade, uninstall, refresh and recovery emits an event through KMES — what one carries, and what emission depends on.
---

Every install, upgrade, uninstall, refresh, and recovery emits an audit
event.

Events go into the kernel event subsystem, KMES, through the `kmes_emit`
system call. Because emission is a local kernel call rather than a
message to a userspace daemon, it has no unreachable-destination failure
mode: there is no reachability probe, no fail-closed rule, and no
retention journal.
Whether and when events are drained and persisted is the historian's
concern, not peipkg's.

## What an event carries

| Field | Where it lives |
|---|---|
| Operation type | The event's type tag |
| The caller's identity | **The kernel-stamped header** |
| Target packages | The payload: name, version, architecture |
| Outcome, with a rejection reason | The payload |
| Transaction identifier | The payload |
| Timestamp, UTC | The payload |
| Source repository | Not carried |

Identity is not in the payload and is not peipkg's to write. The kernel
stamps the caller's effective token, its true token, and its process
identity onto every emission, where they cannot be forged or suppressed
by the emitting program. That is a stronger guarantee than a payload
field: peipkg could lie about a payload field, and cannot lie about a
header the kernel wrote.

The source repository is not recorded on an install or upgrade event,
although it is known. A plan drawing packages from several repositories
names none of them.

A committed cross-root operation emits its success event without a
transaction identifier, so it cannot be joined to the transaction ledger
or to the kernel's own record of the file operations it performed.

## Event types

| Type | Emitted for |
|---|---|
| `peipkg.install` | A successful install |
| `peipkg.upgrade` | A successful upgrade — and a downgrade, and an undo |
| `peipkg.uninstall` | A successful uninstall |
| `peipkg.refresh` | A repository refresh |
| `peipkg.transaction-failed` | A transaction that was rolled back |
| `peipkg.recovery` | A recovery-mode resolution |
| `peipkg.authorisation` | An operator authorisation record |
| `peipkg.repo-add` | A repository add |
| `peipkg.repo-remove` | A repository remove |
| `peipkg.config-change` | A trust-policy or transport-flag change |
| `peipkg.claim` | A claim grant or revoke |

Downgrade and undo are deliberately recorded as upgrades, since the set
carries no downgrade type.

`peipkg.config-change` is declared and never emitted. A repository
re-added with a weakened signature policy or an enabled transport
allowance produces an event indistinguishable from a routine add, so
trust-policy history cannot be reconstructed from the stream.

A refresh in which some repositories succeeded and others failed emits
one event with a rejection outcome, an empty repository field, and a
count in its detail.

## Successes and failures

A committed operation emits a success event; one that is rejected or
rolled back emits a separate failure event. Rejection reasons and error
text travel in the detail field.

An operator who declines at a prompt emits nothing: the transaction
never started.

An automatic recovery at the head of an ordinary operation emits
nothing. The same rollback performed deliberately through the recover
command does. `peipkg recover`'s own failure paths emit nothing either.

`peipkg-compose` emits nothing at all.

## What emission depends on

Emitting requires an audit privilege on the caller's token. peipkg warns
and continues when emission fails, so an operator with write access to
the payload destinations but without that privilege installs packages
with no peipkg audit event.

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
