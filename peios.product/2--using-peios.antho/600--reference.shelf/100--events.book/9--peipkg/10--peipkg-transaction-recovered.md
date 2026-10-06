---
title: "peipkg.transaction.recovered"
description: "The record that peipkg recover reconciled interrupted transactions, rolling back each one it found pending, or failed to."
---

- **Event type:** `peipkg.transaction.recovered`
- **Defined in:** `peipkg.evman`
- **Tier:** standard
- **Gating:** none
- **Cardinality:** once per run of peipkg recover

The record that `peipkg recover` reconciled interrupted transactions,
rolling back each one it found pending, or failed to. Every run writes it,
one that found nothing to recover included. An automatic recovery at the
start of an ordinary operation does not write it.

Replaces `peipkg.recovery`.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`subject.token.sid`](~peios/events/field-index/fields-subject#subject.token.sid) | `bin.sid` | required | The user SID of the effective token the operation ran under. |
| [`operation.succeeded-count`](~peios/events/field-index/fields-operation#operation.succeeded-count) | `uint` | required | Interrupted transactions rolled back, before the failure on a run that failed. Zero when there were none. |
| [`outcome.success`](~peios/events/field-index/fields-outcome#outcome.success) | `bool` | required | Whether the operation succeeded. |
| [`outcome.detail`](~peios/events/field-index/fields-outcome#outcome.detail) | `str` | optional | The error, on a run that failed. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `peipkg.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
