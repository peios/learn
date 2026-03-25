---
title: Understanding Application Confinement
type: concept
order: 10
---

**Application confinement** inverts the default access model. A normal process can access anything the DACL grants to its identity. A confined process starts from **nothing** — access is denied by default, regardless of the token's user SID, group memberships, or privileges. The only way a confined process can access an object is if the object explicitly opts in.

## Why confinement exists

Some applications should not have access to everything the user can access. A media player does not need to read the user's SSH keys. A document viewer does not need to write to system configuration. A downloaded application should be sandboxed until it proves trustworthy.

Without confinement, these applications run with the user's full token — they can access anything the user can access. With confinement, the application can only touch objects that know about it and have chosen to allow access.

## How confinement works

A confined token carries three elements:

| Element | Purpose |
|---|---|
| **Confinement SID** | A unique SID identifying this confined application. When present on the token, confinement is active. |
| **Capability SIDs** | A set of declared capabilities — what the application needs access to. Objects can grant access to specific capability SIDs. |
| **Confinement exempt** | An escape hatch. When set, confinement restrictions are not evaluated. For compatibility with software that cannot operate under confinement. |

AccessCheck evaluates confinement as a **final mask** over the normal result. The normal pipeline runs first — integrity checks, DACL walk, privilege overrides — and produces a set of granted rights. The confinement check then independently evaluates the DACL, matching only against the confinement SID and capability SIDs. The final result is the **intersection**: only rights that both evaluations agree on are granted.

## What confinement blocks

Confinement is an absolute boundary. Things that normally augment access are suppressed:

- **Privileges do not bypass confinement.** `SeBackupPrivilege`, `SeTakeOwnershipPrivilege`, `SeSecurityPrivilege` — none of them can grant access that the confinement check denies.
- **Owner implicit rights are skipped.** A confined application does not receive READ_CONTROL or WRITE_DAC even if it owns the object.
- **SACL access is unreachable.** Since SACL access is entirely privilege-controlled and privileges do not bypass confinement, a confined application cannot access any object's SACL.

The application's user identity — which might be SYSTEM, an administrator, or any other powerful principal — is irrelevant inside the confinement boundary.

## How objects opt in

For a confined application to access an object, the object's DACL must contain an ACE that grants access to one of:

- The application's **confinement SID** — grants access to this specific application
- One of the application's **capability SIDs** — grants access to any application that declared this capability
- The well-known **ALL_APPLICATION_PACKAGES** SID — grants access to all normal confined applications

Objects that do not carry any of these ACEs are inaccessible to confined processes — regardless of what other ACEs exist in the DACL.

## Strict confinement

Normal confined tokens carry the `ALL_APPLICATION_PACKAGES` capability, giving them access to system objects that broadly opt in to confinement. For stronger sandboxing, this capability can be omitted — creating a **strictly confined** token.

A strictly confined token can only access objects that grant to `ALL_RESTRICTED_APPLICATION_PACKAGES` (a narrower well-known SID that far fewer objects grant to) or to the application's own specific capability SIDs. The default access surface is much smaller.

Strict confinement is not a separate kernel mechanism — the evaluation is identical. The difference is which well-known SIDs are present on the token at creation time. It is a policy decision.

## When to use confinement

Confinement is appropriate for:

- **Untrusted applications** — downloaded software, third-party plugins
- **Single-purpose services** — applications that need access to a narrow set of resources
- **Defense in depth** — limiting the blast radius even for trusted applications that handle untrusted input

If a service needs broad access to the system, confinement is not the right tool. The solution is to not confine it and rely on the DACL, privileges, and integrity levels for access control.
