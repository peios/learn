---
title: Inheritance
type: concept
description: When a new object is created, its security descriptor is computed by combining the parent's inheritable ACEs with the creator's defaults. The result is stored on the child as a complete SD — the kernel never walks the parent at access-check time. This page covers the eager-evaluation model, the inheritance flags, CREATOR_OWNER/GROUP substitution, and the protected-ACL flag.
related:
  - peios/security-descriptors/overview
  - peios/security-descriptors/acls-and-aces
  - peios/security-descriptors/ownership
  - peios/identity/well-known-principals
---

When a new object is created under a parent — a file in a directory, a registry key under another key — the new object gets its own security descriptor. The kernel computes that SD at creation time by combining inheritable ACEs from the parent's SD with whatever the creator supplied or defaulted. The result is stored on the child as a **complete, self-contained SD**. From that point on, the access check on the child consults only the child's own SD; the parent is not walked.

This is the **eager evaluation** model. It has one large consequence: **modifying a parent's inheritable ACEs does not propagate to existing children**. The children's SDs were computed when they were created and are now their own. Whatever changes you make to the parent affect only objects created after the change. Children that already exist keep the SDs they had.

This page covers the inheritance algorithm — what counts as inheritable, how the merge works, the special placeholders (`CREATOR_OWNER`, `CREATOR_GROUP`), and the `SE_DACL_PROTECTED` and `SE_SACL_PROTECTED` flags that opt an object out of inheritance entirely.

## Eager vs lazy

Two models are possible:

- **Lazy inheritance**: a child has no inherited ACEs of its own; access checks on the child walk the parent SD too. Changes to the parent propagate immediately.
- **Eager inheritance**: a child's SD is fully computed at creation; access checks consult only the child. Changes to the parent affect future children only.

Peios uses eager inheritance, like the access-control model it grew out of. The advantages: access checks are local (you only need one SD's worth of data), no walking up directory trees during evaluation, no concurrency issues with "the parent moved between my permission check and the operation". The disadvantage: when you change a parent's permissions, you need a separate sweep to propagate the change to existing children — a tool's job, not the kernel's.

In practice, eager inheritance means: when an administrator changes a directory's DACL and wants the change to apply to existing files, they need a propagation tool. The kernel does not do this automatically and provides no syscall for "re-inherit all children". A propagation tool walks the tree and rewrites child SDs explicitly.

## The inheritance flags

Four ACE flags control how an ACE propagates to children. They are the same four mentioned on the [ACLs and ACEs](~peios/security-descriptors/acls-and-aces) page:

| Flag | Effect at creation of a child |
|---|---|
| `OBJECT_INHERIT_ACE` (`OI`, 0x01) | The ACE inherits to children that are **non-containers** (files, not directories). |
| `CONTAINER_INHERIT_ACE` (`CI`, 0x02) | The ACE inherits to children that are **containers** (directories). |
| `NO_PROPAGATE_INHERIT_ACE` (`NP`, 0x04) | The ACE inherits to direct children but its `OI`/`CI` flags are **cleared** in the inherited copy, so it stops propagating after one level. |
| `INHERIT_ONLY_ACE` (`IO`, 0x08) | The ACE is **not evaluated** on the object it sits on. It exists only to be inherited. |

Common combinations:

| Flags | Meaning |
|---|---|
| `CI \| OI` | Inherit to all descendants, files and directories, recursively. The most common pattern. |
| `CI` | Inherit to descendant directories only. |
| `OI` | Inherit to descendant files only. |
| `CI \| OI \| IO` | Apply to descendants but not to this object. |
| `CI \| OI \| NP` | Apply to immediate children only. Grandchildren do not inherit. |
| `(none)` | This ACE does not inherit. It applies only to this object. |

The `INHERIT_ONLY_ACE` (`IO`) flag is what lets you say "this rule is for children, not for the parent itself". An `IO` ACE is invisible to the access check on its own object; the DACL walk skips it. But it is copied to children at creation time.

## The merge algorithm

When a new child is created, the kernel needs to produce the child's SD from three inputs:

1. The **parent's** SD. Inheritable ACEs from here will be copied (with adjustments) into the child.
2. The **creator's** SD, if one was supplied as a parameter to the create call. This contains explicit ACEs the creator wants on the new object.
3. The **creator's token**. Provides defaults (owner, primary group, default DACL) when the creator did not supply specific values.

The merge proceeds as follows:

1. **Compute the child's owner.** If the creator supplied an owner in the explicit SD, use it (subject to the same-self-or-owner-group rule from [Ownership](~peios/security-descriptors/ownership)). Otherwise, use the creator's token's default owner.
2. **Compute the child's primary group.** Same rule: explicit SD if present, otherwise the creator's token's default primary group.
3. **Compute the child's DACL.** Start with explicit ACEs from the creator's SD (or, if the creator did not supply a DACL, the creator's token's `default_dacl`). Then append inheritable ACEs from the parent's DACL — but only those whose flags say they should propagate to this kind of child (container or non-container).
4. **Compute the child's SACL.** Same algorithm as the DACL, applied to SACL ACEs.

Each inherited ACE goes through a small transformation as it is copied:

- The `INHERITED_ACE` flag (0x10) is **set** in the copy. This marks it as having come from inheritance, not from explicit assignment.
- If `NO_PROPAGATE_INHERIT_ACE` was set, the `OI` and `CI` flags are **cleared** in the copy. (NP itself is also typically cleared.)
- If the ACE's SID is `CREATOR_OWNER` (`S-1-3-0`), the SID is **substituted** with the new child's owner SID.
- If the ACE's SID is `CREATOR_GROUP` (`S-1-3-1`), the SID is **substituted** with the new child's primary group SID.

The CREATOR substitution is the mechanism that makes inheritable ACEs portable. A directory's DACL containing `CI | OI ACCESS_ALLOWED CREATOR_OWNER GENERIC_ALL` means "every file or subdirectory created under here grants full access to whoever owns it". The owner of each child is different; the substitution at creation time fills in the right SID for each one.

## Sources of an inherited SD, ranked

Which source wins for each component of the child SD, in order:

| Component | First source | Second source | Third source |
|---|---|---|---|
| Owner | Creator's explicit SD (if owner present) | Creator's token's default owner | (none — must be present) |
| Primary group | Creator's explicit SD (if group present) | Creator's token's default primary group | (none — must be present) |
| DACL | Creator's explicit SD (if DACL present) | Creator's token's `default_dacl` | (no DACL means NULL DACL) |
| SACL | Creator's explicit SD (if SACL present) | (no fallback) | (no SACL means no audit policy) |

Plus, in every case, **inheritable ACEs from the parent are appended** to whatever DACL/SACL was chosen as the base. The parent's contributions never replace; they always extend.

This means: a creator who supplies an explicit DACL gets *that* DACL **plus** the inheritable ACEs from the parent. They cannot exclude the parent's ACEs except by setting the protected flag (see below).

## Protected ACLs

There is an opt-out: the `SE_DACL_PROTECTED` and `SE_SACL_PROTECTED` flags in the SD's control field.

| Flag | Effect |
|---|---|
| `SE_DACL_PROTECTED` (0x1000) | The child's DACL does not accept inheritable ACEs from the parent. Only the explicit ACEs in the creator's SD (or the creator's `default_dacl`) appear. |
| `SE_SACL_PROTECTED` (0x2000) | Same, for the SACL. |

When a creator sets these flags on the explicit SD they pass to the create call, the resulting child's DACL/SACL is purely what the creator wrote. The parent might have a hundred inheritable ACEs; none of them appear on the child.

Protected ACLs are used when an object should be administered without reference to its container. A service that creates files whose access should be controlled only by the service, not by whoever happens to own the directory it lives in, sets `SE_DACL_PROTECTED` on each file's explicit SD at creation.

The flags can also be set after creation, via a subsequent `kacs_set_sd`. Doing so does not retroactively *remove* previously inherited ACEs — they were copied at creation time and are now the child's own — but it does protect against future re-inheritance if a propagation tool sweeps the tree.

## Auto-inherit flags

Two more SD control flags work alongside the protected flags:

| Flag | Effect |
|---|---|
| `SE_DACL_AUTO_INHERIT_REQ` (0x0100) | Set by a creator that wants the child to participate in auto-inheritance. Tools that propagate inherited ACEs use this to decide whether to update the child. |
| `SE_DACL_AUTO_INHERITED` (0x0400) | Set by the kernel on a child whose inherited ACEs have been computed by the auto-inheritance algorithm. |

The corresponding SACL pair (`SE_SACL_AUTO_INHERIT_REQ`, `SE_SACL_AUTO_INHERITED`) works the same way.

These flags exist so tools can distinguish "this child wants automated propagation" from "this child has its own bespoke DACL the user wrote by hand". A propagation tool sweeping a tree typically updates only children with the auto-inherit flags set, leaving hand-crafted DACLs untouched.

## What inheritance does *not* do

A handful of things often attributed to inheritance but not done by it:

- **Inheritance does not happen at access-check time.** Once a child has its SD, the parent is not consulted on access decisions. Inheritance is purely a creation-time activity.
- **Inheritance does not retroactively update children.** A change to a parent's inheritable ACEs is invisible to children created before the change. Propagation requires an explicit sweep.
- **Inheritance does not chain across moves.** Moving a file from directory A to directory B does not re-run inheritance against B. The file's SD remains whatever it was. (Copying is a different operation; it creates a new object, which does go through inheritance.)
- **Inheritance does not preserve ACE order.** Inheritable ACEs from the parent are appended to the explicit ACEs from the creator. If you want canonical order, the creator needs to either start from the parent's order and intersperse, or run a canonicalisation pass afterwards.

## Inheritance and creator-supplied SDs

A subtle interaction worth knowing: when a creator passes an explicit SD to the create call, the explicit ACEs go *before* the inherited ones. This means the creator's ACEs sit higher in the DACL than the parent's, and first-writer-wins favours them.

If the parent says "deny X" and the creator says "allow X", the creator's allow wins because it sits first. If the canonical order says the parent's inherited deny should win (because explicit ACEs from the creator should not override the parent's policy), the creator needs to either *not* supply a competing ACE or arrange the explicit SD to use the protected-ACL flag.

This is one of the reasons creators usually pass **no** explicit DACL (relying on the default-DACL + parent-inheritance merge) rather than constructing a custom SD. The latter is correct in cases where the creator knows exactly what the child's policy should be; the former is correct in cases where the creator just wants the natural policy of its location.
