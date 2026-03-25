---
title: Service Identities and Per-Service SIDs
type: concept
order: 60
description: How services get purpose-built tokens with per-service SIDs to isolate authority between services sharing an account.
---

Every service on Peios runs with its own **purpose-built token**. The init process creates each service's token at startup, tailored to the service's role — with the right identity, group memberships, and only the privileges the service needs.

## Service accounts

Services run under one of several built-in accounts, depending on what they need to do:

| Account | SID | Typical use |
|---|---|---|
| **SYSTEM** | `S-1-5-18` | Core system services that need full access to the machine (init, authentication service, registry) |
| **Local Service** | `S-1-5-19` | Services that need minimal local access and no network identity |
| **Network Service** | `S-1-5-20` | Services that need to authenticate to other machines on the network |

Most services run as Local Service or Network Service. SYSTEM is reserved for the small set of trusted components that form the core of the operating system.

## Per-service SIDs

Multiple services might run under the same account. Two services both running as Local Service would share the same user SID — making them indistinguishable to access control. Any resource that grants access to one would implicitly grant access to the other.

Per-service SIDs solve this. Each service receives a **unique SID** in its token's group list that identifies that specific service. Even if two services share the same user account, their per-service SIDs are different.

This means a security descriptor can grant access to a specific service without granting it to every service running under the same account. A database service can have exclusive access to its data directory, and another Local Service process cannot reach it — even though both tokens carry the same user SID.

## How service tokens are built

The init process constructs each service's token from its service definition:

1. **User SID** — the service account (SYSTEM, Local Service, or Network Service)
2. **Per-service SID** — a unique SID identifying this specific service, added to the group list
3. **Groups** — any additional groups the service needs membership in
4. **Privileges** — only the specific privileges the service requires, nothing more

A DNS service gets the privileges it needs to bind a port. A file server gets the privileges it needs to impersonate clients. Neither gets the other's privileges, and neither gets privileges it doesn't need.

## Principle of least privilege

Per-service tokens enforce least privilege at the identity level. Each service starts with the minimum authority required for its role. If a service is compromised, the attacker gains only what that service was allowed to do — not the full authority of the account it runs under, and not the authority of any other service.

This is a structural property, not a convention. The kernel enforces the token's contents on every access decision. A service cannot escalate beyond its token regardless of what it attempts.
