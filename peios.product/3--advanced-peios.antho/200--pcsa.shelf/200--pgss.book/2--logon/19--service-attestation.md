---
title: Service attestation
description: How a service manager obtains a token for a service it is launching — a request with no credential behind it, and the narrow conditions under which an authority may honour one.
---

`msg_type` = `0x0020`. Client to authority, on `/run/logon.sock`. A
complete request in one message; the authority answers with
`AccessGranted` (§2.9) or `AccessDenied` (§2.10) and nothing else
follows.

| Field | Encoding | Limit |
|---|---|---|
| `identity` | string | 128 |
| `service` | string | 256 |

A service has no human to prompt and no secret to present. This is the
message by which the component that launches services obtains a token
for one, and the whole of this section is about the conditions under
which an authority may answer it.

## A service identity MUST NOT have a credential

An authority MUST NOT hold, store, or accept a credential for a service
identity, and MUST NOT offer a credential exchange for one.

This is not a convenience. A machine that could authenticate its own
services unattended would have to hold their secrets, so a credential
for a service identity implies a store of service credentials on every
machine that runs one — a structure that is read by anything which
compromises the machine, and which grants whatever those identities
were given. The requirement exists to make that structure impossible
rather than to make it careful.

What replaces the credential is *attestation*: the authority satisfies
itself about **who is asking**, and derives everything else.

## Why this is not a `LogonStart`

A `LogonStart` (§2.7) followed by no credentials would encode the same
request. It is a separate message because the difference is structural
rather than cosmetic.

Accepting a credential-free `LogonStart` creates a path through an
authority's conversation handling on which **zero credentials
succeeds**. The only thing then standing between an arbitrary principal
and a credential-free token is the authorisation check below being
correct — so a defect in that check is a complete authentication bypass
rather than a defect.

With a distinct message, the credential-free path is reachable only by
a message that carries no principal an authority would accept. The
check remains necessary; it stops being the only thing.

An authority MUST reject a `LogonStart` that completes without a
credential exchange for any identity it would accept here, and MUST
reject a `ServiceAttest` naming an identity it would accept there.

## Who may send it

An authority MUST refuse a `ServiceAttest` unless **both** of the
following hold of the connected peer, each established from the
connection itself and never from the message:

1. The peer is a principal the authority permits to attest — this
   standard does not fix which, and an implementation SHOULD keep the
   set as small as one.
2. The peer is the process the platform designates as its service
   manager, established by a property of the connection that no other
   process can present.

Neither is sufficient alone, and an authority that checks only the first
has a much weaker rule than it appears to. On a system where platform
components share one identity — which is usual — the first condition
alone admits every daemon on the machine, so compromising any one of
them yields a token for any service identity the authority would mint.

An authority MUST answer a refusal with `PermissionDenied`.

> [!NOTE]
> On Peios the two facts are that the peer's token names SYSTEM, and
> that the peer is PID 1. The second is sound there for a reason
> specific to PID 1 — it cannot exit and be replaced while the system
> runs, and the credentials are captured by the kernel when the
> connection is made — and that reasoning does not extend to any other
> process identifier.

## What the authority may attest

An authority MUST NOT mint a token under this message for a principal
that has not been designated as usable for a service logon.

The designation is a property of the principal, held wherever that
principal is held, and it is what keeps this message from being an
oracle that yields a credential-free token for anybody on the machine.
An authority that cannot determine whether a principal carries it MUST
refuse with `AccountRestricted`.

Identities the authority defines for itself — the platform's own service
identities, which no principal source holds and for which no credential
could exist — are designated by construction.

A refusal here MUST NOT distinguish "no such principal" from "not
designated for service logon", for the reason given in §2.10.

## `service`, and what the authority cannot check

`service` names the service being launched. The authority uses it to
derive the per-service identifier it stamps on the token, which is what
keeps two services running under the same identity distinguishable to an
access decision.

**An authority cannot verify it.** Elsewhere in this standard a peer's
claims are checked against the connection: an authority establishes who
is calling rather than believing what it is told. That is not available
here, because the process this request is about *does not exist yet* —
there is no token to interrogate and nothing to compare the name
against.

So `service` is taken on the peer's word. This is a genuine grant of
trust and it is not removable: the service manager holds the service
definitions, launches the process, and is the only component in a
position to know which service it is launching. It is the reason the set
of peers permitted to send this message is required to be as narrow as
it is.

An authority MUST reject an empty or unusable `service`, with
`MalformedRequest`. An empty name derives a well-formed identifier that
names nothing and that every service making the same mistake would
share.

## The token

Answered with `AccessGranted` (§2.9), carrying the token as a descriptor
under the same rules as any other logon, and with the logon type
recorded as `Service`.

The `profile` structure SHOULD be empty. A service has no home
directory, no shell and no display name, and an authority that has
nothing to say MUST leave the fields empty rather than invent values.

### The token is weaker, and MUST be

A token issued on attestation MUST NOT be usable to authenticate to
another system on this authority's behalf.

The evidence behind it does not travel. A credential a principal source
verified is evidence a second system could in principle have checked
too; a local process's word is evidence on one machine only, and a token
forwarded off the machine on the strength of it would let one system's
service manager act as an arbitrary account on another.

Where a platform expresses this as a level on the token, the level an
attested logon receives MUST be below the level a credentialled logon
receives, and MUST bound everything derived from that token.

An authority MUST record, in whatever it records for a credentialled
logon, that this logon was attested rather than authenticated. An audit
trail that cannot tell the two apart cannot answer which authority
vouched for a session.
