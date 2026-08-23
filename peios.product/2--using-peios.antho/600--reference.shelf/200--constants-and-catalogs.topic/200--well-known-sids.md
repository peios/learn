---
title: Well-known SIDs
type: reference
description: Where the well-known SID catalogue lives — PCDS §4.4 — and the PIP trust label ladder.
related:
  - peios/constants-and-catalogs/overview
  - peios/identity/well-known-principals
  - peios/process-integrity-protection/overview
---

The well-known SID catalogue is **PCDS §4.4**, in the Peios Core Data Structures specification. It is normative there, and is not duplicated here.

It covers the universal SIDs (`S-1-1-0` Everyone, `S-1-3-0` CREATOR OWNER, and the rest), the NT authority SIDs under `S-1-5`, the BUILTIN groups under `S-1-5-32`, domain SID structure, integrity label SIDs under `S-1-16`, capability SIDs under `S-1-15`, service SIDs under `S-1-5-80`, and the PIP trust labels under `S-1-19`.

For the conceptual treatment — which principals matter and why — read [Well-known principals](~peios/identity/well-known-principals).

## A note on the BUILTIN range

PCDS lists the BUILTIN groups KACS assigns meaning to. It deliberately does **not** enumerate `S-1-5-32-547` through `S-1-5-32-583`, which Active Directory defines: KACS gives them no special semantics, and they participate in ACE matching like any other group SID.

An older revision of this reference tabulated them. That table was removed on purpose, not lost — enumerating names the system does not act on implies a behaviour that does not exist.

## PIP trust labels

The `S-1-19-T-L` ladder encodes two dimensions: `T` is the PIP type axis, `L` the trust axis. Dominance requires both to be greater than or equal.

The numeric tiers are in [Other constants](~peios/constants-and-catalogs/other-constants), and the full SID list is in PCDS §4.4. The mechanism is [Process integrity protection](~peios/process-integrity-protection/overview).
