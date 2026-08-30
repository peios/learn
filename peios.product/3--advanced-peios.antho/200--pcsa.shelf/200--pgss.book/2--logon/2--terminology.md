---
title: Terminology
description: Terms this chapter borrows unchanged from the Peios Kernel TRM and PCDS, and the one it has to qualify — logon type.
---

Terms defined in the Peios Kernel TRM (token, logon session, privilege,
integrity level, logon type) and in PCDS (SID, security descriptor,
DACL) are used here with the same meaning and are not redefined.

**Authority.** The process that listens on the logon socket, decides
whether a logon succeeds, mints the resulting token, creates the logon
session, and answers identity lookups. There is at most one authority on
a running system.

**Client.** A process that connects to the authority. Also called the
*originator* when the emphasis is on whose identity the authority
verifies. There are two client roles — originating a logon and looking
an identity up — and they are independent (§2.20).

**Principal.** The identity a logon is *for* — the person or service
being authenticated. The principal is not a party to the conversation;
the client speaks on their behalf.

**Conversation.** One logon connection's exchange, from the client's
opening message to a terminal message from the authority. One connection
carries exactly one conversation.

**Round.** One `CredentialRequest` from the authority and the
`CredentialResponse` that answers it. A conversation MAY take several
rounds.

**Terminal message.** `AccessGranted` or `AccessDenied`. Exactly one is
sent, and nothing follows it.

**Credential material.** Any byte sequence a principal supplies as proof
of identity — a password, a one-time code, a response from a token.
Distinguished throughout from a **verifier**, which is what an authority
stores and which MUST NOT be usable as credential material.

**Prompt.** A request from the authority for one piece of credential
material, carrying enough description for a client to render it without
understanding what it is for.

**Derivation.** The authority's construction of a token's contents — its
SIDs, privileges and integrity level — from the authenticated identity
and local policy. Distinct from *authentication*, which establishes only
that the principal is who they claim.

**Attestation.** A trusted process's assertion that a logon should
happen, standing in for a credential where none exists and none should.
Distinct from *authentication*, which establishes that a principal is
who they claim by something only they could present; an attestation
establishes only that the party asking is one the authority permits to
ask (§2.19).

**Source.** A party an authority consults in order to answer a question
about identity. Whether an authority has sources at all, and what they
are, is its own design; the term appears here only where the protocol's
behaviour depends on there being more than one possible answerer
(§2.15, §2.18).

## A note on "logon type"

`LogonType` (§2.7) describes the *kind* of session being established —
interactive, network, batch, service. It is a property of the situation,
not of the principal, and the same principal may hold several sessions
of different types at once. Its values and meanings are defined by KACS
and described in the Peios Kernel TRM; this chapter carries it but does
not define it. The values are listed for reference in §2.B.
