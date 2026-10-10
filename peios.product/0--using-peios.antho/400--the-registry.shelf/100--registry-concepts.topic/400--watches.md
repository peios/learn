---
title: Watching for changes
type: how-to
description: Observe registry changes with reg watch, re-read after notifications or interruptions, and verify the consumer separately.
related:
  - peios/registry-concepts/configuration-and-meaning
  - peios/registry-layers/layers
  - peios/registry-administration/bootstrap-and-self-configuration
  - peios/registry-security/access-control
  - peios/registry-concepts/overview
---

Use a watch to notice that configuration changed. Use a fresh read to
learn the current state, and the consuming component's status and events
to learn whether it accepted that state.

## Watch a key from a terminal

```sh
reg watch Machine/System/KMES --subtree --filter value
```

This remains running until interrupted. `--subtree` includes descendant
keys; omit it for only the named key. The filters are `value`, `subkey`
and `sd`, as a comma-separated list; the default is all three. `--count N`
limits the run to N events. See [`reg watch`](~peios/registry-tools/reg#reg-watch-key).

Arming a watch requires `KEY_NOTIFY`. Reading values separately requires
`KEY_QUERY_VALUE`; a watch is not permission to read everything beneath it.

## Read after a notification

`reg watch` reports that something under its filter changed. It does not
decode the detailed change records. In another terminal, inspect the
current state:

```sh
reg get Machine/System/KMES
reg get Machine/System/KMES BufferCapacity -L
```

Watches describe effective-state changes, not a history of every layer
write. A write hidden by another layer need not change the effective
answer. Layer operations may require a full re-read rather than provide
one notification for every affected value.

## A notification is not consumer acceptance

Uncommitted transaction changes are not published to watchers. A
committed change can notify a consumer, but the consumer still has to
read, validate and apply it. Follow [Change a setting and verify it](~peios/registry-concepts/configuration-and-meaning)
instead of treating a watch line as confirmation that the service changed.

## Recover after missed events

Watch delivery is best-effort, with bounded queues. An overflow means the
record is incomplete; re-read the key and, for a subtree watch, its subtree.
Restore, layer deletion and a source re-registration can also trigger
this recovery path. A watch is not a backup or a complete change journal.

After a source outage, wait for reads to work again and resynchronise
from current values. After restarting `reg watch`, take a fresh read
rather than assume the new stream includes changes made while it was stopped.

## When the same path names a different key

A watch follows the key object opened at registration, not the path text.
If another key replaces it at the same path, the old watch does not move
to the replacement. Reopen the path and arm a new watch when you need to
observe the replacement. Merely hiding a key does not destroy its watch;
the object and path distinction is explained in the
[LCS watch dispatch reference](~peios/lcs/watches/dispatch).

## Where to go next

- [Access rights for watching and reading](~peios/registry-security/access-control)
- [Source interruptions and safe retry](~peios/registry-administration/lcs-and-sources#when-a-source-goes-away)
- [LCS watch model](~peios/lcs/watches/the-model),
  [record layout](~peios/lcs/watches/event-records), and
  [queue behavior](~peios/lcs/watches/queues-and-overflow) for client implementers
