---
title: How Identity Cascades Across Local Services
type: concept
order: 30
description: How a client's identity flows through chains of local services via impersonation without amplifying authority.
---

When a service impersonates a client and then calls another local service, the client's identity **cascades** — the second service sees the client, not the first service.

This is how multi-tier architectures work securely on Peios. The client's identity flows through the chain of services, and each service accesses resources with the client's permissions.

## A concrete example

Alice connects to a web application. The web application needs to read a configuration value from the registry service on her behalf.

1. Alice connects to the web application at **Impersonation** level
2. The web application thread impersonates Alice
3. While impersonating, the thread connects to the registry service
4. The registry service receives the connection and checks the peer identity — it sees **Alice**, not the web application
5. The registry service impersonates Alice and reads the registry key
6. The kernel checks Alice's permissions against the registry key's security descriptor

At no point does the web application's own identity appear in the access decision for the registry key. Alice's identity traveled from the web application to the registry service, and the registry service evaluated access as Alice.

## Why this works

When an impersonating thread connects to another local service, the connection carries the **impersonation token** — the client's identity. The receiving service sees the client's SID, not the calling service's SID.

The receiving service can then impersonate the client in turn, continuing the chain. Each service in the chain acts as the client, accessing only what the client is allowed to access.

## The impersonation level controls cascading

Cascading only works at **Impersonation** level or above. At Identification level, the first service can see the client's identity but cannot act as them — so when it connects to a second service, the connection carries the first service's own identity, not the client's.

| Client's level | What the second service sees |
|---|---|
| **Anonymous** | Anonymous identity |
| **Identification** | The first service's identity |
| **Impersonation** | The client's identity |
| **Delegation** | The client's identity (and can forward it further, even across the network) |

## The chain does not amplify authority

Each service in the chain impersonates the same client identity. The client's permissions do not grow as the identity passes through more services. If Alice cannot read a registry key, no amount of cascading through intermediary services changes that.

The chain also does not accumulate the services' own permissions. The web application might have broad registry access under its own identity, but while impersonating Alice it can only access what Alice's token allows.

## Cascading and SeImpersonatePrivilege

Every service in the chain must hold `SeImpersonatePrivilege` to impersonate the client. If a service in the middle of the chain does not have the privilege, the cascade breaks at that point — the next service sees the unprivileged service's identity, not the client's.

This is a safety property. Only services that are explicitly granted impersonation capability can participate in identity cascading. An unprivileged service cannot silently forward a client's identity to other services.
