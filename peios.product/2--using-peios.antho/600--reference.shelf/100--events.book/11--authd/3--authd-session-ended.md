---
title: "authd.session.ended"
description: "The record that authd ended a logon session at someone's request, by ending every process whose primary token belongs to it (PGSS Logon §2.22)."
---

- **Event type:** `authd.session.ended`
- **Defined in:** `authd.evman`
- **Tier:** essential
- **Gating:** none — every session end authd carries out is recorded; a refused request and a query are not
- **Cardinality:** once per `SessionEnd` authd acts on

The record that authd ended a logon session at someone's request, by
ending every process whose primary token belongs to it (PGSS Logon
<span>§</span>2.22). The kernel destroys the session when the last reference drops,
and records that as `kacs.session.destroyed`; this record adds who asked,
which the kernel cannot know.

A refusal is not recorded here. Who may end another principal's session is
decided by an access check against the `SessionEndSecurity` descriptor,
which KACS records as `kacs.audit.access.checked` with `object.kind`
`authd-session-end` when the descriptor's SACL asks it to.

Essential because ending somebody's session is rare and is an
administrative act on another principal.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`subject.token.sid`](~peios/events/field-index/fields-subject#subject.token.sid) | `bin.sid` | required | The principal that asked: themselves, signing out, or someone the descriptor permits to end other principals' sessions. |
| [`object.session.id`](~peios/events/field-index/fields-object#object.session.id) | `uint.luid` | required | The LUID of the logon session the operation acted on. |
| [`object.session.user.sid`](~peios/events/field-index/fields-object#object.session.user.sid) | `bin.sid` | required | Whose session it was. |
| [`object.session.logon-type`](~peios/events/field-index/fields-object#object.session.logon-type) | `str.enum` | required | What kind of logon the session represents, from the `KACS_LOGON_TYPE_*` values in `uapi/pkm/token.h`. |
| [`outcome.success`](~peios/events/field-index/fields-outcome#outcome.success) | `bool` | required | True when no process was left holding the session. |
| [`outcome.reason`](~peios/events/field-index/fields-outcome#outcome.reason) | `str.enum` | when `outcome.success == false` | Some processes survived every round, or could not be examined. The session lives on until they exit.<br><br>Values here (open set): `processes-remaining`. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `authd.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
