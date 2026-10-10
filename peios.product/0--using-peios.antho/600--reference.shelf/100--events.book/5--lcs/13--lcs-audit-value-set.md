---
title: "lcs.audit.value.set"
description: "The record that a registry value was written through a key handle, or that an attempt to write one failed."
---

- **Event type:** `lcs.audit.value.set`
- **Defined in:** `lcs.evman`
- **Tier:** essential
- **Gating:** KEY_SET_VALUE overlaps the alarm mask cached on the key handle
- **Cardinality:** once per write through a handle whose mask covers it

The record that a registry value was written through a key handle, or that
an attempt to write one failed. The key's `SYSTEM_ALARM` ACEs configure it:
the ACEs that match the caller when the key is opened give the handle a
continuous-audit mask, and every later write whose right overlaps the mask
is recorded, as `kacs.audit.handle.used` does for files.

**The mask is fixed when the key is opened.** Removing the alarm ACE does
not silence a handle already open, so the write that removes it is still
recorded; equally, adding one does not reach handles opened before.

**A transacted write is recorded when it is staged, not when it lands.**
`outcome.success` then means the source accepted it into the transaction;
whether the transaction took effect is the matching
`lcs.audit.transaction.committed`, joined on `transaction.id`.

**A timed-out write may have been applied later.** The source is not told
to cancel, and when its reply arrives the kernel still applies the write's
effects, with nothing recording who made it. Such a record says
`outcome.success` false with `request.timed-out` true: read it as "may
have been applied".

The data itself is never recorded, only its type, length and SHA-256
digest, with the same three for the value it replaced.

## Fields

| Field | Type | Presence | Meaning |
|---|---|---|---|
| [`subject.token.sid`](~peios/events/field-index/fields-subject#subject.token.sid) | `bin.sid` | via [`caller`](~peios/events/groups/group-caller) | The user SID of the effective token the operation ran under. |
| [`subject.token.integrity`](~peios/events/field-index/fields-subject#subject.token.integrity) | `uint.integrity` | via [`caller`](~peios/events/groups/group-caller) | The integrity RID of the effective token. |
| [`subject.token.id`](~peios/events/field-index/fields-subject#subject.token.id) | `uint.luid` | via [`caller`](~peios/events/groups/group-caller) | The token's own LUID, identifying this specific token rather than the logon session it belongs to. |
| [`subject.token.auth-id`](~peios/events/field-index/fields-subject#subject.token.auth-id) | `uint.luid` | via [`caller`](~peios/events/groups/group-caller) | The LUID of the logon session the effective token belongs to. |
| [`subject.token.type`](~peios/events/field-index/fields-subject#subject.token.type) | `str.enum` | via [`caller`](~peios/events/groups/group-caller) | Whether the effective token is a primary token or an impersonation token. |
| [`subject.token.impersonation`](~peios/events/field-index/fields-subject#subject.token.impersonation) | `uint.enum` | via [`caller`](~peios/events/groups/group-caller) | The impersonation level of the effective token. |
| [`object.kind`](~peios/events/field-index/fields-object#object.kind) | `str.enum` | required | Always `key`. |
| [`object.key.guid`](~peios/events/field-index/fields-object#object.key.guid) | `bin.guid` | required | The registry key an operation acted on. |
| [`object.key.path`](~peios/events/field-index/fields-object#object.key.path) | `str` | required | The resolved absolute path of the registry key, in canonical form, such as `Machine\System\KMES`. |
| [`object.key.layer.name`](~peios/events/field-index/fields-object#object.key.layer.name) | `str` | optional | The layer written, `base` when the caller named none. Absent only when the request failed before its layer was read. |
| [`object.key.value.name`](~peios/events/field-index/fields-object#object.key.value.name) | `str` | optional | Absent only when the request failed before its name was read. |
| [`object.key.value.type`](~peios/events/field-index/fields-object#object.key.value.type) | `uint.enum` | optional | The type written. Present once the data was read from the caller. |
| [`object.key.value.length`](~peios/events/field-index/fields-object#object.key.value.length) | `uint.bytes` | optional | Present with `object.key.value.type`. |
| [`object.key.value.digest`](~peios/events/field-index/fields-object#object.key.value.digest) | `bin` | optional | Present with `object.key.value.type`. |
| [`object.key.value.type-previous`](~peios/events/field-index/fields-object#object.key.value.type-previous) | `uint.enum` | optional | The effective value before the write. Only on a write outside a transaction that found one: a transacted write never reads it. |
| [`object.key.value.length-previous`](~peios/events/field-index/fields-object#object.key.value.length-previous) | `uint.bytes` | optional | Present with `object.key.value.type-previous`. |
| [`object.key.value.digest-previous`](~peios/events/field-index/fields-object#object.key.value.digest-previous) | `bin` | optional | Present with `object.key.value.type-previous`. |
| [`access.requested`](~peios/events/field-index/fields-access#access.requested) | `uint.mask` | required | Always `KEY_SET_VALUE`. |
| [`access.granted`](~peios/events/field-index/fields-access#access.granted) | `uint.mask` | required | What the handle was opened with. |
| [`access.matched`](~peios/events/field-index/fields-access#access.matched) | `uint.mask` | required | The subset of the requested access that overlapped an audit mask and therefore caused the record to exist. |
| [`access.audit-mask`](~peios/events/field-index/fields-access#access.audit-mask) | `uint.mask` | required | The full continuous-audit mask cached on a handle, of which `access.matched` is the part this operation touched. |
| [`mutation.sequence`](~peios/events/field-index/fields-mutation#mutation.sequence) | `uint` | optional | The sequence stamped on the write. Absent only when the request failed before one was allocated. |
| [`mutation.sequence-expected`](~peios/events/field-index/fields-mutation#mutation.sequence-expected) | `uint` | optional | Present on a compare-and-swap write. |
| [`transaction.id`](~peios/events/field-index/fields-transaction#transaction.id) | `uint` | optional | Present when the write was staged in a transaction. |
| [`request.timed-out`](~peios/events/field-index/fields-request#request.timed-out) | `bool` | when `outcome.success == false` | True when the source did not answer in time, so the write may have been applied after all. |
| [`outcome.success`](~peios/events/field-index/fields-outcome#outcome.success) | `bool` | required | Whether the operation succeeded. |
| [`outcome.errno`](~peios/events/field-index/fields-outcome#outcome.errno) | `int.errno` | when `outcome.success == false` | The error the operation failed with, as a negative errno. |

Every record also carries the header fields of [the envelope](~peios/events/introduction/the-envelope), which no payload repeats.

*Generated from `lcs.evman` by `pkm/tools/gen-events-book.py`. Edit the fragment, not this page.*
