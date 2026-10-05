---
title: Conformance
description: The obligations of the emitter, the consumer and the system, gathered in one place, and what conformance does not require.
---

## A conforming emitter

- Writes event types of at least three segments, kebab-case, ending in a
  past-tense verb, under a platform root listed against it or under its
  own package name (§6.3).
- Writes one event type per action, with the result in `outcome.*`, and
  carries `outcome.success` wherever the action can fail (§6.6).
- Encodes every path as nested maps, never as a key containing `.`, and
  writes only defined fields and the variants and standard attributes
  §6.4 permits (§6.4, §6.10).
- Writes nothing at a header path, and does not repeat a header value in
  its payload (§6.4, §6.5).
- Encodes each value in its type's wire form, omits a field that has no
  value, carries principals as SIDs without names, and writes no
  debugging output (§6.5).
- Carries `object.kind` wherever it carries an access mask (§6.5).
- Makes access decisions about objects it guards through the kernel's
  access check, passes the object's identity as the audit context, and
  writes no access-decision event of its own (§6.7).
- Keeps a stored descriptor's SACL intact and its store writable only by
  those trusted with audit policy (§6.7).
- Writes events, not log text, and declares each type's tier, choosing
  essential only for one of the two reasons of §6.8.
- Writes no event whose type the emission policy finds off, writes
  essential events without consulting it, notices a change to it, and
  falls back to tier defaults when it cannot read it (§6.9).
- Installs a fragment describing every event type it writes and every
  field it defines, which passes the rules of §6.10.

## A conforming consumer

- Exposes header values under the paths of §6.4.
- Does not treat an event type's root as evidence of who wrote it
  (§6.3), and does not present an asserted field as observed by the
  kernel (§6.7).
- Does not accept a value in a wire form other than its type's (§6.5).
- Treats an unknown value of an open enumeration as a value, not an
  error (§6.5).
- Reads the catalogue from every `.evman` file in `/usr/share/evman/` and
  no subdirectory, and treats a fragment breaking rule 1, 2 or 3 as
  defining nothing (§6.10).

## A conforming system

- Has the platform fragment at `/usr/share/evman/kernel.evman` (§6.10).
- Lets every emitter read `Machine\Generic\Events`, lets only
  administrators write it and the keys of platform roots, and SHOULD
  audit writes to it (§6.9).

## What conformance does not require

Conformance does not require an emitter to write any particular event,
to cache the emission policy, or to define fields beyond those it
writes. It does not require a consumer to store, index or query events,
to read the catalogue at all, or to resolve SIDs to names. It does not
require either role to know about any event type or field other than the
ones it writes or reads: an unknown event type is still an event, and an
unknown field is still a value at a path.
