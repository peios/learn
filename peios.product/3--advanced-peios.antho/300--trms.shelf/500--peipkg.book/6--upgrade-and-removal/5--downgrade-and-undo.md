---
title: Downgrade and Undo
description: A downgrade is an upgrade to an older version with one extra precondition — plus undo, and what a version revert does not revert.
---

## Downgrade

A downgrade is an upgrade whose new version is older than the installed
one. The procedure is identical, with one additional precondition: the
operator has explicitly authorised it.

The authorisation is raised by the resolver as an elevated action, and
is not satisfied by the routine confirmation prompt.

> [!NOTE]
> Explicit authorisation is required because a downgrade is unusual: it
> implies the operator wants to revert to a known-good earlier state,
> often after a failed upgrade. Making them opt in ensures the downgrade
> is intentional rather than the result of a misconfigured constraint.

A downgrade target has to be available from a configured repository's
archive index, or from a package file already cached. Versions pruned
from an archive cannot be reached without an externally supplied package
file.

## Undo

`peipkg undo` reverts the effect of a previous transaction. It works by
re-resolving against the archive index with downgrades permitted, and
applying the resulting plan as an ordinary transaction, rather than by
restoring the previous transaction's backups.

Two consequences follow from that choice. Undo needs the archive index,
and therefore a reachable repository or a warm cache — it is not an
offline operation. And it produces a new transaction with its own
journal and its own rollback, rather than unwinding an old one, so the
guarantees are the same as any other change.

## What a version revert does not revert

Reverting a package's version does not revert anything outside that
package's payload: registry state, configuration materialised by
reconcillers, runtime data under `/var/`, and any user data are
unaffected.

Comprehensive system rollback, including state under registry control,
is a higher-level concern handled by recovery snapshots. Package-level
version revert covers the common case of an update breaking something.
