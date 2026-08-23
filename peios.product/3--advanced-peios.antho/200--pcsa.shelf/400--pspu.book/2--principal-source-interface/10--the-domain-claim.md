---
title: The Domain Claim
description: A source declares the domain it is authoritative for — how the claim is checked, why domains must be disjoint, and what it does not prove.
---

A source declares the domain it is authoritative for. Every principal it
may assert lives under it (§2.18).

## It is a claim

A source generates or is given its own domain, so **nothing about the
SID can prove the claim is honest**. What gives it weight is entirely
what the authority does with it.

An authority MUST apply all of the following.

### 1. A domain MUST be declared

A source that declares no domain MUST be refused. There would be nothing
to confine its assertions to, which is the whole purpose of collecting
one.

> [!NOTE]
> The field is appended to a message that existed before it, so a source
> built against an older shape decodes as declaring *nothing* rather
> than as malformed. That is why the refusal is stated as its own rule:
> the diagnosis should name the real problem.

### 2. The shape MUST be checked

A domain MUST be a well-formed, locally-issued domain SID: revision 1,
the NT authority (`5`), the non-unique prefix `21`, and three further
sub-authorities — `S-1-5-21-A-B-C`, four sub-authorities in total.

The shape is the entire check, and it is enough. A source cannot claim
`S-1-5-32` (BUILTIN), or the NT authority's well-known range, or
`S-1-1-0`, because none of them has that shape. **There is no list of
forbidden domains to keep in step with the SID catalogue** — the
permitted shape excludes every one of them by construction.

### 3. Domains MUST be disjoint

No two concurrently registered sources may claim the same domain. Two
authorities for one namespace means whichever answers first decides who
a name belongs to, and the other's principals become impersonable by the
first.

### 4. A source MUST NOT change domain

A source that re-registers MUST declare what it declared before. An
authority MUST refuse a change.

This is the check that survives a source restarting, and it is worth its
cost: every other check passes for a source that is killed and comes
back compromised. It still holds the right service SID, its new domain
is still a claimable shape, and with itself deregistered there is
nothing left to collide with.

An authority MAY hold this record only for its own lifetime. Persisting
it means the authority writing state, which is a larger commitment than
the guarantee justifies.

### 5. An administrator MAY pin

An authority SHOULD allow an administrator to configure the exact domain
a named source must declare, and MUST refuse a source declaring anything
else when one is configured.

A configured pin that cannot be parsed MUST NOT be treated as absent.
Absence means *no pin*; an unparseable value means an administrator
tried to apply the control and got it wrong, and silently downgrading
that to "unconstrained" removes the control at the moment it was being
applied. An authority MUST fail towards refusing the source.

## What remains uncovered

With no pin configured, and another source not currently registered, a
compromised source could declare *that* source's domain and assert its
identities. Disjointness catches it only while both are registered.

This is stated rather than solved. Closing it requires someone to write
the pin down, and an authority cannot invent that authority for itself —
writing it automatically would mean the process holding the
token-minting privilege also holding a configuration write handle, which
is a worse trade than the gap it closes.
