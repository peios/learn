---
title: Prior Art
---

## SQLite

loregd uses SQLite as its storage engine. SQLite provides the
transactional semantics, WAL-mode concurrency, and crash recovery
that loregd relies on. loregd is specified against SQLite directly
— the schema, concurrency model, and operational behaviour all name
SQLite features (WAL mode, ATTACH, SAVEPOINT, shared-cache URIs,
PRAGMA).

An alternative storage engine would need to provide equivalent
semantics but is not the target of this specification.

## Windows registry hive format

The Windows registry stores hives as binary files (REGF format)
managed directly by the kernel's Configuration Manager. loregd
diverges from this model entirely: storage is in SQLite databases
managed by a userspace daemon, not kernel-managed binary files.
The data model (keys, values, SDs) is shared via the LCS
specification (PSD-005), but the storage format has no relationship
to REGF.

## LCS RSI contract

loregd implements the Registry Source Interface defined in PSD-005
§7. The RSI defines the operations, message format, error model,
and source obligations. loregd's request handling (§5.1) is a
direct mapping of RSI operations to SQLite queries. The RSI
contract is normative for loregd's wire behaviour — where this
specification and PSD-005 §7 disagree, PSD-005 §7 is correct.
