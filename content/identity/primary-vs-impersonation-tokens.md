---
title: Primary Tokens vs Impersonation Tokens
type: concept
order: 40
description: The difference between a process's primary token and per-thread impersonation tokens, and when the kernel uses each.
---

There are two kinds of token on Peios: **primary tokens** and **impersonation tokens**. They serve different purposes and operate at different scopes.

## Primary tokens

Every process has exactly one primary token. It is the process's baseline identity — the answer to "who is this process?"

The primary token is **shared by all threads** in the process. It is set when the process is created and inherited from the parent. All threads see the same primary token, and changes to it (such as enabling or disabling a privilege) are visible to every thread.

A process's primary token can only be replaced by a caller that holds the `SeAssignPrimaryTokenPrivilege` — a highly restricted privilege typically held only by the init process and the authentication service.

## Impersonation tokens

An impersonation token is a **per-thread** override. When a thread is impersonating, the kernel uses the impersonation token instead of the primary token for access decisions.

Impersonation is how services act on behalf of their clients. When a file server receives a request from a user, the handling thread sets an impersonation token that carries the user's identity. The kernel then checks the user's permissions, not the server's. Other threads in the same process are unaffected — they continue using the primary token or their own impersonation tokens.

When the thread is done handling the request, it reverts to the primary token by clearing its impersonation state.

## Which token does the kernel use?

The rule is straightforward:

1. If the thread has an impersonation token, the kernel uses it.
2. Otherwise, the kernel uses the process's primary token.

There is always a token — every thread either has an impersonation token set or falls back to the primary token. The kernel never makes an access decision without an identity.

## Why two kinds?

The primary token establishes what the process **is**. A web server is a web server — its primary token identifies the service account it runs as, with the privileges and group memberships appropriate to that role.

The impersonation token establishes what the process is **doing right now**, on behalf of someone else. The web server handling a request from Alice temporarily becomes Alice for the purpose of accessing Alice's files. It doesn't need blanket access to every user's files — it accesses exactly what Alice can access, nothing more.

This separation means services only need the permissions required for their own operation. Access to client resources is scoped to what each client is individually allowed to do.
