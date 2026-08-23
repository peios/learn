---
title: CAAP format
type: reference
description: Where the central access policy wire format is specified.
related:
  - peios/wire-formats-reference/overview
  - peios/central-access-policies/policies-and-rules
---

The central access policy wire format — the structure `kacs_set_caap` accepts — is specified in the **Peios Kernel TRM §3.A**, the KACS ABI reference.

The conceptual model, and what the structures mean, is [Policies and rules](~peios/central-access-policies/policies-and-rules).

## Shape, in summary

Fields are length-prefixed: each part begins with a 32-bit byte count followed by that many bytes, and an absent field has length zero. That convention runs through the policy blob, its rules, and each rule's applies-to expression and SACL.

The limits that bound it — 256 KB per wire spec, 256 rules per policy, 64 KB per applies-to expression — are in [Other constants](~peios/constants-and-catalogs/other-constants).

The applies-to expression and the rule SACLs use the same conditional-ACE bytecode as a conditional ACE, specified in PCDS §5.11.
