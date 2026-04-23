---
title: Understanding Identity on Peios
type: concept
description: Every process runs with a token — a structured bundle of security information the kernel evaluates on every access decision.
related:
  - peios/identity/what-are-sids
  - peios/identity/how-tokens-work
  - peios/access-control/understanding-access-control
---

Every process on Peios runs with an **identity** — a complete picture of who the process is and what it is allowed to do. This identity is carried in a kernel object called a **token**.

## What is a token?

A token is a structured bundle of security information that the kernel attaches to every thread. When a process opens a file, connects to a service, or performs any secured operation, the kernel inspects the thread's token to decide whether the operation is allowed.

A token contains:

| Component | What it represents |
|---|---|
| **User SID** | The unique identifier of the user or service this process is acting as |
| **Group SIDs** | The groups the user belongs to — each identified by its own unique SID |
| **Privileges** | System-wide rights the token carries, such as the ability to shut down the machine or take ownership of an object |
| **Integrity level** | A trust tier (from Untrusted through System) that sets a floor on what the process can modify |

There are additional components — impersonation level, logon session, token source — covered in their own pages. The important thing is that all of this travels together as a single object. There is no separate system for "who you are" and "what you can do." The token is both.

## Security principals

A **security principal** is anything that can have an identity: a user, a group, a service, or a machine. Each principal is identified by a globally unique **Security Identifier (SID)** — a structured value that never changes and is never reused.

Principals exist in a directory (such as Active Directory). When a user authenticates, the system looks up their principal record, resolves their group memberships and privilege assignments, and builds a token. The token is a **runtime snapshot** of that principal's identity and policy at the moment of authentication.

## How identity flows through the system

Tokens are created and inherited through a simple chain:

1. **The kernel boots.** It creates the initial SYSTEM token — the highest-privilege identity on the machine — and assigns it to the init process.

2. **The init process starts services.** Each service receives a purpose-built token with its own identity, group memberships, and privileges appropriate to its role.

3. **Users authenticate.** When a user logs in, the authentication service verifies their credentials, resolves their identity from the directory, and creates a token. Processes launched in that user's session inherit this token.

4. **Child processes inherit their parent's token.** When a process creates a child, the child receives a copy of the parent's token. The child runs with the same identity unless the system explicitly assigns a different one.

At every step, the token is the single source of truth. The kernel does not consult external services or databases when making access decisions — it evaluates the token that the thread already carries.

## One model, one vocabulary

Every access decision on Peios flows through the same path: the kernel takes the thread's token and evaluates it against the security policy on the object being accessed. This is true whether the object is a file, a registry key, a network socket, or an IPC endpoint.

This means there is one set of concepts to learn. Understanding how tokens, SIDs, and security descriptors work gives you the tools to reason about access control anywhere in the system.