---
title: Prior Art
description: The event vocabularies this chapter learned from — Windows event logging and auditing, the Elastic Common Schema and OpenTelemetry's semantic conventions — and where it departs from each.
---

This appendix is informative.

## Windows event logging and auditing

Peios's access model is Windows's, and so is the shape of its audit:
SACLs with audit ACEs decide which accesses are recorded, and a token's
audit policy can force recording for one principal. Windows audit policy
also sits above SACLs, so that a category switched off suppresses even
records a SACL asks for. §6.9 keeps that relation for a gated event type
that is not essential, and drops it for the access audit itself, which
is essential so that a SACL alone decides (§6.8).

This chapter departs from Windows in its names. Windows identifies events
by numeric ID within a provider, and its payload fields are named per
event; the same value is `SubjectUserSid` in one event and `TargetSid`
in another. Here the name is the policy anchor, so every event type is
a dotted name and every value has one path.

## Elastic Common Schema

The Elastic Common Schema names fields by dotted, nested paths and
shares a field set across sources, so that one query finds a host or a
user wherever it appears. This chapter takes the same approach.

It departs in leading with the participant's role rather than its kind:
`subject.token.sid`, where the schema leads with the kind of thing. A
consumer searching for a principal in any role searches across roles
either way, and leading with the role makes `subject` a single policy
anchor for "may see who did it".

## OpenTelemetry semantic conventions

OpenTelemetry names attributes by dotted paths and keeps a registry of
them with stability levels, so that a name is defined once and
referenced everywhere. The catalogue of §6.10 plays the registry's part,
and its rule that no path is defined twice is the same discipline,
checked mechanically.

It departs in fixing the type and wire form of every value, rather than
leaving encoding to each exporter, because the event stream is consumed
directly and a SID or a time written two ways is two values to every
query.
