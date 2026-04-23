---
title: How Peios Eliminates Root
type: concept
description: Why UID 0 carries no security authority on Peios and how specific privileges replace root's monolithic powers.
---

There is no root user on Peios. UID 0 exists in the Linux credential system — the kernel ABI requires it — but it carries no security authority. No access decision checks for UID 0. No special case grants UID 0 additional rights. The traditional "root can do anything" property does not exist.

## Why UID 0 has no meaning

On traditional Linux, UID 0 is the ultimate authority — the kernel grants it bypass over virtually all access checks. This makes root the single most valuable target for an attacker and the single largest source of accidental damage.

On Peios, all access decisions flow through AccessCheck, which evaluates **tokens** against **security descriptors**. AccessCheck does not know what a UID is. It matches SIDs, walks DACLs, checks privileges, evaluates integrity levels. UID 0 does not appear in any security descriptor, does not match any ACE, and does not grant any privilege.

A process with UID 0 and a process with UID 65534, holding the same token, have **identical authority**. They can access exactly the same files, send signals to exactly the same processes, and perform exactly the same operations.

## How the system boots without root

Traditional Linux requires root (UID 0) to boot — PID 1 runs as root and starts services as root before they drop privileges.

Peios replaces this with the **SYSTEM token**:

1. The kernel creates the SYSTEM token (`S-1-5-18`) at initialization — the highest-privilege identity on the machine, with all privileges enabled and System integrity level
2. PID 1 (the init process) inherits the SYSTEM token
3. The init process creates purpose-built tokens for each service — with the right identity, groups, and only the privileges needed
4. Services start with their correct tokens from the beginning — no privilege dropping required

The SYSTEM token's projected UID happens to be 0 (matching the Linux convention for the init process). But this is a projection artifact, not a security property. The init process has full authority because it holds the SYSTEM token with all privileges — not because its UID is 0.

## What replaced root's powers

Every operation that traditionally required root maps to a specific mechanism on Peios:

| Traditional root power | Peios equivalent |
|---|---|
| Bypass all file permissions | `SeBackupPrivilege` / `SeRestorePrivilege` (intent-gated) |
| Kill any process | `PROCESS_TERMINATE` right on the target's SD (+ PIP dominance for protected processes) |
| Change file ownership | `SeTakeOwnershipPrivilege` |
| Load kernel modules | `SeLoadDriverPrivilege` |
| Bind privileged ports | `SeBindPrivilegedPortPrivilege` |
| Change system time | `SeSystemtimePrivilege` |
| Mount filesystems | `SeTcbPrivilege` |
| Modify audit rules | `SeSecurityPrivilege` |

Each power is a separate, grantable, revocable privilege — not a single monolithic identity. A service that needs to bind port 53 gets `SeBindPrivilegedPortPrivilege` and nothing else. It cannot load kernel modules, change file ownership, or kill protected processes. The blast radius of compromise is bounded by the specific privileges assigned.

## No single point of total compromise

On traditional Linux, compromising any root process gives the attacker everything. On Peios, there is no single identity that grants unrestricted access:

- **SYSTEM** has all privileges but is still subject to PIP. A SYSTEM process without PIP dominance cannot debug an Isolated process.
- **Administrators** have broad access but operate at High integrity, not System. They cannot modify System-integrity objects without explicit elevation.
- **Privileges are narrow and revocable.** A service can remove privileges it no longer needs, permanently.

The closest equivalent to root compromise is compromising the kernel itself — which is outside the scope of any access control model. Within the access control boundary, no single principal has unconditional access to everything.
