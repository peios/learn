---
title: How Security Descriptors Work
type: concept
description: The structure of a security descriptor — owner, group, DACL, and SACL — and how objects receive one.
---

A **security descriptor (SD)** is the complete security policy for a protected object. Every secured object on Peios has one. The security descriptor is a self-contained structure — everything the kernel needs to evaluate access is in a single blob.

## The four components

### Owner SID

The owner is the principal that controls the object. By default, the owner can read the security descriptor and modify the DACL — even if no ACE in the DACL explicitly grants them access. This means an owner can always recover control of their own objects.

When a new object is created, the owner is typically set to the user SID from the creating token.

### Primary group SID

The primary group is set from the creating token's primary group. It exists primarily for compatibility and for certain default behaviors. In most access control scenarios, the DACL is what governs access — the primary group does not play a direct role in AccessCheck.

### DACL (Discretionary Access Control List)

The DACL is where access rules live. It is an ordered list of **Access Control Entries (ACEs)** — each one a rule that grants or denies specific rights to a specific principal.

When a thread requests access to an object, AccessCheck walks the DACL from top to bottom, looking for ACEs that match the thread's token. Deny ACEs block access. Allow ACEs grant access. The order of entries matters — an early deny takes precedence over a later allow.

### SACL (System Access Control List)

The SACL controls system-level policy that is not at the owner's discretion:

- **Audit ACEs** — define which accesses generate audit events (successful access, failed access, or both)
- **Mandatory integrity labels** — set the minimum integrity level required to access the object
- **Other system policy** — resource attributes, central access policy references

Modifying the SACL requires the `SeSecurityPrivilege` — ordinary owners cannot change audit or integrity policy on their objects.

## NULL DACL vs empty DACL

This distinction is critical:

| State | Meaning |
|---|---|
| **NULL DACL** | The DACL is absent. No access control is applied — **all access is granted to everyone**. |
| **Empty DACL** | The DACL is present but contains zero entries. No ACE can match — **all access is denied to everyone** (except the owner's implicit rights). |

A NULL DACL is not "no permissions set." It is "no access control at all." This is rarely what you want. An object with a NULL DACL is completely unprotected.

## Where security descriptors are stored

The SD structure is the same regardless of object type, but the storage mechanism varies:

| Object type | Storage |
|---|---|
| Files and directories | Extended attributes on the filesystem |
| Registry keys | The registry's backing store |
| Processes | Kernel memory, attached to the process |
| IPC endpoints | Kernel memory, attached to the endpoint |

The kernel retrieves the SD from the appropriate store when AccessCheck needs it. From the evaluator's perspective, all SDs look the same — the storage is an implementation detail.

## How objects get their security descriptors

No object is created without a security descriptor. When a new object is created, the SD is built from two sources:

1. **The creating token** — provides the owner SID, the primary group SID, and a default DACL
2. **The parent object** — provides inheritable ACEs from its own DACL (if the parent has any)

If an explicit SD is provided at creation time, it takes precedence over these defaults. The mechanics of how parent ACEs are inherited are covered in the inheritance documentation.

The result is that every object is born with a complete security policy. There is no window where an object exists without protection.
