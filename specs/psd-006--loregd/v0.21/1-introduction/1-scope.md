---
title: Scope
---

This specification defines loregd (Local Registry Daemon), the
primary registry source for the Peios operating system. loregd
implements the Registry Source Interface (RSI) defined in PSD-005,
providing persistent storage for one or more
registry hives using SQLite.

loregd is the first and reference source implementation. Any process
implementing the RSI contract can serve as a registry source;
loregd is not architecturally special. It is operationally special:
it is the source that provides the Machine\ and Users\ hives at
boot, making it the critical path to a running system.

This specification covers:

- The command-line interface and startup sequence
- The SQLite database schema (one database per hive)
- Volatile key storage via attached in-memory databases
- Connection pool model and concurrency
- Transaction handling and write serialisation
- Crash recovery (orphaned GUID cleanup)
- First-boot initialisation (hive root creation)
- The RSI request processing loop
- Case-insensitive storage via stored folded forms
- Shutdown and hive unload behaviour

This specification does not cover:

- LCS (the kernel subsystem) -- PSD-005
- The RSI binary protocol (wire format, message framing, op codes)
  -- PSD-005 §7 and §11.3
- Registry key schemas (those belong to the subsystems that own
  them)
- Other source implementations
- peinit's service management of loregd (PSD-007)
