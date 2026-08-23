---
title: AccessDenied
description: The terminal failure message — a deliberately small denial vocabulary, and what a denial must never reveal.
---

`msg_type` = `0x8003`. Authority to client. The other terminal message;
nothing follows it.

| Field | Encoding | Limit |
|---|---|---|
| `denial` | `u32` | §2.B |
| `reason` | string | 512 |

## denial

A code from a deliberately small vocabulary (§2.B), for a client that
needs to *act* differently — retry, offer a different account, report a
system fault.

`PermissionDenied` and `LogonTypeNotPermitted` are distinct on purpose:
the first says the peer may not use this socket for this at all, the
second that it may originate logons but not of this kind. A client can
act differently on each.

## reason

Text for the principal to read. A client SHOULD display it and MUST NOT
interpret it.

The division is the same one `CredentialRequest` makes between
`credential_type` and `credential_name`: the machine-readable field is
small and stable, the human-readable one is free.

`reason` MUST NOT narrow an `AuthenticationFailed` into a specific
cause.

## What a denial must not reveal

The denial vocabulary deliberately does **not** distinguish "no such
principal" from "wrong credential". Both are `AuthenticationFailed`.

A protocol that distinguished them would make account enumeration a
supported feature: anyone able to reach the socket could test names and
learn which exist. An authority MUST NOT provide that distinction
through the denial code, through `reason`, or through observable timing.

The timing obligation is the one most often missed, and it binds even
though this chapter cannot check it. An authority whose
unknown-principal path returns faster than its wrong-credential path has
published the distinction it just declined to state — see §2.12.

> [!NOTE]
> An authority MAY record the distinction in an audit trail an
> administrator can read. What it must not do is return it to the
> caller.
