---
title: Deleting keys and values
type: how-to
description: Choose per-layer deletion, masking or hiding; review recursive deletion and verify what remains visible afterward.
related:
  - peios/registry-layers/layers
  - peios/registry-layers/what-layers-are-for
  - peios/registry-security/access-control
  - peios/registry-administration/lcs-and-sources
  - peios/registry-concepts/overview
---

Before deleting, inspect the current value and its winning layer. A
registry deletion normally removes an entry in the selected layer; a
remaining entry can become visible afterward.

## Choose the operation you mean

| Intent | Operation | Result |
|---|---|---|
| Withdraw one layer's value | `reg del KEY NAME --layer LAYER` | Removes that layer's entry; another may surface. |
| Keep a value absent through a layer | `reg mask KEY NAME --layer LAYER` | Adds a tombstone that competes with other entries. |
| Withdraw one layer's key name | `reg del KEY --layer LAYER` | Removes that layer's claim; another may remain. |
| Mask a key name through a layer | `reg hide KEY --layer LAYER` | Adds a hidden-key entry. |
| Withdraw a whole configuration layer | `reg layer del LAYER` | Removes its entries across the registry. |

`KEY`, `NAME` and `LAYER` are placeholders. Masking and hiding still obey
[precedence and write order](~peios/registry-layers/layers); they do not
ignore stronger entries. `reg unmask` and `reg unhide` remove the selected
layer's markers. `reg mask KEY --all` applies a blanket tombstone to values
on that key. See the [`reg` reference](~peios/registry-tools/reg).

Hive roots cannot be deleted or hidden.

## Deleting values

1. Read `reg get KEY NAME -L` and confirm the destination layer.
2. Remove only the intended layer's entry.
3. Read the value again. It may be absent or replaced by another winner.
4. Verify the consumer's response. Absence may select a default or retain
   a prior runtime setting, depending on that component's documented behavior.

Do not assume deleting the effective value restores its compiled default.
Do not use deletion to probe for hidden entries on a live system.

## Deleting a populated key

The kernel's single-key delete refuses visible child keys, but the tools
provide recursive deletion:

- `reg del KEY -r --layer LAYER` walks the subtree and deletes in a
  transaction. It deletes links without following their targets.
- Registry Editor's **Delete key…** deletes the shown key and its subtree
  after confirmation. Check **Writes go to** first.

Inspect the subtree with `reg tree KEY --values` and save an appropriate
[backup](~peios/registry-administration/backup-and-restore) before proceeding.
The command opens the keys before deleting; file-descriptor and transaction
limits can cause the whole operation to be refused. See
[`reg del`](~peios/registry-tools/reg#reg-del-key-value) for the documented limits.

`reg del -r` prompts only when input is a terminal, unless the prompt is
explicitly skipped. Non-terminal input proceeds without confirmation.
A failure before commit aborts the batch. After a commit timeout or source
failure, inspect state before retrying; an error does not prove rollback.

## Deleting out from under an open handle

An open handle refers to a key object, not just its name. Removing its
last name does not revoke existing handles: their reads, writes and
watches can continue while the object remains open. New opens by the
removed path fail, or resolve another key if layers provide one.

If a service must use a replacement key, it may need to reopen it through
its documented reload or restart procedure. The
[LCS deletion reference](~peios/lcs/the-data-model/deletion-and-orphans)
covers object lifetime.

## Permission

Deleting or hiding a key requires `DELETE` on that key. Deleting or
masking a value requires `KEY_SET_VALUE` on its key. Layer-targeted
operations also require permission to write into the layer. Parent
permissions alone do not establish access to descendants.

## Where to go next

- [Recover using a layer](~peios/registry-layers/what-layers-are-for)
- [Key and layer access checks](~peios/registry-security/access-control)
- [Verify the consumer after a change](~peios/registry-concepts/configuration-and-meaning)
