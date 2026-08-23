---
title: Deleting keys and values
type: concept
description: Deleting a key withdraws one layer's claim to a name — the key stays if another layer still claims it, and there is no recursive delete.
related:
  - peios/registry-layers/layers
  - peios/registry-layers/what-layers-are-for
  - peios/registry-security/access-control
  - peios/registry-administration/lcs-and-sources
  - peios/registry-concepts/overview
---

Deletion is one more thing the [layered model](~peios/registry-layers/layers) quietly reshapes. "Delete this key" sounds absolute, but in a store where a name is the winner of a per-layer contest, removing a key really means withdrawing *one layer's claim* to that name. Several behaviours follow that are worth knowing before you delete anything.

## Deletion, in one sentence

**Deleting a key withdraws one layer's claim to a name; the key disappears only if no layer still claims it — and even then, anything holding it open keeps working until it lets go.**

## Deleting withdraws a claim

When you delete a key, you remove its name in a particular layer — the [base layer](~peios/registry-layers/what-layers-are-for) unless you say otherwise. Nothing about the key is special-cased; its claim in that layer is simply withdrawn, and it drops out of the [contest](~peios/registry-layers/layers) for that name.

If another layer still names the key, it stays visible through that layer. So deleting a key that a role also provides removes only *your* claim — the role's key remains until the role does. To remove a key everywhere, every layer's claim has to go. For anything delivered by a role or a policy, that means removing the *layer* (which [reverts cleanly](~peios/registry-layers/what-layers-are-for)) rather than deleting the key — deleting it in the base layer would not touch the role's claim anyway.

(The hive roots themselves — `Machine\`, `Users\<SID>\` — cannot be deleted or hidden. They are the anchors the namespace hangs from.)

## There is no recursive delete

You cannot delete a key that still has visible child keys; the deletion is refused. There is no "delete this whole subtree" primitive. Removing a populated subtree is a deliberate walk from the leaves upward, performed by whatever tool you are using — not a single sweep in the kernel.

This is a safety property, not a limitation to work around. A mistaken delete cannot take a populated subtree down with it; you have to mean it, key by key.

## Deleting out from under an open handle

A key can be deleted while a process still has it open, and the registry handles that the same way Linux handles deleting an open file (the *unlink* model). The open handle keeps working — reads, writes, and watches all continue against the now-unnamed key — and the key is only truly discarded once the last handle closes. Meanwhile, new attempts to open it *by path* fail at once: the name is gone, even though the object lingers for whoever still holds it.

So "deleted" means "no longer reachable by name", not "destroyed this instant". A service that had the key open does not break mid-operation; it holds the last reference until it closes, and only then does the key go away.

## Deleting values

A value works the same way one level down. Deleting a value withdraws a layer's write for that value name. If a lower-precedence or older layer also wrote that value, its write resurfaces as the new effective value — the ordinary [revert](~peios/registry-layers/what-layers-are-for). Remove a value's only write and the value simply becomes absent.

## Permission

Deleting (or hiding) a key requires delete permission on it — see [Access control on keys](~peios/registry-security/access-control). As everywhere in the registry, the check is against the key you are deleting, decided by its security descriptor, with no check on the keys above it.

## Where to go next

For the contest that "withdrawing a claim" feeds back into, read [Layers](~peios/registry-layers/layers).

For removing configuration in bulk — deleting a layer, which is what you do instead of deleting a role's or policy's keys — read [What layers are for](~peios/registry-layers/what-layers-are-for).
