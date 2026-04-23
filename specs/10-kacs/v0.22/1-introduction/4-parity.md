---
title: Compatibility
---

KACS is the security model of Peios. It is not a port or reimplementation of any other system's security model. The design choices -- tokens, Security Descriptors, AccessCheck, structured SIDs, per-thread impersonation -- were made because they solve the problems Peios needs solved: coherent identity, rich per-object access control, scoped delegation, and integrated audit.

These same primitives are used by Active Directory environments. Peios is designed to participate in AD domains as a first-class member: domain-joined Peios machines exchange security data with domain controllers, authenticate via Kerberos, and enforce access policies distributed through Group Policy. This interoperability imposes specific binary format requirements on KACS data structures.

## Format compatibility

The following data structures MUST use the binary formats specified by MS-DTYP, ensuring byte-level compatibility with Active Directory and Samba:

- **Security Identifiers (SIDs)** -- same binary encoding, same comparison rules, same well-known values.
- **Security Descriptors** -- self-relative binary format (MS-DTYP section 2.4.6). An SD from a Windows domain controller, replicated through Samba 4, is evaluated by KACS without translation.
- **Access Control Entries** -- same ACE types, same header format, same access mask layout.
- **Access masks** -- same 32-bit layout: object-specific bits 0--15, standard bits 16--20, special bits 24--25, generic bits 28--31.
- **Conditional ACE expressions** -- same binary bytecode format (MS-DTYP section 2.4.4.17).

## Evaluator compatibility

Given the same token, SD, and desired access mask, KACS SHOULD produce the same access decision as described in MS-DTYP for the standard evaluation model. This ensures that access policies authored in AD environments -- file permissions set via Group Policy, object ACLs on directory entries, central access policies -- behave predictably on Peios machines.

Where Peios departs from the MS-DTYP evaluation model, the divergence is intentional and documented. The following table lists all intentional divergences:

| Area | Divergence | Rationale |
|---|---|---|
| Conditional ACE `@Local.` | Resolved from an AccessCheck parameter, not a token field | Per-call context that varies between access checks |
| Virtual groups in expressions | `Member_of({S-1-3-4})` returns TRUE for the owner | Semantic consistency between SID matcher and expression evaluator |
| INT64/UINT64 promotion | Relational operators promote between INT64 and UINT64 | Without promotion, UINT64 claims are unusable in conditions |
| `Member_of` filtering | Filters by ACE polarity; deny-only groups do not satisfy allow-ACE conditions | Consistent with deny-only group semantics |
| `Exists` scope | Extended to all four attribute namespaces | No reason to restrict existence tests to Local and Resource |
| ACE mask mapping | ACE masks are mapped via GenericMapping at evaluation time | Required for central access policy GENERIC_ALL in recovery ACEs |
| MAXIMUM_ALLOWED semantics | Uses first-writer-wins for both targeted and MAXIMUM_ALLOWED requests | Eliminates desync between "what can I do?" and "can I do this?" |
| Zero desired mask | Succeeds (not ACCESS_DENIED) | "Asked for nothing, got nothing" is a valid answer |
| Alarm ACEs | Repurposed for continuous per-operation auditing | Reserved but never implemented in the reference model |
| Multiple scoped policy ACEs | Allowed per SACL | AND semantics make composition safe |
| Mandatory policy mutability | `mandatory_policy` is immutable on the token | Mutable policy reduces MIC to advisory |
| Impersonation integrity ceiling | Unconditionally enforced; SeImpersonatePrivilege does not bypass it | MIC is a real boundary when mandatory_policy is immutable |
| Impersonation origin check | Dropped | Eliminates hidden impersonation paths |
| PIP determination | Kernel-only, from binary signature; no parent input | One input, one answer, no ambiguity |
| Object type list validation | Rejects duplicate GUIDs and level gaps | Prevents FindNode returning the wrong node |
| Composite equality | Element-wise ordered comparison | Never over-grants |

## Features handled by other subsystems

The following features relevant to a complete security posture are not part of KACS. They are handled by other Peios subsystems.

| Feature | Subsystem |
|---|---|
| Kerberos / NTLM authentication | authd |
| S4U (Service-for-User) | authd |
| Credential storage and protection | authd |
| Active Directory replication | Samba 4 |
| Group Policy distribution | Registry / roles |
| Network share permissions | Samba SMB layer |
| Resource-Based Constrained Delegation | KDC (authd) |
| Authentication Policies and Silos | KDC (authd) |
| Encrypting File System | Future service |
