---
title: Impersonating a Client's Identity
type: how-to
description: How service developers impersonate a client connection so the thread operates under the client's identity.
---

This page is for **service developers**. When a client connects to your service, you can impersonate their identity so that all access decisions on your thread use the client's permissions instead of your service's.

## Impersonate the client

After accepting a client connection, call the impersonate operation on the connection handle:

```
impersonate(connection)
```

From this point, the calling thread carries the client's impersonation token. Every access decision — file opens, registry reads, connections to other services — is evaluated against the client's identity.

Other threads in your process are unaffected. They continue using the service's primary token or their own impersonation tokens.

## Verify the impersonation state

After impersonating, you can confirm the thread's identity:

```bash
$ idn show <pid>/<tid>
User:            S-1-5-21-...-1013 (alice)
Impersonating:   yes
Impersonation Level: Impersonation
```

The thread is now acting as Alice.

## Requirements

Two conditions must be met for impersonation to succeed:

**The service must hold `SeImpersonatePrivilege`.** Without this privilege, the impersonate call fails. This privilege is assigned to service accounts that need to act on behalf of clients.

**The client must have set a sufficient impersonation level.** If the client connected at Identification level, the service can read the client's identity but the impersonation token will only be usable for identification — access decisions will use the Anonymous identity, not the client's.

## What happens during impersonation

While impersonating:

- File opens check the **client's** token against the file's security descriptor
- Registry operations check the **client's** token against the key's security descriptor
- Connections to other local services carry the **client's** identity — the receiving service sees the client, not your service
- Privilege checks use the **client's** privileges, not your service's

Your service's own identity and privileges are irrelevant for the duration of the impersonation. The thread operates entirely under the client's authority.
