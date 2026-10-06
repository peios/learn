---
title: "peipkg.action.authorised"
description: "The record that the operator was asked to authorise an elevated action specifically, apart from the routine proceed prompt, and what they answered."
---

- **Event type:** `peipkg.action.authorised`
- **Defined in:** `peipkg.evman`
- **Tier:** essential
- **Gating:** none — every authorisation is recorded
- **Cardinality:** once per elevated action put to the operator, and once per stale repository proceeded with

The record that the operator was asked to authorise an elevated action
specifically, apart from the routine proceed prompt, and what they answered.
`outcome.success` false means they declined. The routine prompt and its
`--yes` never answer one of these. Asked about several actions, the
operator answers them in turn, and the first refusal ends the questions.

`stale-trust-state` and `stale-index` are answered by `--allow-stale`
rather than a prompt, so they are only ever recorded as authorised: without
the flag the command fails instead, and writes no record of this type.

Replaces `peipkg.authorisation`.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`subject.token.sid`](~peios/events/field-index/fields-subject#subject.token.sid) | `bin.sid` | required | The user SID of the effective token the operation ran under. |
| [`operation.name`](~peios/events/field-index/fields-operation#operation.name) | `str.enum` | required | Which elevated action was put to the operator.<br><br>Values here (open set): `low-trust-provides` · `foreign-replaces` · `downgrade` · `remove-modified-file` · `stale-trust-state` · `stale-index`. |
| [`object.package.name`](~peios/events/field-index/fields-object#object.package.name) | `str` | optional | The package the action concerns: the package substituted by `provides` for `low-trust-provides`, the successor for `foreign-replaces`, the package moving backward for `downgrade`, and the package being uninstalled for `remove-modified-file`. |
| [`object.file.path`](~peios/events/field-index/fields-object#object.file.path) | `str.path` | when `operation.name == remove-modified-file` | The modified file the uninstall would remove, as the package database records it: absolute within the root peipkg operated on. |
| [`object.repository.name`](~peios/events/field-index/fields-object#object.repository.name) | `str` | optional | The repository, for `stale-trust-state` and `stale-index`. |
| [`outcome.success`](~peios/events/field-index/fields-outcome#outcome.success) | `bool` | required | False when the operator declined. For `remove-modified-file`, keeping the file and aborting the transaction both decline the removal. |
| [`outcome.detail`](~peios/events/field-index/fields-outcome#outcome.detail) | `str` | optional | The action as it was put to the operator. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `peipkg.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
