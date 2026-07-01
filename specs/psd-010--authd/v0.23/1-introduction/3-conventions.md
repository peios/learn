---
title: Conventions
---

This specification conforms to PSD-001.

This specification uses the normative keywords MUST, MUST NOT, SHOULD,
SHOULD NOT, and MAY per RFC 2119.

Binary fields are little-endian unless stated otherwise, matching the
KACS wire formats of PSD-004. Strings on the wire are UTF-8 and are
length-prefixed, never NUL-terminated.

SIDs are written in the `S-R-I-S…` string form for readability; their
binary encoding is defined by PSD-004 §2 and is the form actually
transmitted and stored. RID constants are written in decimal.

SQL examples use SQLite syntax with SQLite type affinity (INTEGER,
TEXT, BLOB, REAL). As in PSD-006, the schema is normative but the exact
DDL is illustrative: an implementation MUST preserve the columns and
constraints described, but MAY differ in incidental syntax.

Pseudocode and message-sequence descriptions are illustrative. Where
prose and pseudocode disagree, the prose is normative.

authd and lpsd are specified to be implemented in Rust against the
`peios` crate's KACS bindings (PSD-004) and, for lpsd, SQLite via a
bundled (statically compiled) SQLite library. The language and library
choices are recorded for implementers; they are not themselves
normative requirements of the subsystem's behaviour.

Where this specification names a KACS syscall, security descriptor,
token field, or privilege, PSD-004 is authoritative for its semantics;
this document is authoritative only for how authd and lpsd use it.
