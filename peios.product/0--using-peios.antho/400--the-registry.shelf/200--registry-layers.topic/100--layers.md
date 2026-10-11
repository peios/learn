---
title: Layers
type: how-to
description: Find which registry layer wins, understand precedence and same-precedence write order, and diagnose a change hidden by another layer.
related:
  - peios/registry-concepts/configuration-and-meaning
  - peios/registry-layers/what-layers-are-for
  - peios/registry-security/access-control
  - peios/registry-concepts/watches
  - peios/registry-concepts/overview
---

If a successful write does not change the value you read, inspect the
winning layer before writing again:

```sh
reg get Machine/System/KMES BufferCapacity -L
reg layer ls -l
```

Registry Editor shows the winning layer in the value pane and the layer
list under **Layers…**. Neither interface currently shows the complete
set of shadowed entries for a value.

## What a layer retains

A layer groups registry entries so they can be enabled, disabled or
removed together. Each layer retains at most one entry for a particular
value name on a key. Another write in the same layer replaces that
entry; layers are not a history of every edit.

The default write destination is `base`. Use `--layer NAME` or Registry
Editor's **Writes go to** control to select a different destination.
Check the destination before changing or deleting anything.

## How the winner is chosen

For each value separately, the registry selects among active entries:

1. Highest **precedence** wins.
2. At equal precedence, the latest **write sequence** wins.

A read returns that effective winner. A winning tombstone instead makes
the value absent. The same ordering also governs layered key names.

## Equal-precedence layers can each win different values

Base and role layers normally use precedence 0. Neither is permanently
above the other. If base writes one value last and a role writes another
last, each wins its own value. Layer creation order does not establish a
fixed order for all their settings.

This also means a later role update can supersede an earlier local edit
at the same precedence. Record the winning layer for the specific setting
rather than assuming all settings come from one layer.

## When precedence really does differ

A higher-precedence entry wins even over a newer lower-precedence entry.
Rewriting base does not defeat policy above precedence 0.

Creating or raising a layer above 0 requires `SeTcbPrivilege` in addition
to the relevant key rights. Administrator membership alone does not
supply that privilege. Do not change layer precedence as a shortcut around
a policy decision; use the responsible policy or role's management path.

## Sequence numbers are ordering information

Write order is a monotonic sequence, not the key's wall-clock last-write
time. Changing the clock does not make an older entry win.

`reg get -L` exposes the winning sequence. Conditional writes check the
destination layer's entry, so a winner from a different layer is not a
usable version of your own layer's value. See [Transactions](~peios/registry-advanced/transactions).

## It is not only values

Layers can create or hide key names and mask individual or all values on
a key. Removing a marker lets the remaining entries compete again; it
need not leave the key or value absent. Read
[Deleting keys and values](~peios/registry-layers/deleting-keys-and-values)
before choosing between delete, mask and hide.

## Where to go next

- [Disable or remove a layer and verify recovery](~peios/registry-layers/what-layers-are-for)
- [Key and layer permissions](~peios/registry-security/access-control)
- [LCS resolution algorithm](~peios/lcs/layers/resolution) and
  [sequence counter](~peios/lcs/layers/the-sequence-counter) for implementation detail
