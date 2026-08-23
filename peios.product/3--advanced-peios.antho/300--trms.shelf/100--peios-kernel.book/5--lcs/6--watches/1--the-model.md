---
title: The Watch Model
description: A persistent subscription to changes on an open key, following inotify rather than the Windows model — what it observes, its event types and filters.
---

A watch is a persistent subscription to changes on an open key. It
follows the inotify model rather than the Windows one: once armed, it
stays armed until the fd closes, and events keep arriving without
re-registration. `RegNotifyChangeKeyValue` is single-shot, and the
window between receiving a notification and re-registering is a window
in which changes are missed; a persistent watch has no such window.

A watch is armed by `REG_IOC_NOTIFY` on a key fd, which requires
`KEY_NOTIFY` in the fd's granted mask. Arming takes a filter — a bitmask
of event categories — and a subtree flag. After arming, the fd is
pollable: `EPOLLIN` reports pending events, and `read()` returns
structured records.

Each fd carries at most one watch. Arming an already-armed fd replaces
the filter and the subtree setting and leaves queued events in place.
Arming with a filter of zero disarms: the watch is removed and every
pending event is discarded. To watch one key under two different
filters, open it twice.

Arming a watch on a key that is already orphaned fails with `ENOENT`. A
watch armed before the key was orphaned stays armed (§5.2.9).

## What a watch observes

Events describe changes to **effective** state, not to layer mechanics.
A watcher sees that a value changed; it does not see which layer won,
or that a layer was deleted. Removing a layer whose value was on top
produces `VALUE_SET` for the value that surfaced underneath. Removing a
hiding entry that was concealing a lower-precedence key produces
`SUBKEY_CREATED`. The layer system is not visible through a watch at
all.

The events are computed by diffing the effective state before the
mutation against the effective state after it, which is what makes this
true by construction rather than by careful case analysis. A change
that replaces the key at a child name with a different key object —
different GUID, same name — produces `SUBKEY_DELETED` followed by
`SUBKEY_CREATED`, because that is what the diff says happened.

Only committed state is observable. Operations inside an uncommitted
transaction produce nothing; the whole set fires at commit (§5.6.4).

## Event types

| Event | Code | Name field | Meaning |
|---|---|---|---|
| `REG_WATCH_VALUE_SET` | 1 | value name | The effective value at this name changed or appeared. |
| `REG_WATCH_VALUE_DELETED` | 2 | value name | The effective value at this name disappeared. |
| `REG_WATCH_SUBKEY_CREATED` | 3 | subkey name | A child key became visible. |
| `REG_WATCH_SUBKEY_DELETED` | 4 | subkey name | A child key became invisible. |
| `REG_WATCH_SD_CHANGED` | 5 | empty | The watched key's Security Descriptor was modified. |
| `REG_WATCH_KEY_DELETED` | 6 | empty | The watched key itself became invisible. |
| `REG_WATCH_OVERFLOW` | 7 | empty | Events were dropped; re-read to recover. |

`VALUE_SET` fires when a value is written, when a tombstone or blanket
tombstone is removed and a lower-precedence value surfaces, and when a
layer deletion makes a different value effective. `VALUE_DELETED` fires
when the last entry for a name goes away, when a tombstone masks every
entry, and when a blanket tombstone masks this name.

`SUBKEY_CREATED` and `SUBKEY_DELETED` cover both halves of the naming
model: a path entry appearing or being removed, and a hiding entry
being removed or created.

The three no-name events carry no name, and that is enforced: a record
constructed with a name for `SD_CHANGED`, `KEY_DELETED` or `OVERFLOW`
is rejected rather than emitted.

## Filters

The filter selects event *categories*, not individual event types.

| Filter bit | Value | Admits |
|---|---|---|
| `REG_NOTIFY_VALUE` | `0x01` | `VALUE_SET`, `VALUE_DELETED` |
| `REG_NOTIFY_SUBKEY` | `0x02` | `SUBKEY_CREATED`, `SUBKEY_DELETED` |
| `REG_NOTIFY_SD` | `0x04` | `SD_CHANGED` |
| `REG_NOTIFY_ALL` | `0x07` | all three of the above |

`KEY_DELETED` and `OVERFLOW` are delivered unconditionally. They are
not in any category and no filter suppresses them: the first tells a
watcher its key is gone, and the second tells it that what it has been
told is incomplete. Neither is something a watcher can usefully opt out
of.

A filter containing an undefined bit is rejected, as is a subtree flag
other than 0 or 1 or a non-zero padding byte in the argument structure.

## Blanket tombstones

A watcher never learns that a blanket tombstone exists. When one is
written, LCS works out which values it newly masks and emits one
`VALUE_DELETED` per name; when one is removed, one `VALUE_SET` per name
that became visible. The per-value view is the only view.
