---
title: Command Line and Startup
---

## Command-line interface

```
loregd <HiveName>=<DatabasePath> [<HiveName>=<DatabasePath> ...]
```

Each argument declares a hive name and the filesystem path to its
SQLite database file. loregd registers all declared hives with LCS
at startup.

**Examples:**

```
loregd Machine=/var/lib/registry/machine.regdb Users=/var/lib/registry/users.regdb
loregd Machine=/var/lib/registry/machine.regdb Users=/var/lib/registry/users.regdb Roles=/var/lib/registry/roles.regdb
```

loregd MUST accept one or more hive arguments. Zero arguments is
an error (exit immediately with a non-zero status).

Hive names are case-insensitive for routing purposes but loregd
preserves the case provided on the command line for registration
with LCS.

Database paths MUST be absolute. Relative paths are an error.

## No configuration

loregd has no configuration file, no environment variable
configuration, and no registry-based self-configuration. It is
the configuration store — it does not need to be configured.

All operational behaviour is determined by:
- The command-line arguments (hive names and database paths)
- The SQLite database contents
- Compiled-in defaults (WAL mode, connection pool sizes, etc.)

## Startup sequence

1. **Parse arguments.** Extract hive name → database path mappings.
   Validate: at least one hive, all paths absolute, no duplicate
   hive names.

2. **Open databases.** For each hive, open (or create) the SQLite
   database file at the declared path. Enable WAL mode. Run
   `PRAGMA journal_mode=wal` and `PRAGMA foreign_keys=ON`.

3. **Attach volatile stores.** For each hive, create a shared
   in-memory database for volatile key storage using SQLite's
   shared-cache URI:
   `ATTACH 'file:<hivename>_volatile?mode=memory&cache=shared' AS volatile`.
   This URI MUST be identical across all connections (read and
   write) for the same hive, ensuring all connections share the
   same volatile store. Each hive has its own volatile store
   (distinct URI per hive).

4. **Run schema migrations.** Ensure the database schema matches
   the current loregd version. Create tables if the database is
   new. Migrate if the schema version is older. Refuse to start
   if the schema version is newer than loregd supports (prevents
   downgrade corruption).

5. **First-boot detection.** For each hive, check whether a root
   key record exists. If not, this is a first boot for this hive:
   generate a random GUID for the root key, create the root key
   record with the appropriate default SD (see the Hive Root SDs
   section of the LCS v0.21 specification), and persist it.

6. **Crash recovery.** For each hive, clean up orphaned GUIDs:
   delete key records that have no corresponding path entries in
   any layer. Cascade to values and blanket tombstones. SQLite's
   WAL recovery handles any uncommitted transactions automatically
   when the database is opened.

7. **Compute max sequence.** For each hive, query the maximum
   sequence number across all tables (path_entries, values,
   blanket_tombstones). Report the global maximum across all
   hives in the registration handshake.

8. **Open /dev/pkm_registry.** Requires SeTcbPrivilege in the
   calling thread's token.

9. **Register hives.** Issue REG_SRC_REGISTER with all hive names,
   root GUIDs, the global max sequence number, and flags (no
   private hives — loregd registers global hives only).

10. **Enter request loop.** Begin reading RSI requests from
    /dev/pkm_registry and dispatching to the appropriate hive
    database.

## Exit behaviour

loregd exits when:
- /dev/pkm_registry is closed by the kernel (LCS shutdown)
- A fatal database error occurs (corruption, disk full)
- peinit sends a termination signal

On exit, loregd closes all database connections. SQLite finalises
any open WAL transactions. The volatile stores (in-memory
databases) are destroyed — volatile keys are gone. LCS detects
the source disconnect and marks all hives as unavailable.
