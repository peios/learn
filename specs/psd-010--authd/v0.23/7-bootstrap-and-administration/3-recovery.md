---
title: Recovery
---

Recovery is the inverse of seeding (§7.1): a path back to a usable
administrator when the only one is lost, and a way to repair or restore
a damaged store.

## Lost administrator

If no usable administrator remains, the system MUST be able to re-enter
a SYSTEM-authority setup path (the bootstrap authority of §7.1) under
which a new administrator can be created via lpsd's administration
interface. This MUST require local, SYSTEM-level access, consistent with
the bootstrap trust model — it is not a remote or unprivileged
operation.

## Database repair and restore

lpsd MUST provide offline inspection and restore tooling backed by the
SQLite facilities of §3.5:

- an **inspector** mode (`lpsd --inspector` or equivalent) that opens
  the database read-only for examination and `PRAGMA integrity_check`;
- a **restore-from-backup** mode that replaces the live database from a
  known-good backup produced by SQLite's online backup.

A missing or uninitialised database on a normal boot is a hard error
that routes here, never a silent re-initialisation (§7.1).

## What recovery does not do

Recovery MUST NOT regenerate the machine SID for an existing instance
(§3.1, §7.1): doing so would orphan every principal whose SID is
`machine_sid`-relative. Machine-SID generation happens once, in
first-boot setup mode.
