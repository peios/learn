---
title: "peipkg.repository.added"
description: "The record that peipkg added a repository and established trust in it, or tried to and failed."
---

- **Event type:** `peipkg.repository.added`
- **Defined in:** `peipkg.evman`
- **Tier:** essential
- **Gating:** none — every repository trust ceremony is recorded
- **Cardinality:** once per repository add

The record that peipkg added a repository and established trust in it, or
tried to and failed. Adding a repository decides whose packages the system
will install, which is why it is essential. A command refused before it
names a base URL, such as `repo add <name>` for a repository with no
configuration, writes nothing.

Replaces `peipkg.repo-add`.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`subject.token.sid`](~peios/events/field-index/fields-subject#subject.token.sid) | `bin.sid` | required | The user SID of the effective token the operation ran under. |
| [`object.repository.name`](~peios/events/field-index/fields-object#object.repository.name) | `str` | required | The repository the event is about, by the name it is configured under. |
| [`object.repository.url`](~peios/events/field-index/fields-object#object.repository.url) | `str` | required | The base URL of the repository the event is about, which is what identifies it (PSPU <span>§</span>5.36). |
| [`outcome.success`](~peios/events/field-index/fields-outcome#outcome.success) | `bool` | required | Whether the operation succeeded. |
| [`outcome.reason`](~peios/events/field-index/fields-outcome#outcome.reason) | `str.enum` | when `outcome.success == false` | Why the operation resolved the way it did.<br><br>Values here (open set): `stale` · `busy` · `denied` · `unowned` · `alternate-upgrade` · `unresolvable` · `untrusted` · `failed`. |
| [`outcome.detail`](~peios/events/field-index/fields-outcome#outcome.detail) | `str` | optional | The error as peipkg reported it to the operator. Absent on success. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `peipkg.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
