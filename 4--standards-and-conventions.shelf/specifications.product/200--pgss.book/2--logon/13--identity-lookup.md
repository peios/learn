---
title: Identity Lookup
description: The second half of the chapter — turning an identity you already hold into something displayable, on a second socket rather than a second standard.
---

Sections 2.3 to 2.12 specify how a caller obtains a token. The remainder
of this chapter specifies how any program on the system turns an
identity it already holds into something it can display or compare: a
name into a SID, a SID into a name, a POSIX identifier into either.

It exists because a Linux program calls `getpwuid` and has never heard
of a token. Without this surface, every principal an authority mints
appears throughout the system as a bare number.

## Why the authority answers this

An authority may federate identity to separate sources, and a source
counts POSIX identifiers **relative to a range the authority assigns
it**. The authority adds the base. No message in either direction
carries an absolute identifier to or from a source: a source asserts
relative numbers, and is asked by relative number or by SID.

The arithmetic that makes a number absolute therefore exists in exactly
one place, and only that place can invert it. No source can be asked
"who is uid 1001000", because no source is ever asked an absolute
number at all. The authority is not merely a convenient place to put
this — it is the only party the protocol permits to answer.

The same holds for names. A bare name may exist in more than one source,
and which one wins is a property of the system rather than of any source
in it (§2.15).

> [!NOTE]
> An authority that keeps all identity in one built-in database still
> satisfies this, and for it the rebasing question does not arise. The
> requirement is on the answer, not on how the answer is reached — as
> everywhere else in this chapter.

## A second socket, not a second standard

Identity lookup is served on `/run/ident.sock` (§2.14), separately from
`/run/logon.sock`, by the same authority speaking the same framing
(§2.6).

The separation is **not** for isolation. One authority answers both, so
a defect or a hang in either reaches the other regardless; a second
socket buys nothing there and this chapter does not pretend otherwise.

It is for **admission**. A listening socket has one accept queue. A
single directory listing is thousands of lookups and a filesystem walk
is millions, where logons are a handful per boot — so a shared socket
would let an ordinary `find` fill the queue that an administrator needs
in order to sign in and stop it. Two sockets means the two populations
of caller cannot starve each other, whatever load either is under.

The second reason is access control. The set of programs that may
originate a logon is small and enumerable; the set that may look up a
name is every program on the system. Those want different security
descriptors, and a descriptor is a property of a socket.

## Not a conversation

A logon is stateful: the connection *is* the conversation, and needs no
correlation identifier (§2.5).

A lookup is not. Requests are independent, a connection carries as many
as a client cares to send, and replies MAY return in an order other than
the one requests arrived in. Each request therefore carries a `tag` that
its reply echoes (§2.14).

> [!NOTE]
> That is what allows an authority to satisfy several outstanding
> requests from one connection together — against a remote source, in a
> single query — without a delay window that would tax a caller waiting
> on a single answer. Nothing here requires it, and an authority that
> answers strictly in order, one request at a time, is fully conformant.

## Not authentication

No credential ever crosses this socket. There is no message with which a
client could offer one and none with which an authority could ask.

Everything here returns the kind of data a POSIX system has historically
kept in a world-readable file. An authority MAY nonetheless restrict
individual fields (§2.16), and the request names the fields it wants
precisely so that it can.

## Not in this version

**Privileges, integrity levels, owner and default DACL are not returned
by any message here.** They are not identity: nothing stores them, and
an authority computes them from local policy at the moment it derives a
token (§2.1).

They are, however, deliberately *reserved* rather than excluded. An
authority that cannot be asked what a policy would produce can only be
verified by signing someone in and observing the result. A future
revision is expected to add a distinct request of the shape:

```
Evaluate { key, logon_type } -> { privileges, integrity, owner, default_dacl }
```

— a token that is derived and then discarded. It is parameterised by
logon type because the answer genuinely depends on it: an authority adds
SIDs reflecting *how* a principal signed in (§2.16), so "what privileges
does this principal have" has no single answer.

A revision MUST NOT instead add privileges or integrity as fields of
`Lookup` (§2.16). A field of a record describes something a source
holds; this does not.
