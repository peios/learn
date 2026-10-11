---
title: "peipkg.claim.changed"
description: "The record that peipkg granted a role to a package or revoked it, or tried to and failed."
---

- **Event type:** `peipkg.claim.changed`
- **Defined in:** `peipkg.evman`
- **Tier:** standard
- **Gating:** none
- **Cardinality:** once per claim grant or revoke

The record that peipkg granted a role to a package or revoked it, or tried
to and failed. A grant names the new holder; a revoke leaves
`object.claim.holder` out. A change the operator declines at the proceed
prompt writes nothing.

Replaces `peipkg.claim`.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`subject.token.sid`](~peios/events/field-index/fields-subject#subject.token.sid) | `bin.sid` | required | The user SID of the effective token the operation ran under. |
| [`transaction.id`](~peios/events/field-index/fields-transaction#transaction.id) | `uint` | optional | The transaction the operation belonged to, registry or package. |
| [`object.claim.role`](~peios/events/field-index/fields-object#object.claim.role) | `str` | required | The role a claim event changed the holder of. |
| [`object.claim.holder`](~peios/events/field-index/fields-object#object.claim.holder) | `str` | optional | The package that holds `object.claim.role` after the event, by name. |
| [`outcome.success`](~peios/events/field-index/fields-outcome#outcome.success) | `bool` | required | Whether the operation succeeded. |
| [`outcome.reason`](~peios/events/field-index/fields-outcome#outcome.reason) | `str.enum` | when `outcome.success == false` | Why the operation resolved the way it did.<br><br>Values here (open set): `stale` · `busy` · `denied` · `unowned` · `alternate-upgrade` · `unresolvable` · `untrusted` · `failed`. |
| [`outcome.detail`](~peios/events/field-index/fields-outcome#outcome.detail) | `str` | optional | Free text about the outcome, for a person to read. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `peipkg.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
