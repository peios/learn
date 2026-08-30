---
title: Scope and Roles
description: What PGSS Logon specifies and who its parties are — obtaining a token from an authority, resolving identity, and the boundaries the authority does not cross.
---

This chapter specifies **PGSS Logon**: the protocol by which a caller
obtains a KACS token and a logon session from an authentication
authority, and the protocol by which any program on the system resolves
an identity it already holds into a name, a SID, or the attributes a
POSIX program expects of one.

Two roles participate.

The **authority** is the process that listens on the logon socket. It
decides whether a logon succeeds, mints the resulting token, creates the
logon session, and answers identity lookups. There MUST be at most one
authority on a running system.

The **client** connects and speaks on a principal's behalf. It proposes
what kind of logon it wants, renders prompts and returns answers without
interpreting them, and receives the token and installs it itself. A
client is not trusted: everything it sends is a claim (§2.4).

The **principal** is the identity a logon is *for* — the person or
service being authenticated. The principal is not a party to the
conversation.

Both roles are publicly implementable. A third party MAY ship a
different authority, a different logon originator, or both, and
interoperate with the other half unchanged.

This chapter covers:

- the two channels an authority offers, and the access control
  governing each (§2.5, §2.14)
- message framing, header layout, and the rules under which the format
  may be extended (§2.6)
- the messages of the logon conversation, their fields, and their
  encodings (§2.7 to §2.10)
- the shape of a conversation: who speaks, in what order, and how it
  terminates (§2.3)
- the transfer of the minted token to the caller, and the
  session-profile values a logon originator needs in order to start a
  session (§2.9)
- credential handling obligations binding on both roles (§2.11, §2.12)
- what an authority MUST establish for itself rather than believe from
  a message (§2.4)
- resolving a principal to a name, a SID, a POSIX identifier, or the
  attributes a POSIX program expects of one (§2.13 to §2.18)
- how a bare name is resolved when more than one source could answer it
  (§2.15)
- how a service manager obtains a token for a service, where there is no
  credential to exchange (§2.19)
- the obligations binding on each role (§2.20)

This chapter does not cover:

- Tokens, SIDs, privileges, integrity levels, logon sessions, logon
  types, and access checks — described in the Peios Kernel TRM. SIDs
  and security descriptors are specified in PCDS.
- How an authority decides *whether* a credential is valid, where it
  keeps identity, which principals exist, or what they are called.
  Those belong to the authority's own design. Mainline's authority
  federates them over PSI, the Principal Source Interface, specified in
  PSPU §2.
- Password change, credential enrolment, and account administration,
  which are not specified.
- Service startup and ordering, described in the peinit TRM.

The distinction in the second point is the load-bearing one. PGSS Logon
specifies how a caller *asks* and how an authority *answers*. It says
nothing about how the authority reaches its answer, because that is
exactly what different systems will do differently, and constraining it
would make the standard a description of one implementation rather than
a contract between two.

> [!NOTE]
> Mainline's authority is `authd`, which federates authentication to
> separate principal-source processes over PSI (PSPU §2). That
> architecture is
> *one* way to satisfy this chapter. An authority that consults a single
> built-in database, or a remote directory, or a hardware token reader,
> conforms equally well provided it speaks this protocol correctly.

## What the authority does not do

An authority MUST NOT be a process factory. It does not fork the
principal's shell, does not learn about controlling terminals,
environments, or session leadership, and does not decide what the caller
does with the token it receives.

The caller installs the token and proceeds. This keeps the most
privileged process on the system out of the business of launching
arbitrary programs, and it means a client can obtain a token for a
purpose the authority need never have anticipated.

> [!NOTE]
> This is why `AccessGranted` carries a descriptor and a session
> identifier and nothing else. There is no field describing what should
> happen next, because nothing about what happens next is the
> authority's concern.

## Authentication and derivation

Two acts, deliberately separated.

**Authentication** establishes that the principal is who they claim. Its
output is an identity and nothing more.

**Derivation** constructs the token: which SIDs it carries, which
privileges, at what integrity level, with what projected identifiers.
Its inputs are the authenticated identity *and local policy*.

The separation matters because the second is where a machine's own rules
apply. An identity established elsewhere — by a directory, by a remote
authority — does not carry entitlements onto this machine with it. What
that identity *means* here is decided here, every time, by the authority
applying local policy.

An authority MUST perform derivation itself. It MUST NOT accept a token,
a privilege set, or an integrity level supplied by any other party,
whatever its trust level.

## The token this chapter does not describe

This chapter governs the conversation and the delivery of its result. It
does not govern the *contents* of the token that results. What SIDs,
privileges, and integrity level a principal receives is derivation, and
derivation is the authority's judgement applied to local policy.

A caller that receives a token from this protocol has been told who it
may act as. It has not been told, and MUST NOT infer, anything further
about how that conclusion was reached.
