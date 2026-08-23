---
title: Security descriptors (wire format)
type: reference
description: Where the byte-level security descriptor layouts are specified — PCDS chapters 4 and 5.
related:
  - peios/wire-formats-reference/overview
  - peios/security-descriptors/acls-and-aces
  - peios/constants-and-catalogs/access-mask-bits
---

The byte-level layout of a security descriptor and everything inside it is specified in **PCDS**, the Peios Core Data Structures specification. It is normative there and is not duplicated here.

| Structure | Section |
|---|---|
| Descriptor header, self-relative form — `Revision`, `Sbz1`, `Control`, and the four offsets | PCDS §5.1 |
| Control flags | PCDS §5.1 |
| ACL header — `AclRevision`, `AclSize`, `AceCount` | PCDS §5.2 |
| ACE header — `AceType`, `AceFlags`, `AceSize` | PCDS §5.4 |
| Per-type ACE body layouts | PCDS §5.4 |
| Access mask bit layout | PCDS §5.3 |
| SID binary format | PCDS §4.1 |
| Claim entry format | PCDS §5.9 |
| Conditional-ACE bytecode | PCDS §5.11 |

Peios uses the MS-DTYP §2.4.6 self-relative format without translation, so a descriptor written by a Windows domain controller and replicated through Samba is evaluated as-is. Where KACS's *evaluator* departs from MS-DTYP — a separate question from the format — the Peios Kernel TRM §3.B has the list.

The **right values** carried in an access mask are catalogued in [Access mask bits](~peios/constants-and-catalogs/access-mask-bits).
