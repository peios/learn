---
title: Extension
description: There is no version number on any of the three interfaces — so unknown fields are ignored, unknown values are refused, and only some things may change.
---

There is no version number on any of the three interfaces. No datagram
carries one, no query message carries one, and there is no exchange in
which either party could state or discover what the other speaks.

That is a deliberate consequence of the shapes chosen, and it is worth
being explicit about, because it means every rule below is the *only*
mechanism available.

Ingestion is one-way over a datagram socket: there is no reply in which
a collector could announce a version and no state in which a producer
could remember one. The query channel could carry a version — it is a
stream, and it has a request message — and does not, because a version
field is only useful if a party may then behave differently, and a
client cannot usefully vary: it either asks a question the collector
understands or does not.

What replaces negotiation is a set of rules under which both sides may
change without either being told.

## Unknown fields are ignored

A collector MUST ignore fields it does not recognise in a log record
(§3.7), in a metric record (§3.11), and in a query request (§3.15).

This is what allows a field to be added. A producer built against a
later revision may send a field this collector has never heard of, and
the record is still stored; a producer built against an earlier one
omits a field that has since been added, and the record is still stored
because everything added is optional.

A field added to any of these three maps MUST therefore be optional, and
a collector MUST NOT require one to be present.

## Unknown values are refused, not ignored

The rule does **not** extend to values.

An unrecognised `type` in a metric record discards the record (§3.12); a
first token that is not a mode fails the query (§3.18); an unrecognised
keyword is a parse error. A collector MUST NOT guess at an unrecognised
value, and MUST NOT skip a field it recognised but could not interpret.

The asymmetry is the point. An unknown field is something the sender
knows about and this collector does not, and ignoring it loses only what
was never understood. An unknown *value* in a known field is the sender
saying something specific about this record, and proceeding without
understanding it stores something other than what was sent.

## Response statuses

A client MUST treat a response whose `status` it does not recognise as
an error terminating the query, and MUST discard the `"ok"` messages it
has received for that query unless `"end"` or `"watch"` had already
arrived (§3.16).

A status is the control flow of the response stream, so there is no
ignoring one: a client that skipped an unknown status would be waiting
for a terminal message that had already been sent, or treating an
incomplete result as complete. Failing is the only safe reading.

A collector MUST NOT introduce a new status for a condition that the
four existing ones can express.

## What may change without notice

- **New optional fields** in a log record, a metric record or a query
  request.
- **New fields in result records.** A client MUST tolerate a key it does
  not recognise, and MUST NOT reject a record for carrying one.
- **New query keywords, clauses and functions.** A client sending one
  the collector does not know receives a parse error, which is the
  correct answer.
- **Wording of any error string** (§3.16).
- **New event types, log origins and metric names.** These are data, not
  interface; nothing enumerates the valid set of any of them.

## What may not change

- **The meaning of an existing field**, in either direction. A field is
  added or it is left alone.
- **The type of an existing field.**
- **The four response statuses**, or the rule that exactly one terminal
  message ends a query.
- **The framing** of §3.15, which has no version field and therefore no
  way to change compatibly.
- **A required field becoming optional, or an optional one becoming
  required.**

## Limits are not the interface

The declared bounds — the datagram ceilings (§3.6, §3.9), the query
message ceiling (§3.15), the concurrency and timeout bounds (§3.14,
§3.16), the existence window and lookback limit (§3.26) — are
configuration, and an administrator may change any of them.

A collector MUST behave identically at any value in its supported range.
A producer or client MUST NOT infer a bound from having exceeded one, or
from not having exceeded one, and MUST NOT depend on the mainline
defaults quoted in this chapter.

The one place this bites is the log and metric datagram ceilings, which
a producer cannot discover and which silently discard what exceeds them
(§3.6). Lowering either is a change to the contract with every producer
on the system, and there is no mechanism by which any of them will find
out.
