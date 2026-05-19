---
title: Security descriptors
type: concept
description: Every protected object in Peios — file, registry key, IPC endpoint, service, token, process — has exactly one security descriptor. The descriptor says who owns the object, who can do what to it, and what should be audited about access. This page is the map for the four components and the topics that cover each one in depth.
related:
  - peios/security-descriptors/acls-and-aces
  - peios/security-descriptors/dacl-evaluation
  - peios/security-descriptors/inheritance
  - peios/security-descriptors/ownership
  - peios/security-descriptors/conditional-aces
  - peios/security-descriptors/the-sacl
  - peios/access-decisions/overview
---

A **security descriptor** (often just SD) is the policy attached to every protected object in Peios. Every file, every registry key, every IPC socket, every running process, every token — all of them carry an SD that defines the security policy for that one object. Where the [token](~peios/tokens/overview) is the "who" of an access decision, the SD is the "what to check against".

If you have only ever read or written security descriptors as opaque binary blobs through a system tool, this set of pages is what they were really doing. SDs have four components, each with its own role, its own evaluation rules, and its own gotchas. The point of this topic is to make those visible.

## The four components

Every SD has exactly four parts:

| Component | What it does |
|---|---|
| **Owner** | A single SID identifying who owns the object. The owner has implicit READ_CONTROL and WRITE_DAC rights (with one exception, covered in [Ownership](~peios/security-descriptors/ownership)). |
| **Primary group** | A single SID. Used when CREATOR_GROUP placeholder ACEs are substituted during inheritance. Rarely directly meaningful. |
| **DACL** (Discretionary Access Control List) | The ordered list of ACEs that decides who can do what to the object. This is the part most people mean when they say "the permissions on a file". Controlled by the owner via WRITE_DAC. |
| **SACL** (System Access Control List) | The list of system-level policy ACEs — audit rules, the object's integrity label, resource attributes, central access policy references, PIP trust labels. Controlled by anyone with ACCESS_SYSTEM_SECURITY (which is gated by [`SeSecurityPrivilege`](~peios/privileges/overview)). |

A given SD can have all four components or some subset. An SD without a DACL is not the same as an SD with an empty DACL — see [DACL evaluation](~peios/security-descriptors/dacl-evaluation) for the rule. An SD without an owner is malformed; the access check rejects it.

## What an SD does not contain

Worth knowing what is *not* in an SD, because these things are often mistakenly attributed to it:

- **The object's content or data.** SDs say nothing about what the object is, only about who can use it.
- **The object's type.** Whether you are dealing with a file, a registry key, or a process is the object manager's concern. The SD is the same shape regardless; only the access rights it grants are object-type-specific (because the [GenericMapping](~peios/security-descriptors/acls-and-aces) for each type is different).
- **The token of the principal who is trying to access the object.** That comes from the caller, not the SD. An SD is policy; tokens are subjects; the access check matches them up.
- **Anything about the parent object.** Inheritance is computed *at creation time* — a child object's SD is its own complete value, not a delegation to the parent. See [Inheritance](~peios/security-descriptors/inheritance) for the eager-evaluation model.

These boundaries matter because the SD's job is small and well-defined. Everything else about an object lives somewhere else: the data is in the data path, the type is in the object manager, the access decision is in the access check.

## Where SDs live

Different object types store SDs in different places, but the format and meaning are the same.

| Object type | Storage |
|---|---|
| Files and directories | An xattr (`security.peios.sd`, or `system.ntfs_security` on NTFS volumes) on the inode. |
| Registry keys | Stored by the registry source. |
| Processes | A field on the PSB (process security block). |
| Tokens | A field on the token object itself. |
| Abstract Unix sockets | A field on the socket LSM blob, stamped from the binding thread's effective token at `bind()`. |
| IPC objects | A field on the object's kernel structure. |

The binary format — the **self-relative** layout — is uniform. An SD that was written for a file can be read by a tool that uses the same parser as for a registry key. This consistency is what lets system tools work generically across object types.

Note one important rule: **reading or writing the SD xattr directly is denied unconditionally**. Even with `CAP_DAC_OVERRIDE`. All SD access must go through the appropriate KACS API (`kacs_get_sd`, `kacs_set_sd`, or the equivalent registry-side APIs). The xattr exists so the SD travels with the file across normal filesystem operations (copy, backup, restore by tools that understand xattrs), but the security boundary is the API, not the xattr layer.

## The cost-of-modification asymmetry

A useful intuition: modifying different parts of an SD requires different rights.

| To change | You need |
|---|---|
| The DACL | `WRITE_DAC` on the object (the owner always has this unless suppressed by OWNER RIGHTS). |
| The owner | `WRITE_OWNER` on the object, *plus* a restriction on which SIDs you can name as the new owner (covered in [Ownership](~peios/security-descriptors/ownership)). |
| The SACL | `ACCESS_SYSTEM_SECURITY` — granted by `SeSecurityPrivilege` rather than by the object's DACL. The DACL never grants this right. |

This asymmetry is deliberate. The DACL is what users control to manage their own data. Ownership is a stronger lever — taking ownership is a deliberate administrative act. The SACL is a system-level concern, gated by a privilege held by administrators and audit systems.

## How an SD gets created

There are three ways an object ends up with its SD:

1. **Inherited from a parent.** The most common path: when a child object is created, its SD is computed by combining the parent's inheritable ACEs with the creating principal's defaults. The result is stored on the child as a complete SD. The parent is not consulted again at access-check time. See [Inheritance](~peios/security-descriptors/inheritance).
2. **Explicitly supplied at creation.** The creator passes an SD as a parameter (to `kacs_open` with a create disposition, to a registry key create, etc.). This SD is taken as-is, subject to the rules about what fields the creator may set (the creator must be entitled to name the owner, for instance).
3. **Synthesised by the kernel.** For objects whose storage layer cannot hold an explicit SD (an abstract socket bound by a process that did not provide one, a file on a mount with `synthesize_ephemeral` policy and no parent inheritance), the kernel constructs a default SD from the creating principal's token (`default_dacl`, `owner_sid_index`, `primary_group_index`). The synthesis path is per-object-type but the result is a normal SD.

Once an SD is in place, it is the authoritative policy for the object. Modifying it after creation is a separate operation governed by `kacs_set_sd` and its access requirements.

## The SD as an evaluation target

When the access check runs on an SD, it is not reading every field. The pipeline does specific things with specific parts of the SD in a specific order. The full algorithm lives in [Access decisions](~peios/access-decisions/overview); a brief sketch for orientation:

1. The owner field is consulted to determine implicit rights (and whether they have been suppressed by OWNER RIGHTS).
2. The SACL is scanned for mandatory integrity labels and PIP trust labels — these gate the access independently of the DACL.
3. The DACL is walked, ACE by ACE, in order, applying first-writer-wins.
4. The SACL is scanned again for audit and alarm ACEs that should fire as a result of the access attempt.

Each step has its own page in this topic. The point of mentioning the order here is so that as you read the deeper pages you can see where each component is consulted.

## Where to start

If you want the structural details — what an ACL looks like, what each ACE type means, what bits the access mask uses — read [ACLs, ACEs, and access masks](~peios/security-descriptors/acls-and-aces).

If you want to understand how a DACL actually decides "allowed" or "denied" — first-writer-wins, ACE ordering, the canonical order, MAXIMUM_ALLOWED — read [DACL evaluation](~peios/security-descriptors/dacl-evaluation).

If you want to know how owner implicit rights work and why OWNER RIGHTS can suppress them, read [Ownership and implicit rights](~peios/security-descriptors/ownership).

If you want the inheritance model — how a child's SD is computed from its parent and creator, and why parent changes don't propagate to existing children — read [Inheritance](~peios/security-descriptors/inheritance).

If you want conditional ACEs — the ABAC-style mechanism where access depends on token claims and resource attributes — read [Conditional ACEs](~peios/security-descriptors/conditional-aces).

If you want the SACL specifically — audit, alarm, integrity labels, central access policy references, PIP trust labels — read [The SACL](~peios/security-descriptors/the-sacl).
