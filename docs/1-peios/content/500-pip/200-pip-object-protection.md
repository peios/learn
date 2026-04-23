---
title: How PIP Protects Objects
type: concept
description: How trust label ACEs in the SACL prevent access to critical files from processes without sufficient PIP trust.
---

PIP protects more than running processes. Critical files — binaries, private keys, system configuration — can carry **trust label ACEs** that prevent access from processes without sufficient PIP trust.

## Trust label ACEs

A trust label ACE is a special ACE placed in an object's SACL. It encodes a minimum PIP type and trust level required to access the object, along with which categories of access are restricted.

When AccessCheck encounters a trust label ACE, it compares the calling process's PIP level against the label. If the process does not dominate the trust label, the restricted access categories are denied — before the DACL is ever consulted.

## Per-category restrictions

Unlike process protection (which is all-or-nothing), object protection is **per-category**. A trust label ACE specifies which operations require PIP dominance:

| Category | What it restricts |
|---|---|
| **Read** | Reading the object's contents |
| **Write** | Modifying the object's contents |
| **Execute** | Executing the object |

A trust label might restrict write and execute but allow read — permitting anyone to inspect the file while preventing modification or execution by non-dominant processes. Or it might restrict all three, making the object completely inaccessible to processes that don't meet the PIP threshold.

## Privileges do not bypass trust labels

Just as with process protection, privileges cannot compensate for missing PIP dominance on trust-labeled objects. A process with `SeBackupPrivilege` that would normally bypass the DACL for read access is still blocked by a trust label that restricts reads. A process with `SeTakeOwnershipPrivilege` cannot claim ownership of a trust-labeled object without PIP dominance.

The trust label is evaluated before privilege overrides take effect. PIP is the first gate — if it denies, nothing else matters.

## Why both process and object protection are needed

Process protection and object protection address different attack surfaces:

- **Process protection** prevents a non-dominant process from reading authd's memory, debugging it, or killing it while it runs
- **Object protection** prevents a non-dominant process from replacing authd's binary on disk, modifying its configuration, or reading its private key files

Without object protection, an attacker who cannot touch the running process could replace its binary and wait for a restart. Without process protection, an attacker who cannot touch the files could read secrets directly from memory. Both surfaces must be covered.

## What carries trust labels

Trust labels are typically placed on:

- **Binaries** for PIP-protected services — preventing modification or replacement
- **Private key files** — preventing read access from non-dominant processes
- **Critical configuration** — preventing tampering with security-relevant settings
- **Signing material** — the kernel module signing key, service signing keys

These labels are part of the system's initial security policy, set during installation and protected from modification by the labels themselves.
