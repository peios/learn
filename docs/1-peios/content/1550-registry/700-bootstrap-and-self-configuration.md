---
title: How the registry boots and configures itself
type: concept
description: The registry is the configuration store for the whole system — so what configures the registry? It mostly configures itself, which means breaking a circular dependency. It does so by running on compiled-in defaults from the instant the kernel loads, then hot-swapping to registry-backed configuration once its store is available. It never waits for configuration to exist.
related:
  - peios/registry/configuration-and-meaning
  - peios/registry/watches
  - peios/registry/lcs-and-sources
  - peios/registry/layers
  - peios/registry/overview
---

The registry holds the configuration for everything on the system. Which raises an awkward question: what configures the *registry*? The honest answer is that it mostly configures itself — and doing that means breaking a circular dependency, because the registry's own settings live in the registry, and the store those settings live in is itself a service that has to start up. This page is how that knot is untied, and it doubles as the purest example of the [reject-or-keep](~peios/registry/configuration-and-meaning) discipline.

## Bootstrap, in one sentence

**The registry subsystem is fully operational on compiled-in defaults from the instant the kernel loads, and hot-swaps to registry-backed configuration once its store comes up — it never enters a "waiting for configuration" state.**

## The circular dependencies

Three loops have to be broken at boot:

- The registry reads its own operational parameters (timeouts, size limits, and so on) from a key under the `Machine\` hive — but that hive is held by a store that has not started yet.
- Other early services want to read *their* configuration from the registry before that same store is up.
- On a brand-new install there is no data at all: the store's database is empty.

A configuration store that refused to function until it was configured would deadlock on the first of these. The registry is designed so that never happens.

## Compiled-in defaults

Every operational parameter the registry uses has a **compiled-in default** that produces correct behaviour. From the moment the kernel module loads, the registry runs on those defaults — it is immediately operational and never blocks waiting for configuration. The [base layer](~peios/registry/what-layers-are-for) likewise exists unconditionally, hardcoded, needing no persisted state. So before any store has registered, the machinery is already alive; it simply has no hives to serve yet.

## Hot-swap, not restart

When the store registers and the configuration keys become readable, the registry **reads, validates, and swaps its parameters in place** — no restart, no re-initialisation. Operations already in flight finish on the values they started with; new operations pick up the new values. The transition from "compiled-in defaults" to "registry-backed configuration" is seamless and is the *only* configuration transition there is.

```mermaid
flowchart LR
    A["Kernel loads — registry live on compiled-in defaults"] --> B["Store registers its hives"]
    B --> C["Read Machine\System\Registry\* parameters"]
    C --> D["Validate and hot-swap into effect"]
```

## It applies reject-or-keep to itself

This is the cleanest demonstration of the idea from [Configuration, not storage](~peios/registry/configuration-and-meaning): the registry treats its *own* configuration as untrusted bytes it must validate. A parameter value that is valid is hot-swapped into effect. One that is invalid — out of range, wrong type — is **ignored**: the registry keeps the value it was already using and emits an audit event naming the key, the rejected value, and the value still in force. It never clamps the bad value to something legal. The subsystem that owns the entire registry does not trust even its own settings until it has checked them — and when stored and in-force disagree, the audit log is the truth.

## First boot, with no data

A fresh install has an empty store, and the sequence is built to cope:

1. The store starts, finds its database empty, and creates the hive root keys with their default [security descriptors](~peios/registry/access-control) — but no configuration beneath them.
2. The registry looks for its parameter keys, finds nothing, and keeps its compiled-in defaults. It is fully operational regardless.
3. The init system (not the registry's concern) restores a **seed** that populates `Machine\` with the system's real configuration.
4. That write trips the registry's watch on its own configuration area; it re-reads, validates, and hot-swaps to the seeded values. Normal operation continues.

At no point is there a stall. Empty store, missing keys, seed arriving later — each is handled by "use the defaults until something better shows up", driven by the same [watch](~peios/registry/watches) mechanism every other reactive consumer uses.

## The self-watch

The registry notices changes to its own configuration the same way any service notices changes — by watching the subtree — except the watcher is internal to the kernel rather than a userspace handle. It is the [reaction loop](~peios/registry/watches) turned on the registry itself: a change to a parameter key fires the watch, the registry re-reads and re-validates, and applies or rejects. There is no polling and no special-case configuration path; self-configuration is just the registry being one more consumer of the registry.

## Where to start

If you want the store itself — what it is, how the kernel and the userspace store divide the work, and the trust boundary between them — read [LCS and sources](~peios/registry/lcs-and-sources).

If you want the validation discipline this page leans on, read [Configuration, not storage](~peios/registry/configuration-and-meaning).

If you want the change-notification mechanism behind the self-watch, read [Watching for changes](~peios/registry/watches).
