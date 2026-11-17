---
title: Authenticate
description: A neutral authentication request routed to one source, with verified originator and optional local logon context.
---

`msg_type` = `0x0002`. Authority to source. **Opens a conversation.**

| Field | Encoding | Limit |
|---|---|---|
| `start` | nested `AuthenticationRequest`, length-framed | PGSS §2.24 |
| `originator` | length-framed bytes (SID) | 68 bytes |
| `has_logon_context` | u8, exactly 0 or 1 | |
| `logon` | nested length-framed local context, when present | below |
| `has_presented` | u8, exactly 0 or 1 | |
| `presented` | nested length-framed proof, when present | below |

## start

The shared authentication request, nested whole (PGSS §2.24). Its fields and
meanings are unchanged — including that `identifier` is an
unverified claim and `supported_credential_types` binds what may be
prompted for.

## Local logon context

Only OS Logon supplies this structure. General Authenticate supplies no
local context and MUST NOT invent a dummy logon type.

| Field | Encoding | Limit |
|---|---|---|
| logon_type | u8 | PGSS §2.B |
| tty | string | 128 bytes |
| remote_host | string | 256 bytes |

These are the local context fields of PGSS §2.7. The type is the caller's
proposal; the terminal and host remain unverified context. Sources apply
general account and credential restrictions for both operations. The
authority applies permitted_logon_types only when finalizing OS Logon.

## originator

The **verified** identity of the process that requested this logon,
taken by the authority from the client's connected socket and never from
a message body.

A source cannot learn this for itself: it is not party to the client's
connection, and there is nothing it could ask. The authority relays it
because a source may legitimately refuse a logon on the strength of it —
an account restricted to console logons needs to know what asked — and
that decision needs a trustworthy input.

A source MUST treat `originator` as established fact and MUST NOT treat
any other field of this message the same way.

## Presented proof

Present only for an **identity-in-answer** credential type (PGSS §2.11),
of which Ntlmv2 is the only one. The authority has already issued the
challenge and collected the answer, because the answer is what names the
principal.

| Field | Encoding | Limit |
|---|---|---|
| credential_type | u8 | MUST be 4, Ntlmv2 |
| challenge | length-framed bytes | exactly 8 bytes |
| answer | length-framed bytes | PGSS §2.11 |

`start` is the client's request unchanged, so its identifier is empty and
it requires the presented type. `answer` is the client's answer data,
unchanged. The source takes the principal's name from the answer, decoded
as the authority decoded it to route the request here, so there is only
one copy of the name to trust.

A source MUST verify the presented proof against `challenge` and answer
with Assertion or Refusal. It MUST NOT send a CredentialRequest in this
conversation: there is no client prompt left to send, and nothing it
asked could be relayed. A source that does not support the presented
type MUST refuse with `AuthenticationFailed`.

The source trusts `challenge` because it trusts the authority, as it
trusts `originator`. Single use and freshness of the challenge are the
authority's obligation (PGSS §2.11).

An authority MUST NOT present a proof for any other credential type.
Every other type is collected by the source over the relayed
interrogation (§2.12), unchanged.

## Routing

Before sending `Authenticate`, an authority MUST decide **which single
source** answers.

The credential MUST NOT be offered to more than one source. Trying each
in turn *with the password* hands every source the credentials of every
other source's users, including on typos — the failure PAM stacking
exemplifies (§2.D).

Resolution therefore happens on the identifier, before any credential
exists. Asking several sources "do you own this name?" is a resolution
step with no secret in it and is permitted; offering them the answer is
not.

An authority SHOULD resolve a qualified name to its owning source and
MUST NOT fall back to another source when the owning one is unreachable.
A name that can fall through lets anyone who can break a network choose
which authority answers for a principal.

### Identity-in-answer types

For an identity-in-answer type, the name arrives with the credential, so
resolution cannot precede it. The authority resolves the name decoded
from the answer, by the same procedure, before offering the proof to any
source, and then offers it to the owning source alone. The rule this
section protects is unchanged: no source ever receives a credential that
belongs to another source's principal. Resolution queries still carry
only the name.

This mirrors NTLM pass-through authentication on Windows, where the local
security authority issues the challenge and forwards challenge and
response to the account's domain controller for verification.

## Conversation limits

An authority MUST bound the conversations it opens against one source. A
source MUST bound what it will track, and MUST refuse beyond its own
limit with `AuthorityUnavailable` (§2.13) rather than dropping the
conversation silently.
