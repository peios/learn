---
title: "authd.service.attested"
description: "The record that the service manager asked authd for a service's token, with no credential behind it, and whether authd minted one."
---

- **Event type:** `authd.service.attested`
- **Defined in:** `authd.evman`
- **Tier:** standard
- **Gating:** none — every service attestation that names a service is recorded
- **Cardinality:** once per `ServiceAttest` authd reads

The record that the service manager asked authd for a service's token,
with no credential behind it, and whether authd minted one. The service
manager is PID 1 running as SYSTEM, and authd takes the service name on its
word, because the process the token is for does not exist yet (PGSS Logon
<span>§</span>2.19).

Standard rather than essential because every service with an identity
other than SYSTEM is attested on every start, so a machine writes these
in proportion to its service restarts.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`subject.token.sid`](~peios/events/field-index/fields-subject#subject.token.sid) | `bin.sid` | required | The principal that asked: the user SID of the peer's token, SYSTEM for the service manager. |
| [`object.service.name`](~peios/events/field-index/fields-object#object.service.name) | `str` | optional | The service the token is for, as the service manager named it. Absent only when the request named no service. |
| [`object.token.sid`](~peios/events/field-index/fields-object#object.token.sid) | `bin.sid` | optional | The identity attested: the service's virtual account, a built-in service identity such as LocalService, or a principal designated for service logon. Present whenever a token was minted: on a success, and on an `undelivered` failure. |
| [`object.session.id`](~peios/events/field-index/fields-object#object.session.id) | `uint.luid` | optional | The logon session created for the service, present exactly when `object.token.sid` is. |
| [`object.token.id`](~peios/events/field-index/fields-object#object.token.id) | `uint.luid` | optional | The token minted, present exactly when `object.token.sid` is. |
| [`object.token.privileges`](~peios/events/field-index/fields-object#object.token.privileges) | `uint.flags` | optional | The privileges local policy granted the token, all of them enabled. Present exactly when `object.token.sid` is. |
| [`outcome.success`](~peios/events/field-index/fields-outcome#outcome.success) | `bool` | required | True only when the token reached the service manager. |
| [`outcome.reason`](~peios/events/field-index/fields-outcome#outcome.reason) | `str.enum` | when `outcome.success == false` | The denial authd sent. `permission-denied` is a peer that is not the service manager; `account-restricted` an identity no source holds, or one not designated for service logon, which authd does not tell apart; `undelivered` a token minted that could not be handed over.<br><br>Values here (open set): `permission-denied` · `malformed-request` · `account-restricted` · `internal` · `undelivered`. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `authd.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
