---
title: "authd.logon.attempted"
description: "The record that something asked authd to sign a principal in, and whether it did."
---

- **Event type:** `authd.logon.attempted`
- **Defined in:** `authd.evman`
- **Tier:** essential
- **Gating:** none — every logon that reaches a principal source's question, or is refused before one, is recorded
- **Cardinality:** once per `LogonStart` authd reads; a connection that opens with anything else writes none

The record that something asked authd to sign a principal in, and whether
it did. Written once per logon conversation, when it ends: with a token
minted and handed over, or with the denial authd sent the originator.
Success and failure are one type, so "every failed logon" is one query.

**The principal's name is never recorded.** On a failure authd does not
know who was signing in: a principal source answers "authentication
failed" alike for a name it does not hold and for a wrong credential, and
the name the originator sent is the caller's input, not an identity. The
source's own record, such as `lpsd.credential.verified`, says what the
wire hides. On a success the principal is `subject.token.sid`.

Essential because a logon is the most important thing an operating system
records about who uses it, and a machine signs people in rarely enough for
every attempt to be kept.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`source.token.sid`](~peios/events/field-index/fields-source#source.token.sid) | `bin.sid` | required | The originator: the principal of the process on the other end of `/run/logon.sock` that asked for the logon. |
| [`source.address`](~peios/events/field-index/fields-source#source.address) | `str.ip` | optional | The remote peer the originator says the logon is for, where it named one and it is an IP address. It is the originator's word, as `login -h` or sshd passes it; a host name is not recorded. |
| [`object.session.logon-type`](~peios/events/field-index/fields-object#object.session.logon-type) | `str.enum` | required | The logon type the originator asked for, whether or not it was granted. |
| [`object.session.auth-package`](~peios/events/field-index/fields-object#object.session.auth-package) | `str` | optional | The principal source authd asked to verify the credential. Absent when the logon was refused before a source was chosen. |
| [`subject.token.sid`](~peios/events/field-index/fields-subject#subject.token.sid) | `bin.sid` | when `outcome.success == true` | The principal signed in: the user SID of the token minted. |
| [`object.session.id`](~peios/events/field-index/fields-object#object.session.id) | `uint.luid` | optional | The logon session created for the sign-on. Every record of what the principal does in it carries the same value as `subject.token.auth-id`. Present whenever a token was minted: on a success, and on an `undelivered` failure. |
| [`object.token.id`](~peios/events/field-index/fields-object#object.token.id) | `uint.luid` | optional | The token minted for the originator, present exactly when `object.session.id` is. |
| [`outcome.success`](~peios/events/field-index/fields-outcome#outcome.success) | `bool` | required | True only when the token reached the originator. |
| [`outcome.reason`](~peios/events/field-index/fields-outcome#outcome.reason) | `str.enum` | when `outcome.success == false` | The denial authd sent the originator, in kebab-case, whether authd decided it or relayed it from the source; `authentication-failed` covers an unknown principal and a wrong credential alike. `abandoned` is a conversation that ended without a terminal answer, because the originator's or the source's connection failed. `undelivered` is a token minted that could not be handed over; its session is reaped once nothing holds it.<br><br>Values here (open set): `malformed-request` · `unsupported-version` · `permission-denied` · `authentication-failed` · `logon-type-not-permitted` · `account-restricted` · `authority-unavailable` · `conversation-limit` · `internal` · `abandoned` · `undelivered`. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `authd.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
