---
title: Scope
description: What PCDS defines — GUID, LUID, SID and the Security Descriptor family — and what it deliberately leaves to the Peios Kernel TRM.
---

This document defines the common binary data structures shared across
Peios subsystems: three identifier types — the Globally Unique
Identifier (GUID), the Locally Unique Identifier (LUID), and the
Security Identifier (SID) — and the Security Descriptor (SD) family.

This document covers:

- GUID — binary format, string representation, comparison semantics,
  and generation requirements
- LUID — binary format, comparison semantics, and allocation model
- SID — binary format, string representation, comparison
  semantics, and the well-known SID catalogue
- SD — the security descriptor structure and its subtypes: ACL and
  ACE formats, access masks, ACE ordering, inheritance, ownership,
  conditional ACEs and their bytecode, claim attributes, and
  resource attributes

This document does not cover:

- Well-known GUID and LUID values — defined in the specifications
  of the subsystems that declare them
- SID-bearing aggregate structures such as SID_AND_ATTRIBUTES —
  described in the Peios Kernel TRM §3.2.2
- The access-check algorithm that evaluates these structures —
  described in the Peios Kernel TRM §3.8
- Per-object-type SD storage locations — described in the Peios
  Kernel TRM §3.3.3 for processes and §3.9.5 for files
- Application-specific identifier namespaces

Three of those exclusions point at a manual rather than at another
specification, which is deliberate and worth stating once. KACS — the
kernel's access-control implementation — is described in the Peios
Kernel TRM §3 and is not separately specified. Peios does not offer a
standard from which a second, independent access-control implementation
could be built; it offers a manual describing the one that exists.

What a third party does need is the other half: the structures that
cross the boundary into that implementation, and the rules for reading
and writing them. That is this document, and it is specified. Where a
structure's meaning depends on what KACS does with it, this document
names the manual article that describes the behaviour rather than
restating it (Conventions §4.7).
