---
title: Prior Art
description: Where the SD family comes from in MS-DTYP — the self-relative descriptor, the ACL and ACE formats, claim entries, and conditional bytecode.
---

## MS-DTYP

The security descriptor family defined in this chapter derives from
the Microsoft Data Types specification (MS-DTYP): the self-relative
security descriptor (§2.4.6), the ACL and ACE binary formats, the
CLAIM_SECURITY_ATTRIBUTE_RELATIVE_V1 claim entry, and the conditional
expression bytecode (§2.4.4.17). Peios keeps the binary formats
byte-compatible so security descriptors round-trip with Windows
systems — over the wire and on NTFS volumes.

Deliberate divergences from the reference model are flagged inline as
notes where they occur: permissive ACL-revision parsing, the
repurposing of alarm ACEs for continuous auditing, evaluation-time
generic mapping, the extension of Exists to all four attribute
namespaces, INT64/UINT64 promotion in relational operators, and
virtual-group visibility in Member_of.
