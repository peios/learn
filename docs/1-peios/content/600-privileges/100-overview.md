---
title: Privileges
type: concept
description: A privilege is a system-wide right carried on a token. Privileges sit alongside identity but are orthogonal to it — they gate specific operations regardless of who you are. This page covers what a privilege is, where they come from, and how they interact with the access check.
related:
  - peios/privileges/lifecycle
  - peios/privileges/intent-gated
  - peios/privileges/categories
  - peios/tokens/overview
  - peios/access-decisions/overview
---

A **privilege** is a system-wide right carried on a token. Where group membership decides "is this principal allowed to do things by virtue of who they are", a privilege decides "is this principal allowed to do *this specific operation*, regardless of who they are". Loading a kernel module, taking ownership of an object, changing the system clock, reading any file for backup — each is gated by a specific privilege, granted to principals whose role legitimately requires it.

Privileges sit on the token alongside the user SID and group list, but they are evaluated separately from identity. The access check reads a privilege bitmask, not a group membership. An ACE in a DACL cannot match a privilege the way it matches a SID. Privileges are their own axis of authority.

## What a privilege is

A privilege has three properties:

- A **name** — a specific string like `SeBackupPrivilege`. Most privilege names start with `Se` and end with `Privilege`; the convention is shared across the catalog.
- A **LUID** — a 64-bit identifier the kernel uses internally to reference the privilege. Privileges occupy specific bit positions in the 64-bit privilege bitmask on every token.
- A **specific operation it gates** — every privilege has a defined effect: which kernel operation, which AccessCheck pathway, which capability it controls.

Privileges are global. The catalog is fixed at build time; there is no API to define new privileges at runtime. A token either has a specific named privilege or does not. The number of distinct privileges in v0.20 is in the low tens.

## Where privileges come from

A token's privileges are decided at one moment: when the token is minted. That happens either:

- During boot, when the kernel constructs the SYSTEM token (which holds **every** privilege).
- When authd authenticates a principal and constructs their token, applying the privilege policy authd has loaded for the principal's role.
- When peinit mints a token for a service it is launching.
- When existing code creates a derived token via DuplicateToken (preserves privileges) or FilterToken (removes the listed privileges).

There is no path to *gain* a privilege after a token is minted. AdjustPrivileges can enable or disable a privilege the token already has, and can permanently remove a privilege, but cannot add one that was not present at creation. A token's privilege bitmask is at most what was put there at the start.

The privilege policy authd consults — which principals get which privileges — is held in the directory (or in the registry on a standalone machine). authd reads the policy at authentication time. From the kernel's point of view, the policy is invisible: it only ever sees the resulting token. authd is the integration point between "who is this user according to the directory" and "what privileges does their token carry".

## The four states of a privilege

At any moment, each privilege on a token is in one of four states:

| State | Meaning |
|---|---|
| **Absent** | The privilege is not on this token. The token's bitmask has the relevant bit clear in both the "present" and "enabled" fields. |
| **Present, disabled** | The privilege is on the token but not currently in effect. The access check ignores it. The token may enable it via AdjustPrivileges. |
| **Present, enabled** | The privilege is on the token and is in effect. AccessCheck will use it where applicable. |
| **Used** | The privilege has been exercised at least once. A sticky audit bit; never cleared. |

The states layer rather than replace. A privilege that has been used remains in whatever present/enabled state it was in; the "used" bit is recorded alongside, for auditing.

Disabling rather than removing is the common pattern. A service runs most of the time with sensitive privileges *present but disabled*, enabling them only at the moment they need to be exercised and disabling them afterwards. The reason: the access check ignores disabled privileges entirely, so the service is not at risk of accidentally exercising a privilege it had not meant to use.

The full lifecycle — transitions, AdjustPrivileges semantics, FilterToken-based permanent removal, the "used" bit — lives in [Privilege lifecycle](~peios/privileges/lifecycle).

## Privileges in the access check

Privileges interact with the access check in three ways:

### Direct gating

Some operations are gated directly by a privilege held at the moment of the call, with no DACL involved.

- `SeLoadDriverPrivilege` gates kernel module loads. No DACL applies; either you have the privilege enabled or the load fails.
- `SeSystemtimePrivilege` gates `settimeofday`.
- `SeCreateTokenPrivilege` gates `kacs_create_token`.

These privileges are direct. The check is "is this privilege enabled on the calling token", full stop.

### Influencing the DACL walk

A handful of privileges, when enabled, change what the DACL walk would conclude. These are the **AccessCheck-influencing** privileges, covered in [Privilege categories](~peios/privileges/categories):

- `SeSecurityPrivilege` grants `ACCESS_SYSTEM_SECURITY` (SACL read/write) regardless of the DACL.
- `SeTakeOwnershipPrivilege` grants `WRITE_OWNER` on any object.
- `SeBackupPrivilege` grants read access to any object (with the backup intent flag set).
- `SeRestorePrivilege` grants write access and ownership-change rights (with the restore intent flag).
- `SeRelabelPrivilege` permits raising an object's integrity label above the caller's own.

These privileges produce grants that no DACL would have produced. They are recorded in the access check's audit state so audit events can record "this access was granted by privilege X" rather than appearing as a DACL grant.

### Intent-gated privileges

Two of the influencing privileges — `SeBackupPrivilege` and `SeRestorePrivilege` — only fire when the caller passes a specific **intent flag** to AccessCheck. Without the flag, the privileges might as well not be present. This avoids accidentally exercising a backup privilege when doing a normal read.

The intent model is covered in [Intent-gated privileges](~peios/privileges/intent-gated).

## Privileges vs groups

The split between privileges and group membership is one of the deliberate design decisions of the model:

| | Group membership | Privileges |
|---|---|---|
| What it grants | Whatever ACEs name the group | A specific operation, named directly |
| Where it lives | The token's `groups` field | The token's privilege bitmask |
| How it is matched | ACE SID matches token group SID | Privilege code is consulted in specific kernel paths |
| Who manages it | The directory administrator (group membership) and per-object administrator (DACL entries) | The directory administrator (privilege policy in authd) |
| Granularity | Group-wide; the same group across all objects | Per-operation; the same privilege across all objects |

A user can be in a group and still not hold a privilege the rest of the group has, or vice versa, because the two are managed independently. authd's privilege policy and the directory's group memberships are separate inputs.

The classical example: BUILTIN\Administrators is a group, and being in it grants whatever ACEs in DACLs name the group. But the dangerous privileges — SeLoadDriver, SeBackup, SeRestore — are not automatic by group membership. authd's policy specifies which administrators get which privileges. A "junior administrator" account in BUILTIN\Administrators might lack SeLoadDriver while a "senior administrator" account holds it.

This separation matters because the failure modes are different. A misconfigured DACL grants too much group access; a misconfigured privilege policy grants too much system-level authority. Both are fixable in different places.

## Privileges and inheritance

Group memberships propagate down through identity (you remain in your groups until your token changes). Privileges work the same way: a token holds the privileges authd minted it with, and the bitmask is preserved through fork, exec, and inheritance into child processes — exactly like the rest of the token.

Privileges do **not** propagate to ACEs or objects. There is no "privilege-bearing" ACE; no SD can be annotated with a privilege requirement; no object can demand "you must have SeBackup to open me". The privilege model and the SD model do not overlap that way. They interact only through the access check, when an influencing privilege is enabled on the caller's token and the AccessCheck pipeline decides whether to use it.

## Where to start

If you want the lifecycle in detail — the present/enabled/used/removed transitions, what AdjustPrivileges actually does, how FilterToken removes a privilege permanently — read [Privilege lifecycle](~peios/privileges/lifecycle).

If you want to understand intent-gated privileges — why SeBackup and SeRestore require an explicit flag and how that flag is passed — read [Intent-gated privileges](~peios/privileges/intent-gated).

If you want to see how privileges are organised — the kernel-standalone group, the AccessCheck-influencing group, the application-level group, the reserved group — read [Privilege categories](~peios/privileges/categories).

If you want the full catalog of named privileges with their numeric LUIDs and one-line descriptions, that is in the [Constants and catalogs](~peios/constants-and-catalogs/overview) reference.
