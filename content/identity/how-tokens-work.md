---
title: How Tokens Work
type: concept
order: 30
---

A **token** is the kernel object that represents a thread's identity. It is created when a principal authenticates and captures everything the kernel needs to make access decisions — the principal's SID, their group memberships, their privileges, and their trust level.

> [!NOTE]
> A token is a **runtime snapshot**. It reflects the principal's identity and policy at the moment of authentication. If a user is later added to a new group or granted a new privilege in the directory, existing tokens are unaffected. The change takes effect the next time the user authenticates and a new token is built.

## What a token contains

| Field | Description |
|---|---|
| **User SID** | Identifies the principal this token represents |
| **Group SIDs** | The groups the principal belongs to, each with flags indicating its state (enabled, mandatory, deny-only, and others) |
| **Privileges** | A set of system-wide rights, each either enabled or disabled |
| **Integrity level** | The token's trust tier — Untrusted, Low, Medium, High, or System |
| **Logon session** | A reference to the authentication event that created this token |
| **Token source** | Identifies what created the token (the authentication service, the kernel at boot, a filter operation) |
| **Default DACL** | The access control list applied to new objects this token creates when no explicit security is specified |

## Tokens are per-thread

Every thread in the system carries a token. In the common case, all threads in a process share the same token — the one the process inherited from its parent. But individual threads can temporarily carry a different token, allowing a server thread to act on behalf of a client while other threads in the same process are unaffected. This per-thread model is covered in detail in the impersonation pages.

## Immutable identity, adjustable policy

A token's **identity** is fixed at creation:

- The user SID cannot change
- The list of group SIDs cannot change
- The integrity level cannot change

A token's **policy** can be adjusted at runtime:

- Individual privileges can be enabled or disabled
- Individual groups can be enabled or disabled

This distinction keeps the identity stable — a token always represents the same principal with the same group memberships — while allowing a process to narrow its own authority. A process can disable a privilege it doesn't currently need, reducing the damage if it is compromised. It cannot grant itself a privilege it was never assigned.

## How tokens are created

Tokens enter the system through three paths:

**Kernel bootstrap.** At boot, the kernel creates the SYSTEM token — the identity of the operating system itself. This token carries all privileges and the highest integrity level. The init process inherits it and uses it to start the core system services.

**Authentication.** When a user or service authenticates, the authentication service looks up the principal in the directory, resolves group memberships and privilege assignments, and creates a token. This is how most tokens enter the system.

**Filtering.** An existing token can be used to create a more restricted copy. Filtering can remove privileges, set groups to deny-only, or apply other restrictions. The result is a new token that can do less than the original — never more. This is used to create reduced-privilege tokens for less-trusted contexts.

## Token inheritance

When a process creates a child, the child inherits a copy of the parent's token. The child starts life with the same identity, groups, privileges, and integrity level as its parent.

This inheritance is the default. The system can override it — for example, the init process creates tokens for services rather than letting them inherit SYSTEM. But unless something explicitly intervenes, identity flows from parent to child.
