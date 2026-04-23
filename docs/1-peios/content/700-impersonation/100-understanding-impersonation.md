---
title: Understanding Impersonation
type: concept
description: How services temporarily adopt a client's identity so access decisions use the client's token, not the service's.
---

**Impersonation** is the mechanism by which a service thread temporarily adopts a client's identity. While impersonating, the kernel evaluates all access decisions using the client's token — not the service's own token.

## Why impersonation exists

Consider a file server that handles requests from many users. Without impersonation, the server would need its own access to every file any user might request. That means granting the file server broad permissions — and if it is compromised, the attacker inherits all of that access.

With impersonation, the file server does not need access to user files at all. When Alice requests a file, the handling thread impersonates Alice. The kernel checks Alice's permissions. If Alice can read the file, the read succeeds. If she cannot, it fails. The file server never accesses anything on its own authority — it always acts as the specific client making the request.

This means a compromised file server can only access what the currently-connected clients can access, and only during the window of their active requests. The blast radius of a compromise is bounded by the clients' individual permissions, not by a blanket grant to the service.

## How impersonation works

1. A client connects to a service
2. The service thread sets an **impersonation token** carrying the client's identity
3. All access decisions on that thread use the client's token
4. Other threads in the service process are unaffected — they continue using the service's primary token or their own impersonation tokens
5. When the thread finishes the client's request, it **reverts** to the service's primary token

The impersonation token is per-thread. A service handling ten clients simultaneously has ten threads, each impersonating a different client. The kernel evaluates each one independently.

## The client controls the scope

Impersonation is not unilateral. The client chooses how far their identity can travel by setting an **impersonation level** on the connection. The four levels range from "the service cannot identify me at all" to "the service can forward my identity to other machines." The service cannot exceed the level the client consented to.

This gives clients control over their own identity. A client connecting to a print spooler might allow impersonation for local file access. A client connecting to an untrusted service might restrict the level to identification only — the service can see who the client is but cannot act as them.

Impersonation levels are covered in detail in the next page.

## SeImpersonatePrivilege

A service must hold `SeImpersonatePrivilege` on its token to impersonate clients. This privilege is assigned to service accounts that need to act on behalf of users — file servers, print spoolers, web services.

A process without `SeImpersonatePrivilege` cannot set an impersonation token, even if a client connects with a permissive impersonation level. The privilege is a gate on the service side, and the impersonation level is a gate on the client side. Both must allow it.
