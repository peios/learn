---
title: Understanding Privileges on Peios
type: concept
order: 10
---

A **privilege** is a system-wide right carried on a token. Privileges are separate from access rights — access rights live on the object (in the security descriptor), while privileges live on the caller (in the token).

Privileges grant the ability to do things that no ACE can express. Shutting down the machine, taking ownership of any object, loading a kernel module, changing the system clock — these are operations that are not tied to a specific object, or that need to override normal access control for a specific purpose.

## Privileges vs access rights

| | Access rights | Privileges |
|---|---|---|
| **Where they live** | On the object, in the DACL | On the caller, in the token |
| **Who controls them** | The object's owner | System policy (assigned at token creation) |
| **What they govern** | Access to a specific object | System-wide operations or AccessCheck overrides |

Both are checked during an access decision. A process might need a specific access right on the object **and** a specific privilege on its token. For example, reading the SACL requires `ACCESS_SYSTEM_SECURITY` (an access right requested in the mask) and `SeSecurityPrivilege` (a privilege on the token). Neither alone is sufficient.

## Assigned by policy

Privileges are determined at token creation time. When a user authenticates, the authentication service resolves which privileges the user is entitled to based on system policy and group memberships in the directory. These privileges are placed on the token.

A process cannot grant itself a privilege it was not assigned. It can enable, disable, or permanently remove privileges from its token — but it cannot add new ones. The set of privileges on a token can only shrink, never grow.

## The privilege lifecycle

Every privilege on a token has a state:

| State | Meaning |
|---|---|
| **Present, disabled** | The token holds this privilege but it is not active. Most privileges start in this state. |
| **Present, enabled** | The privilege is active and will be considered during access decisions and operation gates. |
| **Removed** | The privilege has been permanently removed from the token. It cannot be re-enabled. |

The disabled-by-default design is deliberate. A privilege like `SeBackupPrivilege` grants broad read access that bypasses the DACL — it would be dangerous to have it active at all times. The process must explicitly enable it before use, signaling intent. This limits the window during which a compromised process can exploit a powerful privilege.

Some privileges are exceptions — `SeChangeNotifyPrivilege` (the right to traverse directories without being checked for traverse access) is typically enabled by default because virtually every operation requires it.

## Key privileges

A few of the most important privileges:

| Privilege | What it does |
|---|---|
| `SeBackupPrivilege` | Grants read access to any object regardless of the DACL (when backup intent is declared) |
| `SeRestorePrivilege` | Grants write access to any object regardless of the DACL (when restore intent is declared) |
| `SeTakeOwnershipPrivilege` | Grants the ability to claim ownership of any object |
| `SeSecurityPrivilege` | Grants the ability to read and modify SACLs (audit rules and integrity labels) |
| `SeDebugPrivilege` | Grants the ability to debug any process (subject to PIP) |
| `SeShutdownPrivilege` | Grants the ability to shut down or restart the machine |
| `SeAssignPrimaryTokenPrivilege` | Grants the ability to install a token on a process |
| `SeImpersonatePrivilege` | Grants the ability to impersonate a client |

The complete catalog is available in the privilege reference.

## Intent-gated privileges

Some privileges are only evaluated when the caller explicitly declares intent. `SeBackupPrivilege` and `SeRestorePrivilege` are the primary examples — they only take effect when the caller passes a backup or restore intent flag with the access request.

This prevents a process with backup privilege from accidentally bypassing the DACL during normal operations. The privilege is only active when the process says "I am performing a backup." Normal file operations go through the DACL as usual, even if the token holds the privilege.
