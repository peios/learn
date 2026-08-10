---
title: The Resolved-Principal Contract
---

The **resolved principal** is the record a source returns to the broker
on successful verification. It is the single source-neutral contract of
the subsystem: every source MUST produce it, and the broker MUST accept
it identically regardless of source (§2.1).

## Design: PAC-isomorphic

The contract is modelled on the Windows PAC (`PAC_LOGON_INFO` plus the
claims blobs): the same authorization information a directory hands a
broker for token assembly. It is **information-isomorphic** to the PAC
but is a clean, versioned format, **not** the literal MS-PAC NDR
encoding and **without** the PAC's KDC/server signatures. The local
source/broker hop is a trusted IPC (§6.2), so no on-wire signature is
needed. A domain source MUST verify a real PAC's signatures and then
translate the verified contents into this format; lpsd synthesises the
format directly from its store.

## Fields

A source MUST populate the following on success.

| Field | Meaning | PAC analogue |
|---|---|---|
| `status` | `ok`, `denied(reason)`, or `must_change_password` (§5.1) | — |
| `user_sid` | The principal's SID (`domain/machine SID` + RID) | `LogonDomainId` + `UserId` |
| `primary_group_sid` | Primary group SID | `LogonDomainId` + `PrimaryGroupId`, or another source-authoritative group SID |
| `account_name`, `display_name`, `upn` | Names | `EffectiveName`, `FullName`, UPN |
| `groups` | Group SIDs with `SE_GROUP_*` attributes, expanded within — and **limited to** — the source's own authority (for lpsd, `machine_sid`-relative SIDs and the local `S-1-5-32` BUILTIN aliases it hosts; for a domain source, that domain's SIDs). authd validates this (§5.2). | `GroupIds` + `ExtraSids` + `ResourceGroupIds` |
| `claims` | User and device claims, typed | `*_CLAIMS_INFO` |
| `account_flags` | Account-control flags | `UserAccountControl` |
| `pw_last_set`, `pw_must_change`, `account_expires` | Advisory policy instants (already *enforced* by the source) | `PasswordLastSet`, `PasswordMustChange`, `KickOffTime` |
| `provenance` | `auth_package`, logon domain name and SID | `LogonServer`, `LogonDomainName`, `LogonDomainId` |
| `projected ids` | the source-authoritative uid for the principal and gids for the groups it owns (§3.6) | `uidNumber`/`gidNumber` |

A source MUST NOT include credential material or any verifier in the
resolved principal. A source MUST NOT include the logon SID: the kernel
injects it at mint (§5.3). A source MUST NOT include a group SID it is
not authoritative to assert: no well-known SID (SYSTEM `S-1-5-18` and the
`S-1-5-*` identity/logon SIDs — authd adds the implicit ones in the
policy phase, §5.2 step 1), and, for a **domain** source, no local
`S-1-5-32` BUILTIN alias, since a domain principal's local-group
membership is authd's to resolve via the merge of §5.2 step 1. lpsd,
which hosts the `S-1-5-32` aliases (§3.1), MAY assert membership in them.
authd MUST reject a resolved principal that violates this (§5.2). The on-wire encoding of the resolved-principal
record — field order, widths, and how `denied(reason)` carries its
audit-only reason — is defined normatively in §6.4.

## What the broker adds

The resolved principal is the source's half of the eventual token. The
broker adds the rest in the policy phase (§5.2) and never expects the
source to supply it: merged local groups, the privilege set, the
integrity level, token shaping, and the `auth_id` linking the token to
the session it creates. The clean division is **"who you are and what
you belong to" (source) versus "what that entitles you to on this
machine" (broker)**.
