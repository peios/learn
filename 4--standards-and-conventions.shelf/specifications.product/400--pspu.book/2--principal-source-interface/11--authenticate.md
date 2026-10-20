---
title: Authenticate
description: The client's LogonStart nested whole and routed to a source, with the conversation limits that bound what follows.
---

`msg_type` = `0x0002`. Authority to source. **Opens a conversation.**

| Field | Encoding | Limit |
|---|---|---|
| `start` | nested `LogonStart`, length-framed | PGSS §2.7 |
| `originator` | length-framed bytes (SID) | 68 bytes |

## start

The client's `LogonStart`, nested whole (§2.7). Its fields and their
meanings are PGSS §2.7's, unchanged — including that `identifier` is an
unverified claim and `supported_credential_types` binds what may be
prompted for.

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

## Conversation limits

An authority MUST bound the conversations it opens against one source. A
source MUST bound what it will track, and MUST refuse beyond its own
limit with `AuthorityUnavailable` (§2.13) rather than dropping the
conversation silently.
