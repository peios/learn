---
title: Understanding Logon Sessions
type: concept
description: What logon sessions are, the different logon types, and how the logon SID scopes access to a single session.
---

Every token on Peios is tied to a **logon session** — a kernel object that represents the authentication event that created it. A logon session answers the question: "how did this principal get here?"

## What a logon session contains

| Field | Description |
|---|---|
| **Session ID** | A unique identifier for this logon session |
| **Logon type** | How the principal authenticated (interactive, service, network, etc.) |
| **User SID** | The SID of the principal who authenticated |
| **Authentication package** | The authentication method used (Kerberos, password, etc.) |
| **Logon time** | When the authentication occurred |
| **Logon SID** | A unique SID assigned to this session (`S-1-5-5-{high}-{low}`) |

## Logon types

The logon type records how the principal arrived on the system. Different logon types carry different security implications.

| Type | Meaning |
|---|---|
| **Interactive** | A user authenticated directly — at the console or via a remote login |
| **Service** | A service started by the init process with a purpose-built token |
| **Network** | A principal authenticated over the network (e.g., connecting to a file share) |
| **Batch** | A scheduled task or job running on behalf of a principal |

The logon type is informational — it does not change what the token can do. But it provides context. A security policy might treat an interactive session differently from a network session, and audit logs record the logon type so administrators can understand how access occurred.

## The logon SID

Each logon session is assigned a unique SID in the `S-1-5-5` range. This **logon SID** is added to the token's group list, which means it can appear in access control rules.

This allows resources to be scoped to a specific session. For example, a temporary directory created for a user's interactive session can have an access rule that grants access only to that session's logon SID. Other sessions for the same user — a service running under their account, or a second interactive login — would have different logon SIDs and would not match.

## Tokens and sessions

Every token references exactly one logon session. Multiple tokens can share the same logon session — if a process creates child processes during a session, all of their tokens trace back to the same authentication event.

The logon session exists as long as tokens reference it. When the last process from a session exits and no tokens remain, the session can be cleaned up.
