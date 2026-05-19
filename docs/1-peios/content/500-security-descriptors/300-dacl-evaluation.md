---
title: DACL evaluation
type: concept
description: A DACL is evaluated by walking its ACEs in order and applying first-writer-wins. Each bit in the requested access mask is decided by the first ACE that mentions it. This page covers the walk, the canonical ACE ordering, the NULL-vs-empty DACL distinction, and what MAXIMUM_ALLOWED does to the algorithm.
related:
  - peios/security-descriptors/overview
  - peios/security-descriptors/acls-and-aces
  - peios/security-descriptors/ownership
  - peios/access-decisions/overview
---

When the access check walks a DACL, it is answering one question, bit by bit: for each right the caller asked for, does this DACL grant or deny it? The mechanism is **first-writer-wins** — each bit is decided by the first ACE that mentions it, and once decided, no later ACE can override the decision. The walk is in the order ACEs appear in the DACL.

That rule is short. The consequences are not. The order of ACEs in a DACL is **semantically load-bearing**. A canonical order exists precisely so the rule produces the result you would expect. This page covers the walk, the canonical order, the special cases for null and empty DACLs, and what `MAXIMUM_ALLOWED` does to the algorithm.

## The walk, in one paragraph

The access check starts with two state variables: `decided` (bits whose grant/deny status is now fixed) and `granted` (bits that have been granted). Both start empty. It walks the DACL from first ACE to last. For each ACE: skip if the ACE does not match the caller (wrong SID, INHERIT_ONLY_ACE set, conditional expression evaluates UNKNOWN-or-FALSE for allow / FALSE for deny). For an `ACCESS_DENIED` ACE that matches: any of its mask bits that are not yet in `decided` are added to `decided` and *not* added to `granted` (they are denied). For an `ACCESS_ALLOWED` ACE that matches: any of its mask bits that are not yet in `decided` are added to both `decided` and `granted`. After the walk, the access check has its answer: the bits in `granted` are the rights this DACL would give.

That paragraph is the whole algorithm for an ordinary DACL. Everything else on this page is either a special case (null/empty DACL, MAXIMUM_ALLOWED) or a rule about how to *arrange* ACEs so the walk produces the right answer.

## First-writer-wins, illustrated

Suppose a DACL contains:

1. `ACCESS_ALLOWED Alice FILE_READ_DATA | FILE_WRITE_DATA`
2. `ACCESS_DENIED Alice FILE_WRITE_DATA`

Alice asks for `FILE_READ_DATA | FILE_WRITE_DATA`. The walk:

- ACE 1 matches Alice. `FILE_READ_DATA` and `FILE_WRITE_DATA` are not yet decided. Both are added to `decided` and to `granted`.
- ACE 2 matches Alice. `FILE_WRITE_DATA` is already decided. The ACE has no effect.

Result: Alice gets both rights. The deny in ACE 2 came too late.

Now suppose the DACL is in the other order:

1. `ACCESS_DENIED Alice FILE_WRITE_DATA`
2. `ACCESS_ALLOWED Alice FILE_READ_DATA | FILE_WRITE_DATA`

The walk:

- ACE 1 matches Alice. `FILE_WRITE_DATA` is not yet decided. It is added to `decided` but not to `granted` (denied).
- ACE 2 matches Alice. `FILE_READ_DATA` is not yet decided — it is added to both. `FILE_WRITE_DATA` is already decided. The ACE only takes effect on `FILE_READ_DATA`.

Result: Alice gets `FILE_READ_DATA` only. The deny in ACE 1 prevented the allow in ACE 2 from granting write.

The two DACLs contain exactly the same ACEs but produce different results. That is what is meant by "order matters".

## The canonical ACE order

Because ordering is load-bearing, Peios defines a **canonical order** that produces the result a reasonable reader would expect: explicit denies override explicit allows, and explicit ACEs override inherited ACEs.

| Position | ACE class |
|---|---|
| 1 | Explicit deny ACEs (set directly on the object). |
| 2 | Explicit allow ACEs. |
| 3 | Inherited deny ACEs. |
| 4 | Inherited allow ACEs. |

A DACL written in this order has the following properties:

- An explicit deny always overrides any allow (explicit or inherited) for the bits it covers.
- An explicit allow overrides any inherited rule.
- Inherited denies override inherited allows.

Tools that compose DACLs — a properties dialog, a system utility — are expected to maintain canonical order. The access check itself does not require it; the walk is the same regardless. But a DACL whose ACEs are out of canonical order produces results that may surprise the author. "I added a deny ACE and it had no effect" is almost always a canonical-order problem: the deny was placed after an allow that already decided the bits.

The four classes are distinguished by ACE type plus the `INHERITED_ACE` flag (0x10). Explicit ACEs have the flag clear; inherited ACEs have it set. The kernel sets the flag automatically when an ACE is created by inheritance.

## NULL DACL vs empty DACL

The two states look identical to a casual reader but mean opposite things.

| State | What the SD looks like | What the access check does |
|---|---|---|
| **NULL DACL** | `SE_DACL_PRESENT` flag is **not set** in the SD's control flags. | Grants every valid right. The walk is skipped. |
| **Empty DACL** | `SE_DACL_PRESENT` is set, the DACL exists, but contains zero ACEs. | Grants no rights (except owner implicit rights — see [Ownership](~peios/security-descriptors/ownership)). The walk happens, decides nothing, and the result is an empty `granted` mask. |

The NULL case is rare and dangerous. It is how you say "this object has no discretionary access control at all — anyone can do anything". You will see it on a few system objects where no DACL would be the right thing. You will never see it on a file you set permissions on.

The empty-DACL case is what you get when you explicitly remove every ACE from a DACL but keep the DACL itself. The intent is "no one has any rights to this object", and the access check honors it.

**Tools that print or parse SDs must distinguish the two.** Saying "the DACL is empty" without distinguishing between absent-DACL and zero-ACE-DACL is a recipe for misreading an object's policy.

## ACE flags that affect the walk

A few flags change whether or how an ACE participates:

| Flag | Effect on the walk |
|---|---|
| `INHERIT_ONLY_ACE` (0x08) | The ACE is **skipped** entirely during the DACL walk. It exists only to be copied to children at inheritance time. |
| `INHERITED_ACE` (0x10) | The ACE participates normally. The flag is used to identify inherited ACEs for canonical-ordering purposes, not to change evaluation. |
| `OBJECT_INHERIT_ACE`, `CONTAINER_INHERIT_ACE`, `NO_PROPAGATE_INHERIT_ACE` | No effect on the walk. These flags control inheritance to child objects; the walk on *this* object ignores them. |
| `SUCCESSFUL_ACCESS_ACE_FLAG`, `FAILED_ACCESS_ACE_FLAG` | These are audit/alarm flags and have no effect on access-control ACEs. |

The one to remember is `INHERIT_ONLY_ACE`. An ACE with that flag set is for inheritance purposes only and does not control access to the object it is on. This is sometimes the source of a confusing "but my ACE is right there in the DACL" — yes, it is, but it is inherit-only, so the walk skips it.

## MAXIMUM_ALLOWED: the "what could I get" mode

Normally the access check stops as soon as every bit in the requested mask is decided. If the caller asked for `FILE_READ_DATA | FILE_WRITE_DATA` and both bits are decided after three ACEs in a DACL of twenty, the walk stops — there is nothing more to learn.

When the caller sets `MAXIMUM_ALLOWED` (bit 25) in the requested mask, the access check changes mode. Instead of stopping when the requested bits are decided, it walks the *entire* DACL and accumulates every bit that any ACE would grant the caller. The returned `granted` mask is the union of all rights the caller could have gotten.

This is what tools use to display "you have read, write, and delete access to this file" without having to ask for each right separately. It is also what services use when they want to open an object with whatever rights they can get, deferring the actual privilege check to later operations.

Two specific rules about MAXIMUM_ALLOWED:

- The flag itself is **stripped** from the requested mask before the walk runs. The actual `decided`/`granted` arithmetic is done on the real bits.
- The granted mask is returned through the same channel as a normal access check; the caller learns what they got back.

`MAXIMUM_ALLOWED` does not affect first-writer-wins. A deny ACE that decides a bit still decides it. The full-walk mode just means the walk does not exit early.

## What the DACL walk does not decide

A handful of access decisions happen outside the DACL walk:

- **Owner implicit rights** are granted before the walk starts, based on the SD's owner field. Covered in [Ownership and implicit rights](~peios/security-descriptors/ownership).
- **Privilege-granted rights** (SeBackup, SeRestore, SeSecurity, SeTakeOwnership, SeRelabel) are decided before or after the walk, depending on the privilege. The DACL has no say.
- **MIC** (mandatory integrity) and **PIP** (process integrity protection) checks happen before the DACL walk for non-dominant callers, and can pre-decide write or other bits as denied.
- **Restricted token** and **confinement** intersections happen after the DACL walk and can narrow the result.
- **CAAP** (central access policies) evaluate alongside the DACL and can further restrict.
- **SACL audit** happens after the access decision, based on whatever the DACL walk + the other layers produced.

In other words, the DACL walk is one layer in a longer pipeline. It is the layer most people mean when they talk about "permissions", but it is not the whole story. The full pipeline lives in [Access decisions](~peios/access-decisions/overview).

## Practical tips

A handful of patterns that come up repeatedly:

- **When a deny ACE seems to have no effect**, check whether it appears after an allow ACE that already decided the bit. The fix is to move it earlier (or move the allow later) — i.e. canonicalise.
- **When an inherited ACE seems to override an explicit one**, check canonical order. Inherited ACEs should sit *after* explicit ones; if you find an inherited deny ahead of an explicit allow, the DACL is out of order.
- **When testing access**, query the full SD and walk it manually if the answer is surprising. Almost every "why doesn't this work" reduces to either a misordered DACL, a misplaced INHERIT_ONLY_ACE, or a missing flag.
- **When writing a DACL programmatically**, build it in canonical order from the start. Adding ACEs at the end and "sorting later" is fragile.
