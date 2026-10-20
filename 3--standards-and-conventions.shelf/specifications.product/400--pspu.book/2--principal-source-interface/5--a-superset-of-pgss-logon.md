---
title: A Superset of PGSS Logon
description: A source is an authority for its own slice of the world, which is why most of PSI is PGSS Logon — and where the two deliberately diverge.
---

A principal source *is* an authentication authority for its slice of the
world. The authority that federates is an authority over authorities.
Once that is seen, most of PSI writes itself.

## The relationship

PSI's interrogation phase is **PGSS Logon's, with identical message
bodies**. `CredentialRequest` and `CredentialResponse` carry exactly the
bytes PGSS §2.8 defines, and the authority relays them nearly verbatim
in both directions.

The consequences are worth stating plainly:

- **The source decides what to ask for.** Not the authority. The
  authority does not know what credentials a source requires, and does
  not need to.
- **The authority becomes a relay** in the interrogation phase. It is a
  shorter path than synthesising its own prompts, not a longer one.
- **Adding a credential type is a change to sources**, not to the
  authority and not to clients, which already render what they are given
  (PGSS §2.3).
- **A source could be tested in isolation** by pointing a PGSS Logon
  client at it, for the interrogation phase at least.

## Where they diverge, deliberately

Three differences, each for a stated reason.

**The success terminal.** `Assertion` rather than `AccessGranted`, so
that a source cannot mint. See §2.4. This is the divergence that
matters.

**Multiplexing.** PGSS Logon is one conversation per connection; the
connection *is* the conversation. PSI carries many concurrent logons
over one long-lived connection, so its header adds a conversation
identifier (§2.7). The alternative — serialising every logon behind one
connection — would make any slow logon a system-wide login stall.

**Distinct magic.** `PPSI` rather than `PGSL`. Two protocols this
similar sharing a codec is a cross-protocol hazard: a socket plugged
into the wrong daemon would *partially* work, which is far worse than
failing outright. The magic makes it a hard error on byte zero.

The full accounting of what is shared, what is added and what differs is
§2.C.

## "Just relaying" is loose

The authority is a relay in the interrogation phase only, and even there
it is not passive. It polices what a source may ask a client for
(§2.12), it validates what a source asserts (§2.13), and it enforces
scope (§2.18 to §2.20). Everything before and after the interrogation is
entirely its own.
