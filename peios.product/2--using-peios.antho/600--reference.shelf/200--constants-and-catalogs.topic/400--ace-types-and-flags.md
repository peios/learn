---
title: ACE types and flags
type: reference
description: Where the ACE type and flag catalogues live — PCDS §5.4 — including the AceType constant table and the MIC policy bits.
related:
  - peios/constants-and-catalogs/overview
  - peios/security-descriptors/acls-and-aces
  - peios/access-decisions/mandatory-integrity-control
---

The ACE catalogue is **PCDS §5.4**, in the Peios Core Data Structures specification. It is normative there, and is not duplicated here.

It covers every `AceType` value from 0x00 to 0x15 — the body layout of each family, the `AceFlags` bits, and the ACL revision rules that constrain which types may appear.

Twenty of those values have behaviour. Two do not: 0x04 (`ACCESS_ALLOWED_COMPOUND_ACE`, never implemented anywhere) and 0x15 (`SYSTEM_ACCESS_FILTER_ACE`, an MS-DTYP type Peios has not implemented). Both are named by the kernel ABI so that a decoder can label the byte, but neither affects an access decision: they are skipped when the descriptor is evaluated and preserved unchanged when it is written back. `sd` has no name for either and prints them as `OTHER(0x04)` and `OTHER(0x15)`.

## Two names per type

PCDS names both the ACE **structure** and the `AceType` **constant** that selects it, because a reader may arrive with either — one from a declaration, the other from a hex dump. `ACCESS_ALLOWED_ACE` is the structure; `ACCESS_ALLOWED_ACE_TYPE` is the constant whose value is 0x00.

The headers use a third spelling, moving the qualifier to the front: `KACS_ACE_TYPE_ACCESS_ALLOWED`. The Peios Kernel TRM §3.A maps the two vocabularies.

## Inheritance flags

The four propagation flags and the `INHERITED_ACE` provenance flag are catalogued with the inheritance algorithm in PCDS §5.6, rather than with the type values.

## MIC policy bits

The mask of a `SYSTEM_MANDATORY_LABEL_ACE` carries policy bits saying what a non-dominant caller may not do. Those bits are in PCDS §5.4 alongside the ACE type; the mechanism is [Mandatory integrity control](~peios/access-decisions/mandatory-integrity-control).
