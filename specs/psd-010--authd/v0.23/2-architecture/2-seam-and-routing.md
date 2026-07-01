---
title: The Seam and Routing
---

Two boundaries govern the subsystem: the **seam** between a source and
the broker (what each side is authoritative for), and the **routing
rule** (which side of the broker a given operation flows through).

## The source/broker seam

The seam partitions authority between a principal source and the broker.
It is not a matter of preference: it is dictated by how a domain
directory works, so that lpsd and a future AD source can be
interchangeable.

A source MUST be authoritative for:

- **Credential verification.** The stored verifier and its format live
  in the source and are checked in the source. A verifier MUST NOT
  cross the seam.
- **Account state.** Whether an account is disabled, locked, or expired
  is enforced by the source during verification.
- **The principal's intrinsic identity:** its SID, and its group
  memberships **expanded within the source's own namespace**.
- **Source-native claims** and account attributes.

The broker (authd) MUST be authoritative for:

- **Merging** group contributions across sources (e.g. local groups
  that contain a domain principal — §5.2).
- **Privilege and user-rights assignment** — local/system policy that
  applies in both the local and domain cases.
- **The logon-type rights gate** — whether a principal may perform
  *this* logon type on *this* machine (§5.2).
- **Integrity level** determination and **token shaping**.
- All KACS session and token minting (§5.3).

### The group-expansion guardrail

Group-membership expansion MUST remain in the source and MUST NOT be
performed by the broker. lpsd walks its own membership graph (§3.2); a
domain source obtains an already-expanded, signed membership set from
its directory. The broker re-deriving group membership would be both
expensive and incompatible with how a directory federates trust, so it
is forbidden. The broker only *merges* the membership sets that sources
return; it never *computes* them.

## The routing rule

Whether an operation passes through the broker or goes directly to a
source is decided by one criterion: **source transparency.**

- **Source-transparent operations** — operations that MUST behave
  identically regardless of which source backs the principal — go
  **through authd**, which forwards them to the correct source. These
  are: authentication (Logon), ChangePassword, and self-service
  operations on the caller's own principal. A caller MUST be able to
  perform these without knowing whether it is a local or a domain
  principal.
- **Source-shaped operations** — operations whose form legitimately
  differs between a flat local store and a directory — go **directly to
  a source**. These are account and group administration (create,
  modify, delete users and groups; manage membership) and policy
  management. Forcing these through a common broker surface would
  misrepresent backends that genuinely differ.

Routing to a source (whether by the broker for a transparent operation,
or by an administration client for a source-shaped one) is determined
by the **principal's namespace**: a bare or machine-qualified name
routes to lpsd; a domain-qualified name routes to the domain source.
Administration clients perform this routing through a shared client
library so the rule is implemented once.

> [!INFORMATIVE]
> ChangePassword *must* look the same to a user whether they are local
> or domain, so it is forwarded by the broker. CreateUser legitimately
> differs (a flat RID allocation versus a directory object with a
> distinguished name), so it goes direct. The rule names the boundary
> rather than enumerating every operation.

## Principal-name grammar

authd parses the principal name to choose a source and namespace. Three
forms are accepted; the qualifier is matched case-insensitively (folded
per §3.5), and the bare form is the default:

- **Down-level** `QUALIFIER\name` — `MACHINE\name` (the local machine
  name) and a bare `name` resolve to the local source (lpsd); a domain
  `QUALIFIER` resolves to that domain's source.
- **UPN** `name@SUFFIX` — the local machine suffix resolves to lpsd; a
  domain suffix resolves to that domain's source.
- **Bare** `name` — resolves to the local source.

A name MUST NOT contain both `\` and `@`; a name with both, or an empty
name or qualifier, is `INVALID_REQUEST` (§6.4). A bare name always
resolves to the local source; an unqualified name is never broadcast to
multiple registered sources (§6.1).

## Audit

Because identity *use* (logon) is brokered by authd while identity
*change* (administration) is performed at a source, audit MUST be
centralised at the KMES sink (PSD-003), not at a single emitter. authd
emits logon and session events; a source emits account-change events;
both target the same audit pipeline with a common schema, yielding one
audit stream. No daemon is required to proxy another's audit.
