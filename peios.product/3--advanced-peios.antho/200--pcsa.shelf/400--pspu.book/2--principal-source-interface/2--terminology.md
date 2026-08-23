---
title: Terminology
description: Terms this chapter borrows unchanged from the Peios Kernel TRM, PCDS and PGSS Logon.
---

Terms defined in the Peios Kernel TRM (token, logon session, privilege),
in PCDS (SID, security descriptor, claim attribute) and in PGSS
(authority, client, principal, conversation, round, credential material,
prompt, derivation) are used here with the same meaning and are not
redefined.

**Source.** A process that is authoritative for some set of principals:
it verifies their credentials and says who they are. Called a *principal
source* in full.

**Registration.** The exchange in which a source announces itself and the
authority decides whether to accept it. Precedes any conversation.

**Domain.** The SID namespace a source is authoritative for. Every
principal a source may assert lives under it. See §2.10.

**Source conversation.** One logon's exchange between the authority and a
source, distinguished from other concurrent ones by a conversation
identifier. Not to be confused with a PGSS Logon conversation, which is
between a client and the authority; one of each exists per logon.

**Assertion.** A source's terminal message stating who a principal is.
The only successful outcome a source can produce.

**Originator.** The verified identity of the process that requested a
logon, as established by the authority from the client's connection.
Relayed to the source, which cannot learn it any other way.

**Service SID.** A SID derived from a service's name, placed in that
service's token by the init system, and unforgeable by anything else.
How a source's identity is established (§2.9).

**Membership scope.** The constraint on which groups a source may
assert. Separate from **identity scope**, which constrains whose
identity it may assert at all. Sections 2.18 to 2.20 exist because these
are different questions with different answers.

**Relative identifier.** In this chapter, a POSIX identifier as a source
states it: an offset within the range the authority assigned that
source, never an absolute number (§2.20). Where the SID sense is meant —
the last sub-authority of a SID — the text says so.
