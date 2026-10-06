---
title: "kacs.session.destroyed"
description: "The record that a logon session ended because its last token went away."
---

- **Event type:** `kacs.session.destroyed`
- **Defined in:** `kacs.evman`
- **Tier:** essential
- **Gating:** none — every logon session that ends is recorded
- **Cardinality:** one record per occurrence

The record that a logon session ended because its last token went away.
KACS destroys a session once no token refers to it, or once the only
tokens left are its own linked elevated and filtered pair with nothing else
holding them, and writes this record as it does.

A session that never acquired a token ends another way: a holder of
SeTcbPrivilege destroys it explicitly with `kacs_destroy_empty_logon_session`,
and the same record is written.

**A session whose authentication package name is not valid UTF-8 produces
no record.** KACS cannot encode the name and skips the event rather than
write it, and the session is destroyed regardless.

**The record follows the teardown, written by a kernel worker.** A session
usually ends when a freed credential drops its last token, at a point where
the record cannot be built, so KACS queues it and a kernel work item writes
it moments later. Its header therefore names that kernel worker rather than
the process whose exit or revert ended the session, and it can arrive after
records that process wrote later.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`object.session.id`](~peios/events/field-index/fields-object#object.session.id) | `uint.luid` | required | The LUID of the logon session the operation acted on. |
| [`object.session.user.sid`](~peios/events/field-index/fields-object#object.session.user.sid) | `bin.sid` | required | The user SID of the principal the logon session belongs to: whose session it is. |
| [`object.session.logon-type`](~peios/events/field-index/fields-object#object.session.logon-type) | `str.enum` | required | What kind of logon the session represents, from the `KACS_LOGON_TYPE_*` values in `uapi/pkm/token.h`. |
| [`object.session.auth-package`](~peios/events/field-index/fields-object#object.session.auth-package) | `str` | required | The name of the authentication package that established the session, as the creator supplied it. |
| [`object.session.logon-time`](~peios/events/field-index/fields-object#object.session.logon-time) | `uint.time` | required | When the session was created. KACS keeps it to the second, so the nanosecond value is always a whole number of seconds. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `kacs.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
