---
title: Watch Model
---

The registry provides a change observation mechanism that allows
processes to watch for configuration changes and react to them.
Services like peinit watch their registry subtrees and respond to
changes rather than polling.

## Model

Watches follow the inotify model: persistent subscriptions with
best-effort event delivery and overflow fallback.

- **Persistent watches.** Once armed via REG_IOC_NOTIFY, a watch
  remains active until the fd is closed. Events keep flowing without
  re-arming. There is no single-shot behaviour. This is an
  intentional divergence from Windows' RegNotifyChangeKeyValue (see
  §1.4).

- **Best-effort change log.** Each event describes a specific change
  (what type, what name). Events are delivered in order. If events
  accumulate faster than the watcher reads them, the queue overflows.

- **Overflow fallback.** When the event queue fills, the oldest
  events are dropped and an OVERFLOW event is inserted. The watcher
  MUST do a full re-read of the watched key (and subtree, if
  applicable) to recover current state. Subsequent events after
  overflow continue normally.

- **Committed state only.** Operations within an uncommitted
  transaction do not generate events. Events fire at commit time.
  Watchers never see intermediate transactional states.

- **Effective state changes.** Events reflect changes to the
  effective (layer-resolved) state, not layer mechanics. A layer
  deletion that causes a value to revert generates a VALUE_SET
  event. A layer deletion that causes a key to reappear generates
  SUBKEY_CREATED. The layer system is transparent to watchers.

## Event types

| Type | Code | Name field | Meaning |
|---|---|---|---|
| VALUE_SET | 1 | Value name | The effective value at this name changed or appeared. Fired when: a value is written, a tombstone or blanket tombstone is removed (surfacing a lower-precedence value), or a layer deletion causes a different value to become effective. |
| VALUE_DELETED | 2 | Value name | The effective value at this name disappeared. Fired when: a value entry is removed with no lower-precedence entry to surface, a tombstone is written masking all entries, or a blanket tombstone is written masking this value. |
| SUBKEY_CREATED | 3 | Subkey name | A child key became visible (path entry created, or a HIDDEN entry was removed revealing a lower-precedence key). |
| SUBKEY_DELETED | 4 | Subkey name | A child key became invisible (path entry removed, or a HIDDEN entry was created masking it). |
| SD_CHANGED | 5 | (empty) | The watched key's Security Descriptor was modified. |
| KEY_DELETED | 6 | (empty) | The watched key itself became invisible (its path entry was removed or hidden). The fd remains valid but the key is no longer reachable by path. |
| OVERFLOW | 7 | (empty) | The event queue overflowed. Events were dropped. The watcher MUST do a full re-read to recover current state. |

### Blanket tombstone events

When a blanket tombstone is written, LCS determines which values
are newly masked and generates one VALUE_DELETED event per affected
value name. When a blanket tombstone is removed, LCS determines
which values are newly visible and generates one VALUE_SET event per
affected value name.

Watchers do not need to understand blanket tombstones. They see
per-value effective state changes.

### Layer operation events

When a layer is deleted, changes precedence, or is enabled/disabled,
LCS determines which keys and values have changed effective state
and generates the appropriate events. This may produce a large burst
of events -- the overflow mechanism handles this naturally.

LCS MUST detect and emit events for ALL effective state changes
caused by layer operations. A watch MUST observe every change to
the effective value of a watched key, regardless of whether the
change was caused by a direct write, a layer deletion, a precedence
change, or a blanket tombstone.

## Event format

Each event is a variable-length record read from the key fd via
read(). A single read() call returns as many complete events as fit
in the caller's buffer (matching inotify semantics). If the buffer
is too small for even one event, read() returns EINVAL. Events are
never split across read() calls. The format supports forward
compatibility -- a total length field allows consumers to skip
unknown trailing data added in future versions.

### Direct watch events

```
┌──────────────┬──────────────┬───────────────┬──────────────────┐
│ total_len    │ event_type   │ name_len      │ name             │
│ uint32       │ uint16       │ uint16        │ (variable, UTF-8)│
└──────────────┴──────────────┴───────────────┴──────────────────┘
```

- **total_len:** Total event size in bytes. Consumers advance by
  this amount to reach the next event.
- **event_type:** One of the defined event type codes.
- **name_len:** Length of the name field in bytes. Zero for events
  that carry no name (OVERFLOW, KEY_DELETED, SD_CHANGED).
- **name:** The name of the changed entity. For value events, the
  value name. For subkey events, the subkey name.

### Subtree watch events

Subtree watch events include additional fields after the name,
identifying the path from the watched key to the key where the
change occurred:

```
... name │ path_depth │ path_components              │
         │ uint16     │ (len:uint16 + UTF-8 bytes)...│
```

- **path_depth:** Number of path components from the watched key to
  the changed key. Zero means the change is on the watched key
  itself.
- **path_components:** A sequence of length-prefixed strings (uint16
  length + UTF-8 bytes), one per component from the watched key
  down to the changed key. No delimiter between components --
  length-prefixed encoding is unambiguous.

Length-prefixed components avoid delimiter ambiguity. Registry key
and value names can contain backslashes (value names) or any
Unicode character, so a single concatenated path string would be
unparseable.

Future versions MAY append additional fields after path_components.
Old consumers skip them via total_len. New consumers check
total_len to determine whether optional fields are present.

Exact byte layouts for event structures are defined in §11.2.
