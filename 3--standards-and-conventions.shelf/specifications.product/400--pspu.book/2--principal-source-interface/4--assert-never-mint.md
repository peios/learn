---
title: Assert, Never Mint
description: A source says who somebody is and nothing else — the structural reason a compromised source cannot grant itself privilege.
---

A source says **who somebody is**. It cannot say anything else, and the
protocol is built so that this is structural rather than a rule anyone
has to remember.

## The success terminal

PGSS Logon's success terminal is `AccessGranted`, carrying a session
identifier and a token descriptor. If PSI reused it, sources would be
minting sessions.

PSI's success terminal is `Assertion` (§2.13), which carries an
identity: a SID, a canonical name, and group memberships. **There is no
session identifier and no descriptor to attach a token to.** A source
could not mint one if it wanted to, because there is no message in which
to say so.

That is the whole of the mechanism. No capability check, no trust level,
no configuration flag — a source cannot mint because the protocol gives
it no way to express minting.

## What the authority keeps

Everything else:

- **Derivation.** What the token actually contains — its privileges, its
  integrity level, its derived group memberships, its projected
  identifiers — is the authority's, applying local policy (PGSS §2.1).
- **Session creation.** The logon session, and the record of which
  source vouched for it.
- **Validation.** Every SID a source sends is bytes until the authority
  has checked it (§2.13).
- **Scope enforcement.** What a source is permitted to claim (§2.18 to
  §2.20).
- **Peer verification.** On every connection it accepts.
- **Rate and round limits**, and the policing of what a source may ask a
  client for (§2.12).

## Why a compromised source is bounded

A source that is entirely compromised can lie about the principals in
its own domain. It cannot mint a token, cannot elevate anyone's
privileges, cannot claim identities outside its domain (§2.18), and —
unless configured otherwise — cannot assert memberships outside it
either (§2.19).

That bound is the reason for the process boundary. It is not that
sources are expected to be malicious; it is that a source is the
component parsing credentials from the outside world, and therefore the
one most likely to be wrong.
