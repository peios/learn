---
title: Scope and Roles
description: What PSI specifies — how an authentication authority federates identity to separate processes that hold it — and its two roles.
---

This chapter specifies the **Principal Source Interface (PSI)**: the
protocol by which an authentication authority federates identity to
separate processes that hold it.

Two roles participate.

The **authority** is the process that mints tokens and creates logon
sessions. It is the party asking. On PSI it listens; it never dials out
(§2.3). It is also the party that speaks PGSS Logon to its clients, and
PSI exists so that it can answer them.

The **source**, in full a *principal source*, is a process that is
authoritative for some set of principals: it verifies their credentials
and says who they are. The source role is publicly implementable: any
process an authority has been configured to accept MAY register as a
source, and a third party writing one for a directory, a hardware token
service or an identity provider is the case this chapter is written for.
A conforming source is the subject of the source obligations in §2.21.

A source is not a *store*, necessarily. A local source owns its bytes; a
directory-backed source owns nothing and forwards the question. The
interface deliberately does not distinguish them, which is why the term
is "source" rather than "store".

What a source is emphatically **not** is a component of the authority.
It runs as a separate process, at lower trust, and it cannot mint
anything (§2.4).

This chapter covers:

- the channel, its direction, and why sources connect inward (§2.3,
  §2.6)
- message framing, the conversation identifier, and the rules under
  which the format may be extended (§2.7)
- registration: how a source announces itself, how the authority
  establishes what it is, and what domain it may speak for (§2.8 to
  §2.10)
- the relayed interrogation, and its relationship to PGSS Logon (§2.5,
  §2.12)
- assertion and refusal, the terminal messages of a source conversation
  (§2.13)
- querying a source outside a logon, so that an authority can serve
  PGSS Logon's identity lookup (§2.15, §2.16)
- what a source must declare about itself before an authority may cache
  its answers (§2.8, §2.17)
- scope: what a source may claim about identity, separately about
  membership, and separately again about POSIX identifiers (§2.18 to
  §2.20)
- the obligations binding on each role (§2.21)

This chapter does not cover:

- The logon protocol itself, specified in PGSS.
- Tokens, SIDs, sessions and privileges — described in the Peios Kernel
  TRM, with SIDs, security descriptors and claim attributes specified
  in PCDS.
- How a source stores identity, or verifies a credential.
- Derivation — what a token ends up containing — which is the
  authority's, applying local policy (PGSS §2.1).
- Which sources a machine trusts, and how that is configured.
- Which identifier range a source is given, and how that is configured.
  The *rules* the assignment must satisfy are §2.20.
- Administering a source's contents.

The third of those is the point of the whole interface. A source is
asked a question and gives an answer; how it reaches the answer is
exactly what different sources exist to do differently.

## PSI is not a conformance requirement

PGSS Logon is a Peios Generic System Standard: a system that does not
offer it is not Peios. **PSI is not.** It is the interface an authority
uses to reach the processes that know who exists, and a system running
entirely different authentication infrastructure is still Peios.

It is specified because it is a *public* interface even so. A third
party writing a principal source needs the contract written down, and
needs it to be stable. What it is not is a bar anyone must clear.

> [!NOTE]
> The distinction shows up in what happens when you disagree with each
> document. Disagreeing with PGSS Logon means shipping something that is
> not Peios. Disagreeing with this chapter means shipping an authority
> that federates differently, or does not federate at all, which is a
> design choice nobody will dispute.
