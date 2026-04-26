---
title: Positive Confinement
type: concept
description: How capability SIDs can be used as group memberships to grant access additively — reusing the confinement vocabulary without the confinement gate.
related:
  - peios/confinement/understanding-confinement
  - peios/access-control/how-accesscheck-works
  - peios/identity/understanding-identity
---

Application confinement restricts access — a confined process can only reach objects where both the normal access check and the confinement check agree. **Positive confinement** is a convention that uses the same capability SIDs to do the opposite: grant a process access to resources it would not otherwise have.

## The problem positive confinement solves

Confinement creates a useful vocabulary. When you confine applications, you define capability SIDs like `musicLibrary` or `modifyDns`, and you add ACEs for those capabilities to the objects that confined applications need to reach. Over time, the system accumulates a rich set of capability ACEs on objects across the system — a fine-grained map of "what kind of access does this resource offer?"

But sometimes an unconfined service needs narrow access to another service's resources. A DHCP daemon needs to update DNS records. A log collector needs to read application journals. A backup agent needs to read database files.

Without positive confinement, you have two options:

- **Run the service as a user that already has access.** This often means giving it broader access than it needs — the user might have access to many things the service should not touch.
- **Add the service's user SID to every object it needs.** This is precise but fragile — you are scattering a specific user identity across many DACLs, and it breaks if the service identity changes.

Positive confinement offers a third option that is both precise and maintainable.

## How it works

A capability SID is just a SID. Nothing about its structure limits where it can appear. In normal confinement, capability SIDs live in the token's **confinement capabilities set**, where they participate in the confinement intersection check. But the same SID can be placed in the token's **normal groups set**, where it participates in the regular DACL walk — just like any other group membership.

When a capability SID appears as a group membership:

- The normal DACL walk sees it, matches it against ACEs in the object's DACL, and grants the corresponding rights
- No confinement check is involved — the access is additive
- The process gains access to any object that has an ACE for that capability, without needing its user SID in the object's DACL

This is positive confinement: **using capability SIDs as group memberships to grant access through the normal access check path.**

## Example: DHCP updating DNS

A DNS service confines its applications and defines a `modifyDns` capability. It places an ACE on its control socket:

```
Allow  modifyDns  SOCKET_WRITE
```

Any confined application carrying the `modifyDns` capability can write to this socket — subject to the confinement intersection.

Now the DHCP service needs to update DNS records when leases change. The DHCP service is not confined — it is a trusted system daemon. Instead of adding the DHCP service's user SID to the DNS socket's DACL, you add the `modifyDns` capability SID to the DHCP service's **group memberships**.

The DHCP service now has access to the DNS socket through the normal DACL walk. The capability ACE that was placed there for confined applications works equally well as a group grant for the DHCP service. No new ACE is needed on the object. No confinement is involved.

If the DHCP service is later replaced, migrated, or run under a different user identity, nothing changes on the DNS side — the new service just needs the `modifyDns` group membership.

## Where the SID lives matters

The same capability SID has different effects depending on where it appears on the token:

| Placement | Access check behavior | Effect |
|---|---|---|
| **Confinement capabilities set** | Participates in the confinement intersection check | Restrictive — access is only granted if both the normal check and the confinement check agree |
| **Normal groups set** | Participates in the normal DACL walk | Additive — grants access to any object with an ACE for that capability |

If a token carries the same SID in both places, both checks see it. The normal DACL walk matches it as a group, granting access. The confinement check matches it as a capability, also granting access. The intersection still passes. There is no conflict — but there is also no reason to do this deliberately.

> [!IMPORTANT]
> A capability SID in the groups set does **not** bypass confinement. If the token is confined, the confinement intersection still applies. A confined token with a capability SID only in its groups set — but not in its confinement capabilities set — will still be denied by the confinement check, because the confinement check only looks at confinement capabilities, not groups.

## Why this works well on Peios

Positive confinement is particularly useful on Peios because the system makes aggressive use of confinement for application isolation. This means capability ACEs already exist on objects throughout the system — services, sockets, registry keys, shared directories. The vocabulary is already there.

Rather than building a separate role or group system for cross-service access, positive confinement reuses what confinement already built. The capability SID that means "can modify DNS records" means the same thing whether it appears as a confinement capability or a group membership — the difference is only in how the access check evaluates it.

## When to use positive confinement

Positive confinement is appropriate when:

- A service needs **narrow, well-defined access** to another service's resources
- The target resources **already carry capability ACEs** from confinement
- You want access grants that are **independent of the service's user identity** — surviving identity changes, migrations, and redeployment
- You want to express access in terms of **what the service does** rather than **who the service is**

Positive confinement is not a replacement for confinement. It does not sandbox anything. It is a convention for reusing the SID vocabulary that confinement creates to solve a different problem — granting precise cross-service access without scattering user SIDs across the system.
