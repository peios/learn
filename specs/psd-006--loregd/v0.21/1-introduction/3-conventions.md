---
title: Conventions
---

This specification conforms to PSD-001.

This specification uses the same normative keywords (MUST, SHOULD,
MAY) as PSD-005, per RFC 2119.

SQL examples use SQLite syntax. Column types use SQLite's type
affinity system (INTEGER, TEXT, BLOB, REAL). All SQL is illustrative
-- the schema is normative, the exact DDL is guidance.

loregd's persistent storage is specified against SQLite. The
specification names SQLite features (WAL mode, SAVEPOINT, PRAGMA)
directly. Volatile keys are not stored in SQLite: they live in an
in-process volatile store (§3.1.6). An implementation using a
different storage engine would need to provide equivalent semantics
but is not the target of this spec.
