---
title: Identity in Peios
type: concept
description: How Peios identifies who is acting — principals named by SIDs, carried by tokens, anchored in logon sessions, and checked at every access decision.
related:
  - peios/identity/sids
  - peios/tokens/overview
  - peios/logon-sessions/overview
---

Every action on a running Peios system happens on behalf of a **principal** — a user, a service, a machine, or a well-known system actor. Identity is the unit of policy: every access decision starts with "who is asking?", and the kernel answers that question the same way for files, registry keys, processes, sockets, and tokens themselves.

## The shape of an identity

Identity in Peios has four layers, each with a clear job.

| Layer | Role |
|---|---|
| **Principal** | The thing being identified — a user account, a group, a service, a machine. |
| **SID** (Security Identifier) | The unique name for a principal. SIDs are hierarchical strings like `S-1-5-21-...-1001`. |
| **Token** | The runtime object that carries an identity into the kernel. Every thread has one. |
| **Logon session** | The authentication event a token belongs to. Sessions link tokens back to "who logged in, when, and how". |

These four words appear throughout the Peios documentation, and they are not interchangeable. A principal is the long-lived thing in the directory; a SID is its name; a token is its instance for one run; a session is what produced that token.

## How an identity gets into the kernel

```mermaid
flowchart LR
    A["Principal"] -->|"identity asserted by"| B["Principal source"]
    B -->|"verified identity"| C["authd"]
    C -->|creates| D["Logon session"]
    C -->|mints| E["Token"]
    E -->|installed on| F["Process"]
    F -->|"presents at every syscall"| G["Access decision"]
```

When a user signs in, authentication happens in three steps:

1. A **principal source** verifies the credential and asserts who the principal is — the local principal source for this machine's own accounts, or a directory-backed source on a domain-joined machine.
2. **authd**, the authentication authority, creates a **logon session**: a kernel object that records the authentication event (who, how, when).
3. authd mints a **token** carrying the user's SID, group SIDs, integrity level, privileges, and a reference to the session. The token becomes the user's runtime identity — and its privileges and integrity level come from this machine's policy for the principal, not from the source that identified them.

The client that requested the logon — `login` on a console, for example — installs the token on the session's first process, and every child process inherits it across fork. Threads that need to act on behalf of someone else (for example, a service handling a user request) can temporarily swap in an **impersonation token** while keeping their original — see [Impersonation](~peios/impersonation/overview).

The token is the authoritative carrier. Any other identity values a process can observe — including the numeric IDs that surface through standard Linux system calls — are derived from the token, never the other way around. See [Linux compatibility](~peios/linux-compatibility/overview) for how that projection works.

## Identity vs authorisation

An identity by itself grants nothing. A token says who a thread is; the Kernel Access Control Subsystem (KACS) decides what it can do, by comparing the token against each object's security descriptor. The same token will see different rights on different objects, and the same object will grant different rights to different tokens.

The rest of the security documentation is organised around this separation:

- **Identity says "who".** This topic, plus [Tokens](~peios/tokens/overview) and [Logon sessions](~peios/logon-sessions/overview).
- **Authorisation says "what".** [Security descriptors](~peios/security-descriptors/overview) and [Access decisions](~peios/access-decisions/overview).

If a request fails unexpectedly, you almost always need to look at both sides: which identity made the request, and which access rule rejected it. Pages in both halves cross-link where the two meet.

## What identity does not include

A few things often get bundled with identity that are kept deliberately separate in Peios:

- **Privileges** are not identity. A token carries a set of privileges, but a privilege gates a specific operation (loading a driver, taking ownership of an object), independent of who you are. See [Privileges](~peios/privileges/overview).
- **Integrity level** is not identity. It is a separate axis on the token that controls write-up restrictions. Two users at different integrity levels are still two distinct identities; the integrity level is an additional constraint on top.
- **Process integrity (PIP)** is not identity at all. PIP is a property of the binary the process is running, set by the kernel from the binary's signature. It controls who can inspect or signal the process, independent of who the process is acting as. See [Process integrity protection](~peios/process-integrity-protection/overview).

These distinctions matter because they fail in different ways. An "access denied" caused by the integrity level looks like an identity problem but is not.

## Where to start

If you want to understand how SIDs are constructed, read [SIDs](~peios/identity/sids). For the catalog of built-in principals and their fixed SIDs, read [Well-known principals](~peios/identity/well-known-principals).

If you want the typed attributes a token carries beyond identity — the inputs to attribute-based access decisions — read [Claims on a token](~peios/identity/claims).

If you want the runtime mechanics — how a token is composed, how it survives fork and exec, and how it gets adjusted — read [Tokens](~peios/tokens/overview).

If you are debugging an unexpected denial, the [Inspecting tokens, sessions, and processes](~peios/inspecting/overview) topic shows how to see the identity attached to any running thread.
