---
title: Understanding Access Control on Peios
type: concept
description: Every secured object carries a security descriptor evaluated by a single function — AccessCheck.
related:
  - peios/access-control/how-security-descriptors-work
  - peios/access-control/access-control-lists
  - peios/access-control/how-accesscheck-works
  - peios/identity/understanding-identity
---

Every secured object on Peios — every file, registry key, IPC endpoint, and process — carries a **security descriptor (SD)**. The security descriptor is the object's security policy: it defines who owns the object, who can access it, and what gets audited.

When a thread attempts to access an object, the kernel evaluates the thread's **token** against the object's **security descriptor**. This evaluation is performed by a single function called **AccessCheck** — the same function, the same logic, for every object type in the system.

## What a security descriptor contains

| Component | Purpose |
|---|---|
| **Owner SID** | The principal that owns this object |
| **Primary group SID** | The object's primary group (used in certain default and compatibility scenarios) |
| **DACL** | The Discretionary Access Control List — an ordered list of rules that define who is granted or denied access |
| **SACL** | The System Access Control List — rules that control auditing, mandatory integrity labels, and other system-level policy |

The DACL is where most access policy lives. Each entry in the DACL is an **Access Control Entry (ACE)** — a rule that says "this principal is allowed (or denied) these specific rights." AccessCheck walks the DACL to determine whether the requesting token has the rights it needs.

The SACL is optional and governs system-level concerns — which accesses generate audit events, what integrity level is required, and other policy that is not at the owner's discretion.

## Ownership

Every security descriptor has an **owner**. By default, the owner is granted the right to read the security descriptor and modify the DACL. This ensures that no object becomes permanently inaccessible — the owner can always fix the access rules.

Ownership can be transferred. A principal with the `SeTakeOwnershipPrivilege` can claim ownership of any object. The owner's default rights can also be adjusted — expanded or restricted — through a special ACE type covered in the access control documentation.

## One model for all objects

The same security descriptor structure protects every type of object. A file's SD, a registry key's SD, and a process's SD all contain the same components — owner, group, DACL, SACL — and are evaluated by the same AccessCheck logic.

The specific **rights** differ by object type (a file has read and write data rights, a registry key has query and set value rights), but the structure, evaluation, and concepts are identical. Learning how access control works for one object type teaches you how it works for all of them.
