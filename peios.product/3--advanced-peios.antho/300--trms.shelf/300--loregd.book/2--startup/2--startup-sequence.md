---
title: Startup Sequence
description: Startup runs to completion before a single request is accepted, and any failure in it is fatal.
---

Startup runs to completion before loregd accepts a single request. Any
failure in it is fatal: loregd logs the error and exits non-zero rather
than serving a hive it could not fully prepare.

## 1. Parse and validate arguments

Extract the hive name to database path mapping and apply the validation
in §2.1.

## 2. Open each hive database

For each declared hive, create the database file's parent directory if it
is absent (mode `0755`), then open — or create — the SQLite database at
that path. loregd owns its storage location, so a first boot onto an
empty `/var/state` is expected to work without anything having prepared
the directory.

Four pieces of connection state are established immediately:

- `PRAGMA journal_mode=wal`. The result is read back and checked; if the
  database does not report `wal`, the open fails. WAL mode is what allows
  concurrent readers alongside a writer (§4.1), so silently running
  without it is not acceptable.
- `PRAGMA foreign_keys=ON`. Neither schema declares a foreign key, so
  this constrains nothing.
- `PRAGMA busy_timeout=25000` — 25 seconds (§4.3).
- The volatile database is attached (§3.3).

Each `database/sql` handle is limited to a single underlying connection.

## 3. Attach the volatile store

Each hive gets an in-memory SQLite database, attached to its connections
under the schema name `volatile` (§3.3). The attach happens as part of
opening the connection in step 2; the volatile *tables* are created in
step 4.

## 4. Establish the schema

If the database has no `schema_version` table, it is new: loregd creates
the persistent tables, creates the volatile tables, and stamps the schema
version, in one transaction.

If the version is present, it is compared against the version loregd
supports. A newer version aborts startup, and so does an older one
(§3.1).

## 5. First-boot root key

For each hive, look for a key with no parent. If none exists, this is the
hive's first boot: loregd generates a random 16-byte GUID for the root
key, builds the default hive-root security descriptor, and inserts the
root key record.

The default root descriptor grants SYSTEM and Administrators full access
to the key, grants Authenticated Users read access, marks all three as
container-inheritable, and sets both owner and group to SYSTEM.

## 6. Crash recovery

SQLite's own WAL recovery handles any transaction that was uncommitted
when the process died; it happens when the database is opened and needs
nothing from loregd.

What loregd does on top of that is clean up **orphaned keys** — key
records that no path entry in any layer points at. These can survive a
crash between a key's creation and the creation of the path entry naming
it. In one transaction, loregd deletes the values belonging to orphaned
keys, then their blanket tombstones, then the key records themselves.

The hive root is exempt: it legitimately has no parent and no path entry
pointing at it, so orphan detection skips keys whose `parent_guid` is
null.

## 7. Compute the maximum sequence number

For each hive, take the maximum `sequence` across the path entries,
values, and blanket tombstones — in both the persistent and the volatile
tables — then take the maximum across all hives. That single global
figure is what loregd reports at registration, so the kernel can resume
allocating sequence numbers above everything already stored.

In practice the volatile tables are empty at this point in startup and
contribute nothing.

## 8. Open the registry device

Open `/dev/pkm_registry`. The kernel requires `SeTcbPrivilege` in the
calling thread's token to permit this; loregd performs no check of its
own and relies on the kernel to refuse.

## 9. Register the hives

Issue `REG_SRC_REGISTER` with every hive name, its root key GUID, and the
global maximum sequence number from step 7. The registration flags are
zero: loregd registers global hives only and never private ones.

## 10. Signal readiness and serve

Send readiness to `NOTIFY_SOCKET` if it is set (§2.1), install the
termination signal handler (§2.3), and enter the request loop (§4.2).
