---
title: Credential Types
description: What a credential type tells a client to collect, why the registry is kept short, and why credentials cross the socket in the clear.
---

A credential type tells a client **how to collect** an answer. It does
not tell it what the answer means.

| Value | Name | Collection |
|---|---|---|
| 1 | Password | A line of text, not echoed |

The registry is deliberately short. A type is added when a client would
need to collect something differently, not when an authority acquires a
new way of checking something.

> [!NOTE]
> A one-time code is collected exactly as a password is — a line of
> text, not echoed — so it needs no new type. An authority asks for it
> with `credential_type = Password` and a `credential_name` of
> "Verification code". A hardware token that requires a challenge to be
> relayed to a reader *would* need a new type, because no existing
> collection method produces the answer.
>
> This is the test to apply: does an existing client, understanding only
> the types it already has, collect the right thing? If yes, no new type
> is needed.

## Adding a type

Adding a value to this enumeration is a **breaking change** and requires
a version bump (§2.6).

An authority MUST NOT send a prompt for a type absent from the client's
`supported_credential_types`, so an authority using a new type simply
cannot reach an older client — which is the correct outcome, and is why
the capability list exists. The converse — a newer *client* reaching an
older authority — is what the dropping rule in §2.7 exists for.

## Why credentials cross in the clear

Credential material travels this socket as **plaintext**. That is
deliberate, and the alternative is worse.

Challenge-response requires the verifier to store something it can
recompute the response from: either the plaintext, or a value that is
*password-equivalent*. NTLM works exactly this way — the stored hash is
as good as the password, forever, which is why pass-the-hash has been
the most valuable credential on a Windows network for twenty years.

A modern verifier — argon2id and its relatives — is deliberately **not**
password-equivalent and cannot answer a challenge. That is the property
that makes stealing the store meaningfully weaker than knowing the
passwords.

So challenge-response would trade a permanent weakness at rest for
protection of a channel that is not the weak point. Anyone able to read
this socket can already `ptrace` the process holding the password.

### What would change the answer

A PAKE — OPAQUE, SRP — gives both properties at once: nothing
password-equivalent at rest, and no plaintext on the wire. It is worth
revisiting if an authority ever authenticates **across a network without
TLS**.

It is not worth its complexity for a local, kernel-mediated socket,
where the threat it defends against is already able to do worse.

### What follows

Because plaintext crosses the wire, bounding how long it survives
becomes an obligation of both roles rather than a nicety. See §2.12.
