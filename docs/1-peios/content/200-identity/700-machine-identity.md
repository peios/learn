---
title: Machine Identity in a Domain
type: concept
description: How machines are security principals with their own SIDs, domain accounts, and authentication credentials.
---

In a domain environment, every machine is a **security principal** — just like users, groups, and services. Each machine has its own SID, authenticates to the domain independently, and can appear in access control rules.

## Machine accounts

When a machine joins a domain, the domain controller creates a **machine account** for it. This account has:

- A unique **SID** within the domain (with its own RID, like any other principal)
- A **name** (typically the machine's hostname followed by `$`)
- **Credentials** that the machine uses to authenticate to the domain

The machine authenticates to the domain automatically — typically via Kerberos — without user involvement. This happens at boot and is maintained for the lifetime of the machine's domain membership.

## Why machines have identities

Machine identity enables security policies that would be impossible with user identity alone:

**Access by machine.** A security descriptor can grant access to a specific machine's account. "Only the backup server can read this share" is a policy expressed directly in terms of the machine's SID.

**Audit by machine.** When a network operation is logged, the audit trail records which machine it originated from — not just which user initiated it.

**Domain trust.** The machine's authenticated membership in the domain is what allows it to accept and validate Kerberos tickets from the domain controller. When a user logs into a domain-joined machine, the machine's identity is what establishes trust with the domain — the user's token is then built from information the domain controller provides.

## Machine identity and user identity

A machine's identity and a user's identity are separate. When a user logs into a machine, the processes in their session carry the **user's** token, not the machine's. The machine's identity establishes the trust relationship with the domain; the user's token governs what the user can do.

Some advanced policies can consider both the user and the machine together — for example, granting access only when a specific user is on a specific machine. This is covered in the claims and conditional access documentation.

## Standalone machines

A machine that is not joined to a domain does not have a domain machine account. It still has a local identity for its own services and system processes, but it cannot participate in domain-wide access policies or authenticate to domain resources.
