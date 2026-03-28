---
title: Frequently Asked Questions
type: reference
order: 2
description: Common questions about the Peios security model from newcomers.
---

## General

### What is Peios?

Peios is an operating system designed for secure, manageable infrastructure. It has its own security model — KACS (Kernel Access Control Subsystem) — built into the kernel, providing a unified approach to identity, access control, integrity, and auditing.

### Why a new security model? What's wrong with Linux permissions?

Traditional Linux permissions (owner/group/other with read/write/execute) are coarse and limited. There's no way to say "allow user A read access and user B write access to the same file" without involving ACLs that exist outside the core model. Capabilities, SELinux, AppArmor, and seccomp are bolted on as separate systems with separate vocabularies.

Peios replaces all of this with one model. Security descriptors, tokens, and AccessCheck handle every access decision through a single pipeline. One set of concepts works everywhere.

### Is this based on Windows security?

The security model is heavily inspired by the Windows security architecture — tokens, SIDs, security descriptors, DACLs, and AccessCheck follow the same design principles and are wire-compatible where applicable. However, Peios is its own operating system, not a Windows reimplementation.

### Do I need to understand all of this to use Peios?

No. For basic use, Peios works like any other operating system — you log in, run programs, and access files. The security model is transparent until you need to understand why something was allowed or denied. Start with [Understanding Identity](~identity/understanding-identity) and [Understanding Access Control](~access-control/understanding-access-control) for the foundations, and explore deeper topics as needed.

## Coming from Linux

### Can I still use Linux applications?

Yes. Peios provides a compatibility layer that projects KACS tokens into traditional Linux credentials (UIDs, GIDs, capabilities). Most Linux applications work without modification. See [Understanding Linux Compatibility](~linux-compat/understanding-linux-compatibility).

### What happened to root?

Root (UID 0) has no security meaning on Peios. The superuser concept is replaced by tokens with specific privileges. A process with SeBackupPrivilege can read any file — but only when it explicitly declares backup intent. A process with SeShutdownPrivilege can shut down the machine — but can't read your files. See [How Peios Eliminates Root](~linux-compat/how-peios-eliminates-root).

### What about sudo?

Peios uses linked token pairs instead of sudo. When an administrative user logs in, they receive a filtered token (standard privileges) and an elevated token (full privileges). Elevation switches to the elevated token through a trusted credential path — no password prompt that can be spoofed by a malicious program. See [How Linked Tokens and Elevation Work](~identity/linked-tokens-and-elevation).

### What happens to setuid binaries?

The setuid bit is reinterpreted under KACS. Rather than switching to UID 0, the kernel applies credential projection rules. The behaviour is safe by default and documented in [Understanding Linux Compatibility](~linux-compat/understanding-linux-compatibility).

### Do Linux capabilities still work?

Peios provides a capability switchboard that maps Linux capabilities to the appropriate Peios privilege checks. Applications that check for `CAP_DAC_OVERRIDE` or `CAP_NET_BIND_SERVICE` get the expected behaviour, routed through the KACS privilege system. See [Understanding Linux Compatibility](~linux-compat/understanding-linux-compatibility).

## Security model

### What's the difference between MIC and PIP?

**MIC (Mandatory Integrity Control)** enforces trust tiers — a Medium-integrity process can't write to High-integrity objects. It can be overridden by specific privileges (like SeRelabelPrivilege).

**PIP (Process Integrity Protection)** protects critical processes from interference using two dimensions (type and trust level). Unlike MIC, **privileges cannot bypass PIP**. This makes PIP the strongest protection layer. See [Understanding MIC](~integrity/understanding-mic) and [Understanding PIP](~pip/understanding-pip).

### What's the difference between privileges and access rights?

**Access rights** are on the object — the DACL says "user X can read this file." **Privileges** are on the token — they grant system-wide capabilities like "back up any file" or "shut down the machine." Some privileges interact with AccessCheck, but most gate entirely separate operations. See [Understanding Privileges](~privileges/understanding-privileges).

### What's a security descriptor?

It's the complete security policy on an object: who owns it (owner), who can access it (DACL), and what gets audited (SACL). Every secured object — files, registry keys, processes, services — has one. See [How Security Descriptors Work](~access-control/how-security-descriptors-work).

### What happens when access is denied?

The kernel returns an access denial to the calling process. To understand why, you need to trace through the evaluation pipeline: Was it MIC? PIP? A deny ACE in the DACL? Confinement? The [Troubleshooting Access Denied Errors](~troubleshooting/access-denied-errors) page walks through the diagnostic process.

### Can I audit who accessed what?

Yes. The SACL on an object defines audit rules — which principals and which access types generate audit events. Peios supports per-object auditing, per-token audit policy, privilege-use auditing, and continuous auditing. See [Understanding Auditing](~auditing/understanding-auditing).

## Architecture

### Is the security model in userspace or the kernel?

The kernel. KACS is a kernel module that implements tokens, security descriptors, AccessCheck, MIC, PIP, confinement, auditing, and privilege enforcement. Access decisions are evaluated synchronously in the requesting thread's context — there's no userspace policy daemon in the access path.

### Why one model instead of layered tools?

Layered tools (SELinux + AppArmor + capabilities + seccomp + namespaces) each have their own configuration language, policy format, and failure modes. When something goes wrong, you have to figure out which layer blocked the access.

Peios has one pipeline. When access is denied, the audit event tells you exactly which step — MIC, PIP, DACL, confinement, or CAP — made the decision. One vocabulary, one set of diagnostic tools, one answer.

### How does this scale to large deployments?

Central Access Policy (CAP) provides organisation-wide access rules that apply based on resource attributes — without modifying individual object DACLs. Combined with group-based access control and conditional ACEs using claims, Peios scales the same way enterprise Windows deployments do. See [Understanding Central Access Policy](~central-access-policy/understanding-central-access-policy).
