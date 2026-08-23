---
title: Overview
description: KACS is the security core of Peios — an LSM inside PKM providing identity-based access control — and how it relates to MS-DTYP.
---

The Kernel Access Control System is the security core of Peios: an LSM
within PKM providing identity-based access control in the Linux
kernel. It is the sole identity-based authorization mechanism for
managed objects. Every identity-based decision — a file open, a
registry read, an IPC connection, a signal, a token operation — passes
through one evaluation function, AccessCheck.

This chapter covers tokens (§3.2), the Process Security Block (§3.3),
privileges (§3.4), impersonation (§3.5), binary signature verification
(§3.6), Process Integrity Protection (§3.7), the AccessCheck algorithm
in full (§3.8), file enforcement (§3.9), and how Peios identity is
projected onto the Linux credential model (§3.10).

Two bodies of material that KACS owns conceptually live elsewhere in
the documentation. The binary structures — SIDs, security descriptors,
ACLs, ACEs, access masks, conditional ACE bytecode — are specified in
PCDS, because userspace tooling constructs and interprets them and has
to agree with the kernel byte for byte. The signing format a third
party would use to sign a binary with a PIP level is specified in
PSPK; this chapter describes only the verification side. What remains
here is the kernel's own behaviour: how it holds identity, and how it
decides.

## Terminology

A **token** is a per-thread identity object held in the kernel's
credential structure, carrying a user SID, group SIDs, a privilege
bitmask, an integrity level, an impersonation level, and metadata.
Identity fields — SIDs, type, integrity level — are immutable; policy
fields — enabled privileges, enabled groups, default owner, group and
DACL — are atomically adjustable. Every thread has a token, and there
is no such thing as a null token.

A **primary token** defines a process's baseline identity and is
inherited on fork, reached through `task->real_cred`. An
**impersonation token** temporarily overrides it for access decisions
on one thread only, reached through `task->cred`.

A **LogonSession** is a kernel object representing one authentication
event: a session ID, a logon type, a user SID, an authentication
package, a logon time, and a logon SID. Tokens reference their session
by ID.

A **privilege** is a system-wide right carried on a token. Some
influence AccessCheck; others gate a standalone operation.

An **impersonation level** controls how far an identity can travel:
Anonymous, Identification, Impersonation, or Delegation.

An **integrity level** is a vertical trust classification on tokens
and objects. Numerically it is the mandatory label SID's single
sub-authority compared as an unsigned integer, so any `S-1-16-<n>`
with exactly one sub-authority is valid. In practice five standard
levels form a strict total order — Untrusted (0), Low (4096), Medium
(8192), High (12288), System (16384) — and non-standard values such as
`S-1-16-8448` appear only in SDs authored for Windows interop.
**Mandatory Integrity Control** is the constraint evaluated before the
DACL, blocking write access, and optionally read and execute, when the
caller's level is below the object's label.

**Process Integrity Protection** is a two-dimensional trust model —
type against trust level — protecting processes and objects from
insufficiently trusted callers. Unlike MIC, it revokes rights that a
privilege would otherwise have granted.

The **Process Security Block** is a per-process structure carrying PIP
identity, process mitigations, and process restrictions. It is never
affected by impersonation, which is the point of keeping it separate
from the token.

**FACS**, the File Access Control Shim, is the part of KACS that
replaces Linux DAC with security-descriptor evaluation on files. It
enforces the handle model: AccessCheck runs at open time and the
granted mask is cached on the file description, with later operations
checked against the cached mask.

An **object type** is the category of a protected resource. Each
defines a GenericMapping table translating generic rights into
object-specific ones.

The **TCB** — the components whose correct behaviour is necessary for
system security — is the Linux kernel, PKM, and the core trusted
userspace daemons: peinit, authd, and loregd.

## Relationship to MS-DTYP

KACS is not a port of another system's security model. Tokens,
security descriptors, AccessCheck, structured SIDs, and per-thread
impersonation were chosen because they solve what Peios needs solved:
coherent identity, rich per-object access control, scoped delegation,
and integrated audit.

Those same primitives are the ones Active Directory uses, and Peios is
built to join AD domains as a first-class member — exchanging security
data with domain controllers, authenticating through Kerberos, and
enforcing policy distributed by Group Policy. That imposes binary
format compatibility, which PCDS specifies: an SD written by a Windows
domain controller and replicated through Samba is evaluated by KACS
without translation.

Format compatibility does not imply evaluator compatibility in every
corner. Given the same token, descriptor, and desired mask, KACS
generally reaches the same decision MS-DTYP describes, which is what
makes policy authored in an AD environment behave predictably here.
Where it deliberately does not, §3.B records every departure and why.
