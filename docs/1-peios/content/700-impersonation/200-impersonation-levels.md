---
title: Impersonation Levels Explained
type: concept
description: The four impersonation levels -- Anonymous, Identification, Impersonation, and Delegation -- and when to use each.
---

When a client connects to a service, it chooses an **impersonation level** that controls how far the service can go with the client's identity. The level is set by the client — the service cannot escalate it.

## The four levels

| Level | The service can... | The service cannot... |
|---|---|---|
| **Anonymous** | Nothing — the client's identity is hidden | Identify the client, act as the client, or forward the identity |
| **Identification** | See who the client is (read the SID, check groups) | Act as the client for access decisions or forward the identity |
| **Impersonation** | Act as the client for all local operations | Forward the client's identity to other machines |
| **Delegation** | Act as the client locally and forward the identity to remote services | Nothing — this is the maximum level |

Each level strictly includes the capabilities of the levels below it. A service with Delegation level can do everything Impersonation allows, plus network forwarding.

## Anonymous

The service receives a connection but cannot determine who the caller is. The impersonation token carries the Anonymous SID (`S-1-1-7`) — a generic identity that reveals nothing about the client.

Anonymous is used for testing whether a resource is publicly accessible. A service can impersonate at Anonymous level and attempt an access check to determine if the operation would succeed for an unidentified caller.

## Identification

The service can read the client's token — inspect the user SID, group memberships, privileges, and integrity level. But it cannot use the token for access decisions. Any attempt to open a resource while impersonating at Identification level is evaluated against the Anonymous identity, not the client's.

Identification is useful for services that need to log who is calling or make authorization decisions in their own application logic, without needing kernel-enforced access as the client. An API gateway might check "is this user in the Developers group?" without needing to access any resources on the user's behalf.

## Impersonation

The service can act as the client for all **local** operations. Opening files, reading registry keys, connecting to other local services — the kernel evaluates all of these using the client's token. This is the level most services operate at.

The boundary is the machine. An impersonating thread can access anything the client can access on the local machine. It cannot forward the client's identity across the network — connecting to a remote file share as the client requires Delegation.

## Delegation

The service can forward the client's identity to **remote services** on other machines. This is required for multi-hop scenarios: a user connects to a web application, which needs to access a database on a different server as that user.

Delegation is the most powerful level. It allows the client's identity to travel across machine boundaries via Kerberos delegation. Because of this power, Delegation is typically restricted — only specific service accounts trusted for delegation can exercise it, and the domain policy controls which services can delegate to which targets.

See [Networked IPC](../IPC/networked-ipc) for the mechanism Peios uses to forward identity across the domain — how a Delegation-level token actually reaches a remote service and produces a meaningful local identity there.

## Choosing the right level

The client should set the minimum level the service needs:

| Scenario | Appropriate level |
|---|---|
| Testing if a resource is public | Anonymous |
| Service needs to log who called | Identification |
| Service accesses local resources on behalf of the client | Impersonation |
| Service accesses resources on other machines on behalf of the client | Delegation |

The default for most local service connections is **Impersonation** — sufficient for the service to act as the client locally without granting the ability to forward identity across the network.
