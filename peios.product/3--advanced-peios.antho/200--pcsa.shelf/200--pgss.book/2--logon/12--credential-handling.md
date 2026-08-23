---
title: Credential Handling
description: The obligations that make plaintext on the wire defensible — bounded lifetime, zeroing, and what must never reach a log.
---

These bind both roles. They are stated normatively because plaintext on
the wire (§2.11) is only defensible if its lifetime is short.

## Bounding lifetime

An implementation MUST hold credential material in memory that is
**erased before it is released**, and the erasure MUST NOT be removable
by an optimising compiler.

The obligation extends to **the encoded message**, not only to the
credential field. A `CredentialResponse` holds the password just as much
as the answer inside it does, and a buffer wiped at one level while
another copy is dropped unerased achieves nothing.

An implementation MUST erase:

- the buffer credential material was read into;
- any buffer it was copied into during encoding or decoding, including
  an intermediate allocation abandoned by a buffer that grew;
- any structure holding it once the conversation reaches a terminal
  state.

The middle clause is the one an implementation is most likely to miss.
A growable buffer that reallocates while a message is being encoded
leaves a complete copy of everything written so far in the abandoned
allocation, and erasing the buffer that survives does not touch it.
Reserving the encoded size before writing avoids the problem entirely.

## What this does not promise

It guarantees that *these* buffers are erased before their memory is
reused. It cannot guarantee anything about copies made elsewhere — a
string the caller parsed a credential out of, a register or stack slot
the optimiser chose, a terminal's own input buffer. Those belong to
whoever made them.

Nor does it defend against a hostile kernel, a core dump, or swap. Those
are addressed elsewhere: process integrity protection, and disabling
core dumps for the authority.

## Logging and diagnostics

An implementation MUST NOT write credential material to a log, an audit
record, an error message, or a debugging aid.

A type carrying credential material SHOULD render, under whatever debug
formatting its language provides, as a redaction rather than as its
contents. A stray diagnostic print is the most common way material
escapes a process that was otherwise careful, and the defence is to make
the careless thing produce nothing useful.

## Collection

A client MUST collect a `Password` without echoing it. Where it cannot
establish that echo is suppressed, it MUST NOT collect the credential
anyway.

A client MUST NOT silently truncate an answer. `data` admits 32768 bytes
(§2.8); a client whose collection method admits fewer MUST fail the
conversation rather than send a prefix of what the principal supplied,
which would present as a wrong credential and leave the remainder in
whatever buffer it was read from.

## Timing

An authority MUST NOT allow the *time* it takes to reach a denial to
distinguish an unknown principal from a bad credential (§2.10).

This is more demanding than it looks with a memory-hard verifier,
because the natural implementation returns immediately when a principal
does not exist and spends tens of milliseconds when one does. An
authority MUST perform equivalent work in both cases — verifying against
a decoy verifier that no credential matches is the usual construction.

> [!NOTE]
> A decoy derived from randomness at start-up, rather than from a
> constant, is not merely unguessable but not stable between boots
> either. An implementation built this way runs exactly one verification
> on both paths, including for a principal that requires no credential
> at all.
