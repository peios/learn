---
title: Departures from MS-DTYP
description: Where KACS departs from MS-DTYP despite using its binary formats, and which features are handled elsewhere rather than here.
---

KACS uses the binary formats MS-DTYP specifies, so a descriptor
authored by a Windows domain controller and replicated through Samba
is evaluated without translation. PCDS specifies those formats
normatively.

Evaluator behaviour is a separate question. Given the same token,
descriptor and desired mask, KACS generally reaches the same decision
MS-DTYP describes — which is what makes policy authored in an AD
environment behave predictably here — but it departs deliberately in
the following places.

| Area | Departure | Why |
|---|---|---|
| Conditional ACE `@Local.` | Resolved from an AccessCheck parameter rather than a token field | The context is per-call and varies between checks. |
| Virtual groups in expressions | `Member_of({S-1-3-4})` returns true for the owner | Keeps the SID matcher and the expression evaluator semantically consistent. |
| INT64/UINT64 promotion | Relational operators promote between the two | Without promotion, `UINT64` claims cannot be used in conditions at all. |
| `Member_of` filtering | Filtered by ACE polarity, so deny-only groups do not satisfy allow-ACE conditions | Consistent with deny-only group semantics everywhere else. |
| `Exists` scope | Extended to all four attribute namespaces | No reason to restrict existence tests to Local and Resource. |
| ACE mask mapping | ACE masks are mapped through GenericMapping at evaluation time | Required for `GENERIC_ALL` in central access policy recovery ACEs (§3.8.8). |
| `MAXIMUM_ALLOWED` | First-writer-wins for targeted *and* maximum-allowed requests | Eliminates disagreement between "what can I do?" and "can I do this?" on a non-canonically ordered DACL. |
| Zero desired mask | Succeeds rather than returning access denied | "Asked for nothing, got nothing" is a valid answer. |
| Alarm ACEs | Repurposed for continuous per-operation auditing (§3.8.9) | Reserved but never implemented in the reference model. |
| Multiple scoped policy ACEs | Several permitted per SACL | AND semantics make composition safe. |
| Mandatory policy mutability | `mandatory_policy` is immutable on the token (§3.2.2) | A mutable policy reduces MIC to advisory. |
| Impersonation integrity ceiling | Enforced unconditionally; `SeImpersonatePrivilege` does not bypass it (§3.5.2) | MIC is a real boundary precisely because the mandatory policy is immutable. |
| Impersonation origin check | Dropped | Eliminates hidden impersonation paths. |
| Impersonation level on primaries | Meaningful and queryable: a ratchet every token carries, bounding everything derived from it (§3.5.1). Windows rejects `TokenImpersonationLevel` on a primary. | Delegation here is a flag authd enforces rather than a property of the credential cache, so the flag itself has to be unforgeable across duplication. |
| PIP determination | Kernel-only, from the binary signature, with no parent input (§3.3.2) | One input, one answer, no ambiguity. |
| Object type list validation | Duplicate GUIDs and level gaps rejected (§3.8.5) | Prevents node lookup returning the wrong node and propagation becoming undefined. |
| Composite equality | Element-wise ordered comparison | Never over-grants. |

## Features handled elsewhere

Several capabilities relevant to a complete security posture are not
KACS's, and are named here so their absence is not mistaken for a gap.
Kerberos and NTLM authentication, S4U, and credential storage and
protection belong to authd, as do Resource-Based Constrained
Delegation and Authentication Policies and Silos through the KDC.
Active Directory replication is Samba's. Group Policy distribution
goes through the registry and roles. Network share permissions belong
to the Samba SMB layer. An Encrypting File System is a future service.
