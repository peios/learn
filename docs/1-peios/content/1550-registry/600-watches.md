---
title: Watching for changes
type: concept
description: The registry is not passive storage you poll — a process can arm a persistent watch on a key or its subtree and be notified when the effective state changes. This page covers the watch model, what watchers see (effective-state changes, with the layering invisible), and the best-effort delivery that means a watcher must be ready to re-read.
related:
  - peios/registry/configuration-and-meaning
  - peios/registry/layers
  - peios/registry/bootstrap-and-self-configuration
  - peios/registry/access-control
  - peios/registry/overview
---

Configuration changes while the system is running — an administrator edits a value, a role is installed, a policy is applied. A subsystem could poll the registry to notice, but Peios does not make it: the registry can **tell** a process when something it cares about changes. This is what lets services react to configuration instead of repeatedly re-reading it, and it is how the registry behaves as a live configuration backbone rather than a passive store.

## Watching, in one sentence

**A process arms a persistent watch on a key — optionally covering its whole subtree — and is notified whenever the effective state there changes, so it can react to configuration instead of polling for it.**

## Persistent, not single-shot

A watch is armed on an open key handle. Once armed, it stays armed until the handle is closed: events keep flowing, with no need to re-arm after each one. This matters because re-arming would open a race — a change slipping through in the gap between one notification and the next registration. There is no such gap here. The handle is also pollable: a process waits on it the same way it waits on any other file descriptor, and reads structured change records off it when they arrive.

A watch can cover just the one key, or the key **and its descendants** (a subtree watch), so a service can watch an entire configuration area with a single registration.

## What a watch reports

Events describe what changed, by kind:

| Event | Meaning |
|---|---|
| Value set | The effective value at a name changed or appeared. |
| Value deleted | The effective value at a name went away. |
| Subkey created / deleted | A child key became visible / became invisible. |
| SD changed | The watched key's security descriptor was modified. |
| Key deleted | The watched key itself is no longer reachable by path. |
| Overflow | Events were dropped — re-read to recover (below). |

## Watchers see effective state, not layers

Here is the important tie-back to [Layers](~peios/registry/layers). A watcher is told about changes to the **effective** value — the winner of the contest — and nothing about the machinery underneath. Delete a layer and cause a value to revert, and the watcher sees a plain "value set" event for its new effective value. Apply a higher-precedence policy that overrides a local setting, and the watcher sees the value change. It never sees "a layer was added" or "a write lost a contest" — only that the answer it would get from a read is now different.

This is exactly right: the layering is an implementation of *how* the effective value is chosen, and a watcher only cares *that* it changed. The curtain stays down; the watcher watches the front of it.

## Committed state only

Watch events fire when a change **commits**, never mid-flight. A [transaction](~peios/registry/lcs-and-sources) that writes many values produces its events as one batch at commit time; a watcher never observes a half-applied transaction, and an aborted one produces no events at all. What a watcher sees is always a state the system actually reached.

## Best-effort: be ready to re-read

A watch is a **change notification, not a guaranteed-complete journal.** Events are queued for the watcher, and the queue is bounded. If a watcher falls behind — events arriving faster than it reads them — the queue overflows: the oldest events are dropped and a single **overflow** marker is delivered in their place. The contract on overflow is simple and firm: *re-read the watched key (and subtree) to recover the current state*, then carry on with subsequent events.

So a correct watcher is written to do two things — apply individual events when it is keeping up, and fall back to a full re-read when it is told it fell behind. It never assumes the event stream is a complete edit history; it treats it as "something changed, here is a hint, and if the hint says you missed some, go look." The same overflow-and-re-read recovery covers the bigger disruptions too — a large layer operation, or the backing store restarting — where computing an exact per-change list is not worthwhile.

## The reaction loop

Put watches together with [reject-or-keep](~peios/registry/configuration-and-meaning) and you get the pattern that runs throughout Peios. A subsystem watches its own configuration subtree; when a value changes, the watch fires; the subsystem re-reads, re-validates, and either applies the new value or keeps its last known-good one and logs the rejection. KMES does this for its tuning; peinit does it for service definitions; the registry itself does it for its own parameters (see [How the registry boots and configures itself](~peios/registry/bootstrap-and-self-configuration)). Configuration is something you *react to*, and watches are the mechanism.

## One subtlety: a watch follows the object

A watch is bound to the specific key object you opened, not to the path string. If layers later cause a *different* key to appear at the same path, your watch stays with the original object — it does not jump to the newcomer. If the original key is removed, you get a "key deleted" event; to watch whatever now lives at that path, you reopen the path and arm a fresh watch. This follows from keys having an identity of their own, distinct from the name that currently points at them.

## Where to start

If you want the registry's own use of watches — how it picks up changes to its own configuration without restarting — read [How the registry boots and configures itself](~peios/registry/bootstrap-and-self-configuration).

If you want the validation half of the reaction loop — why a changed value might be read and then refused — read [Configuration, not storage](~peios/registry/configuration-and-meaning).

If you want what it takes to be allowed to watch a key, read [Access control on keys](~peios/registry/access-control).
