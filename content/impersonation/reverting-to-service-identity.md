---
title: Reverting to Service Identity
type: how-to
order: 130
description: How and when to call revert_to_self to clear an impersonation token and return to the service's own identity.
---

After handling a client's request, a service thread should **revert** to the service's primary token. This clears the impersonation state and returns the thread to the service's own identity.

## Revert impersonation

```
revert_to_self()
```

The thread's impersonation token is cleared. All subsequent access decisions on this thread use the process's primary token — the service's own identity.

## When to revert

Revert as soon as the client's request is complete. Holding an impersonation token longer than necessary increases the window during which the thread operates under the client's authority. If the thread performs internal bookkeeping or maintenance after handling the request, that work should run under the service's own identity.

A common pattern:

```
connection = accept_client()
impersonate(connection)

// Handle the client's request — all access uses the client's identity
result = open_file(client_requested_path)

revert_to_self()

// Post-request work — access uses the service's identity
update_internal_log(result)
```

## Verify the revert

After reverting, the thread should be back to the primary token:

```
$ idn show <pid>/<tid>
User:            S-1-5-19 (Local Service)
Impersonating:   no
```

## What happens if you don't revert

If a thread continues with an impersonation token, all subsequent operations are evaluated under the client's identity — including operations that should run as the service. This could cause failures (the client's token may lack permissions the service needs for its own work) or security issues (the thread might access resources that should only be reached under the service's authority).

Always revert explicitly. Do not rely on the impersonation token being cleared automatically.
