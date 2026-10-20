---
title: Prior Art
description: Where PGSS Logon sits against Windows LSA, PAM and POSIX name resolution — and which resemblances are deliberate.
---

## Windows LSA

The closest predecessor is the Windows Local Security Authority and its
`LsaLogonUser` interface. What is taken and what is deliberately left is
worth stating, because the resemblance is close enough that the
differences matter.

**Taken.** The separation of *authentication* from *derivation* —
establishing who someone is, and then constructing a token for them, are
different acts by different rules. The idea that a logon produces both a
token and a session, and that the session records which authority
vouched for it. The vocabulary of logon types.

**Diverged.** LSA's authentication packages are DLLs loaded into the LSA
process, so a defect in any package is a defect in the most privileged
process on the system. Nothing in PGSS Logon admits an in-process
extension point; an authority that federates does so across a process
boundary of its own choosing.

**Rejected.** The challenge-response family (NTLM and successors).
Challenge-response requires the verifier to store something a response
can be recomputed from, which is password-equivalent material — the
pass-the-hash failure mode, where stealing the store is as good as
knowing the passwords. This chapter requires the opposite property: what
is stored MUST NOT be usable to authenticate. See §2.11.

## PAM

Pluggable Authentication Modules supplies the conversation shape: an
authority that asks for what it needs, a client that renders prompts
without understanding them, and several rounds where policy requires
them. That shape is why adding a credential type is a change to
authorities and not to every client, and it is adopted wholesale.

What is not adopted is PAM's stacking, in which a credential is offered
to each module in turn until one accepts. Trying each source *with the
password* hands every source the credentials of every other source's
users, including on typos. Where an authority federates, resolution MUST
select the answering party before any credential is collected.

PAM is also an in-process module system, and the objection under
*Diverged* applies to it equally.

## POSIX name resolution

The identity-lookup half of this chapter answers the questions
`getpwnam`, `getpwuid`, `getgrnam`, `getgrgid` and `getgrouplist` ask,
and its field mask, reference encoding and one-round-trip requirement
are shaped by what those calls need in one go.

What is not adopted is the `passwd` record itself. GECOS is not carried
(§2.9), the flat `name:uid:gid` tuple is replaced by a SID plus a set of
requested fields, and the reserved-character rules (§2.15) exist
precisely because a name that reaches those callers ends up in a
colon-and-comma-separated line that nothing else validates.

Nor is the assumption that an absence is authoritative. A world-readable
file cannot be unreachable, so POSIX has no vocabulary for "the source
that would have known did not answer"; §2.18 exists because a federated
authority does, and reporting that as "no such user" memoises an outage
as a fact.

## Design influences

**Descriptor-passing over ambient authority.** The token is transferred
as a file descriptor rather than named, so that possession of the
conversation is what confers it. There is no window in which a minted
token exists under a name another process could reach for.

**One conversation per connection.** The connection *is* the
conversation's identity, so no correlation identifier exists to be
forged or confused. This is deliberately unlike the identity channel of
§2.14, and unlike PSI (PSPU §2.7), both of which multiplex because
their connections are long-lived.

**Capability declaration over negotiation.** A client states what it can
render and the authority works within it, rather than the two agreeing a
version or a profile. That is what lets a credential type be added to
authorities without a flag day, and it is why the capability list is the
one enumeration whose unknown values are dropped rather than refused
(§2.7).
