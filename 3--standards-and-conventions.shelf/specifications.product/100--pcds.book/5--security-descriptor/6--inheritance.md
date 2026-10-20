---
title: SD Inheritance
description: How inheritable ACEs propagate from a container to a new child — the inheritance flags, CREATOR OWNER and CREATOR GROUP substitution, and the algorithm itself.
---

Security Descriptors propagate structurally. When a file is created in a
directory, the directory's inheritable ACEs flow down to the new file's
SD. This automatic propagation is inheritance.

Inheritance applies to objects with a container/child relationship:
directories contain files and subdirectories, registry keys contain
subkeys and values. Objects without a container parent (standalone IPC
endpoints, tokens, processes) do not inherit.

## Inheritance flags

Four flags in the ACE header's AceFlags field control propagation:

| Flag | Value | Description |
|---|---|---|
| OBJECT_INHERIT_ACE (OI) | 0x01 | Inherited by non-container children (files). For container children (subdirectories), inherited as inherit-only unless NP is also set. |
| CONTAINER_INHERIT_ACE (CI) | 0x02 | Inherited by container children (subdirectories). The inherited ACE remains inheritable (propagates to grandchildren) unless NP is also set. |
| NO_PROPAGATE_INHERIT_ACE (NP) | 0x04 | When inherited, OI and CI flags are cleared on the copy. One-level inheritance. |
| INHERIT_ONLY_ACE (IO) | 0x08 | Does not apply to the object it is attached to. Exists only to be inherited by children. |

A fifth flag records provenance:

| Flag | Value | Description |
|---|---|---|
| INHERITED_ACE | 0x10 | Set on ACEs created through inheritance (not explicitly placed). Determines ordering in canonical form. |

## Common flag combinations

| Flags | Meaning |
|---|---|
| CI \| OI | Inherit to everything — containers and non-containers, recursively. |
| CI | Inherit to containers only, recursively. |
| OI | Inherit to non-containers only. Containers receive it as inherit-only. |
| CI \| OI \| IO | Inherit to everything, but do not apply to this object. |
| CI \| OI \| NP | Inherit to immediate children only. |
| CI \| NP | Inherit to immediate child containers only. |
| (none) | No inheritance. Applies only to this object. |

## CREATOR OWNER and CREATOR GROUP

Two well-known SIDs receive special treatment during inheritance:

- **CREATOR OWNER (`S-1-3-0`)** — when an ACE with this SID is inherited
  by a child object, the SID is replaced with the owner SID of the new
  object (as determined by the owner computation above).

- **CREATOR GROUP (`S-1-3-1`)** — replaced with the primary group SID of
  the creating principal.

Substitution happens at inheritance time, in each ACE that applies to the
new object. An inherit-only ACE keeps the placeholder, so that each object
further down resolves it to its own owner or group (see the inherited ACEs
below).

## The ACEs a child inherits

Each ACE of the parent's ACL contributes to a new child as follows. The
same rule applies to the DACL and the SACL.

1. **Whether it passes.** An ACE passes to a container child if it has CI,
   or OI without NP. It passes to a non-container child if it has OI.
   INHERIT_ONLY on the parent's ACE plays no part. An ACE that does not
   pass contributes nothing.

2. **The copy's flags.** The copy has INHERITED_ACE set and INHERIT_ONLY
   cleared, with three exceptions:
   - An ACE with OI and neither CI nor NP reaches a container as
     inherit-only (OI, IO): it applies to the objects inside, not to the
     container.
   - NP clears OI, CI and NP from the copy. The copy applies to the child
     and goes no further.
   - A non-container's copy has no OI, CI, NP or IO.

   Flags other than these (SUCCESSFUL_ACCESS_ACE, FAILED_ACCESS_ACE) are
   kept.

3. **Resolution.** A copy that applies to the child (IO clear) has
   CREATOR OWNER and CREATOR GROUP substituted, and its generic rights
   mapped through the child's GenericMapping (see below).

4. **The split.** An ACE that names CREATOR OWNER or CREATOR GROUP, or
   carries generic rights, and whose copy both applies to a container
   child and goes on from it (OI or CI still set), gives the child **two**
   ACEs, written one after the other:
   - the resolved copy, with OI, CI, NP and IO cleared, applying to the
     child alone; and
   - an inherit-only copy (the copy's flags with IO set), **left as
     written**: the placeholder unsubstituted and the generic rights
     unmapped.

   Resolving the ACE once and carrying the result down would grant the
   first creator over everything beneath, and map rights through one
   object type's mapping for objects of another. Carrying it unresolved
   would grant nothing here. A non-container gets the resolved copy alone.
   Every other ACE is inherited as one copy.

For example, a directory whose DACL holds `(A;OICIIO;GA;;;CO)` and
`(A;OICI;GR;;;AU)` gives a new subdirectory owned by alice
`(A;ID;FA;;;alice)(A;OICIIOID;GA;;;CO)(A;ID;FR;;;AU)(A;OICIIOID;GR;;;AU)`,
and a new file in it `(A;ID;FA;;;alice)(A;ID;FR;;;AU)`.

## Inheritance algorithm

When a new object is created, its SD is computed from up to three
sources:

1. **Parent SD** — provides inheritable ACEs.
2. **Creator SD** — an explicit SD provided by the caller (if any).
3. **Creator token** — provides the default owner, primary group, and
   default DACL.

A creator SD with SE_SERVER_SECURITY set is rejected; see §5.1.

### Owner

If the creator SD specifies an owner, use it. Otherwise, use the token's
owner SID.

### Group

If the creator SD specifies a group, use it. Otherwise, use the token's
primary group SID.

### DACL

The DACL is computed by merging explicit ACEs from the creator SD with
inheritable ACEs from the parent SD:

- If no creator SD is supplied and the parent has inheritable ACEs: the
  new object's DACL consists entirely of inherited ACEs from the parent.

- If no creator SD is supplied and the parent has no inheritable ACEs:
  the new object's DACL is the token's default DACL. If the token has no
  default DACL, the new object's DACL is null: SE_DACL_PRESENT is clear
  and the DACL offset is zero.

- If a creator SD is supplied but has no DACL (SE_DACL_PRESENT not set):
  the new object's DACL is computed as if no creator SD was supplied
  (inherit from parent, or fall back to the token's default DACL, or
  null DACL if the token has no default DACL).

- If a creator SD is supplied with a DACL (SE_DACL_PRESENT set):
  - Explicit ACEs from the creator SD are preserved.
  - If the creator SD's DACL is not protected (SE_DACL_PROTECTED not
    set) and SE_DACL_AUTO_INHERIT_REQ is set on the creator SD:
    inheritable ACEs from the parent are appended after the explicit
    ACEs. If SE_DACL_AUTO_INHERIT_REQ is not set, only the creator's
    explicit ACEs are used (no parent inheritance).
  - If the creator SD's DACL is protected: parent inheritance is
    blocked. Only the creator's explicit ACEs are used.

In all cases, the resulting DACL is post-processed:

- CREATOR OWNER / CREATOR GROUP SIDs are substituted with the actual
  owner and group in every ACE that applies to the object (INHERIT_ONLY
  clear). This substitution applies to the ACE's SID field
  only. ApplicationData — conditional expression bytecode — is copied
  verbatim: no SID substitution, no generic mapping, no offset
  adjustment. An implementation MUST NOT scan ApplicationData for
  CREATOR OWNER or CREATOR GROUP SIDs.
- Generic rights in every ACE that applies to the object (both explicit
  and inherited) are mapped to object-specific rights via the object
  type's GenericMapping, so no generic bits persist on an ACE the access
  check reads. An inherit-only ACE keeps its generic rights and
  placeholders as written, for the objects further down to resolve.
  Generic rights appearing inside ApplicationData are not mapped.
- The INHERITED_ACE flag is set on all ACEs that came from the parent.
- If any ACE was inherited from the parent, SE_DACL_AUTO_INHERITED is
  set on the new SD's control flags; if the DACL came from the token's
  default DACL instead, SE_DACL_DEFAULTED is set. The equivalent applies
  to SE_SACL_AUTO_INHERITED for the SACL.

An ACE of an unrecognised type is carried to the child unchanged apart
from its AceFlags byte (§5.4). Its mask is not mapped and its SID is not
substituted, because neither can be located within an opaque ACE.

### SACL

Computed identically to the DACL, substituting SACL for DACL throughout.
The token has no "default SACL" — if no creator SACL is supplied and the
parent has no inheritable SACL ACEs, the new object has no SACL.

## Eager evaluation

Inheritance is eager. The new object's SD is fully computed at creation
time. There is no lazy inheritance — the kernel MUST NOT walk up the
directory tree at access time to find inheritable ACEs.

A consequence of eager evaluation: modifying an inheritable ACE on a
parent object does not automatically update existing children. Existing
children retain the SD they were created with. Propagating the change to
descendants is an explicit operation, done by userspace, as below.

## Re-propagation

Re-propagation brings existing descendants up to date with their parent.
The kernel has no primitive for it: the program that changed the parent
walks the tree. Every program that does MUST give the same result, which
is this.

For one child and one ACL (the DACL, the SACL, or each in turn):

1. If the child protects that ACL (SE_DACL_PROTECTED or
   SE_SACL_PROTECTED), it is left exactly as it is.
2. Otherwise, the child's ACEs with INHERITED_ACE set are removed, its
   other ACEs are kept in their order, and the ACEs the parent's ACL gives
   it (above, resolved against the child's own owner and group, through
   the child's object type's GenericMapping) are appended after them. The
   ACL is marked SE_DACL_AUTO_INHERITED or SE_SACL_AUTO_INHERITED.
3. A parent without that ACL gives nothing, so only the inherited ACEs are
   removed. A child without that ACL gets one only if something is
   inherited into it.

The owner, group and the ACL not being re-propagated are unchanged. A
child is re-propagated from its parent as the parent is after its own
re-propagation, so a walk goes parents first. A protected child still
passes its own ACEs on: its descendants are re-propagated from it as it
is. A failure on one child does not stop the walk: the rest are
re-propagated and the failures reported.

libpeios implements this as `reinherit_with` (`peios_sd_reinherit_ex`).
