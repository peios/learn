---
title: "peipkg.repository.reconfigured"
description: "The record that a repository add changed one of an existing repository's trust-relevant settings."
---

- **Event type:** `peipkg.repository.reconfigured`
- **Defined in:** `peipkg.evman`
- **Tier:** essential
- **Gating:** none — every trust-relevant change is recorded
- **Cardinality:** once per changed setting

The record that a repository add changed one of an existing repository's
trust-relevant settings. One record for each setting that changed, written
after the add's own `peipkg.repository.added`. The settings are
`signature_policy`, `allow_insecure_transport`, `max_trusted_age_days`,
`min_index_version`, `max_index_staleness_days` and `trust_anchors`.

Only a change made through the flags of `repo add` is seen. An operator who
edits the repository file directly and re-runs the ceremony leaves nothing
to compare.

Replaces `peipkg.config-change`.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`subject.token.sid`](~peios/events/field-index/fields-subject#subject.token.sid) | `bin.sid` | required | The user SID of the effective token the operation ran under. |
| [`object.repository.name`](~peios/events/field-index/fields-object#object.repository.name) | `str` | required | The repository the event is about, by the name it is configured under. |
| [`config.name`](~peios/events/field-index/fields-config#config.name) | `str` | required | The setting's name as written in the repository file. |
| [`config.text`](~peios/events/field-index/fields-config#config.text) | `str` | when `config.name == signature_policy` | A setting's value in force, where the value is not an integer: a string, or the textual rendering of a value of another registry type. |
| [`config.text-previous`](~peios/events/field-index/fields-config#config.text-previous) | `str` | when `config.name == signature_policy` | The text value a change replaced, beside `config.text`. |
| [`config.value`](~peios/events/field-index/fields-config#config.value) | `uint` | optional | The setting in force, for every setting except `signature_policy`: a number of days or an index version as written, 0 for a setting left at its default; 1 or 0 for `allow_insecure_transport`; for `trust_anchors`, how many anchors are configured, so replacing one anchor with another records equal counts. |
| [`config.value-previous`](~peios/events/field-index/fields-config#config.value-previous) | `uint` | optional | The setting it replaced, in the same form as `config.value`. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `peipkg.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
