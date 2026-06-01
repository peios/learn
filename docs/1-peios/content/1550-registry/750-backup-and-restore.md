---
title: Backup and restore
type: concept
description: The registry can export an entire subtree to a stream and restore one back, wholesale. It is how the system is seeded at first boot, recovered after disaster, and migrated between machines. Restore is a replace, not a merge — and the privilege to perform it is, in effect, the power to rewrite security on everything it touches.
related:
  - peios/registry/bootstrap-and-self-configuration
  - peios/registry/lcs-and-sources
  - peios/registry/access-control
  - peios/registry/layers
  - peios/registry/overview
---

Beyond reading and writing individual values, the registry can move whole subtrees at once: **export** a key and everything beneath it to a stream, and **restore** such a stream back into the tree. This is the bulk-data path, and it is the mechanism behind things you have already met — [first-boot seeding](~peios/registry/bootstrap-and-self-configuration) — as well as the disaster-recovery and migration any real deployment needs.

## Backup and restore, in one sentence

**Backup streams a point-in-time copy of a subtree out; restore replaces a subtree wholesale from such a stream — both are privileged, whole-subtree operations, not value-by-value edits.**

## Backup is a point-in-time snapshot

A backup captures a key and its entire subtree as it stands at one instant — a consistent snapshot, unaffected by writes happening concurrently. The result is a self-contained stream you can send to a file, a pipe, or across a network.

It is **full-fidelity with respect to [layers](~peios/registry/layers)**: a backup records every layer's writes, not merely the effective values. Restore it and the layered structure comes back intact — the base values, the role layers, the policy overlays, all of them, resolving the way they did before. A backup is not a flattened picture of "what the values currently are"; it is the whole stack.

The stream is also self-verifying: it carries an integrity check, so a truncated or corrupted backup is caught when you try to restore it, rather than restored as garbage.

## Restore is replace, not merge

This is the rule to internalise. Restoring into a key **replaces** that key's contents and entire subtree: the existing descendants are removed and the backup's contents take their place. It is not a merge and it does not add to what is there — whatever was under the target key before is gone, supplanted by the stream.

The target key itself survives as the anchor — it keeps its identity and its place in the tree — and everything beneath it is rebuilt from the backup. The whole operation is atomic: it either completes and swaps the new subtree in, or fails and leaves the original untouched. There is no half-restored state to clean up.

## Both bypass per-key permissions — by design

Backup and restore do not consult the security descriptor on each key the way an ordinary open does. They are gated by **privilege** instead — a backup privilege to read the whole subtree, a restore privilege to write it. This is the same model as file backup: a backup operator reads files they were never granted access to, because reading-for-backup is the privilege, not per-file permission.

For restore, the consequence is sharp and worth stating plainly. **The privilege to restore is, in effect, the privilege to rewrite security on everything in the target subtree.** A backup carries each key's security descriptor, and restore writes those descriptors back — so restoring lets the caller replace owners and permissions throughout the subtree, which is close to taking ownership of all of it. Granting restore privilege is therefore a serious act, not a routine one: read it as "may rewrite this subtree, security and all," because that is what it grants.

(Both operations are audited every time they run, regardless of a key's own audit settings — see the [auditing topic](~peios/auditing/overview).)

## What it is for

- **First-boot seeding.** A fresh machine's registry is empty; its initial configuration is delivered by *restoring* a seed. Same mechanism, described in [bootstrap](~peios/registry/bootstrap-and-self-configuration).
- **Disaster recovery.** Snapshot a subtree — or a whole hive — and restore it after a failure or a bad change.
- **Migration.** Move configuration between machines by backing up on one and restoring on another; the stream is portable.

## Where to start

For where restore comes from at first boot, read [How the registry boots and configures itself](~peios/registry/bootstrap-and-self-configuration).

For who actually performs these operations — the kernel coordinating the store — read [LCS and sources](~peios/registry/lcs-and-sources).

For the privilege model they lean on, read [Access control on keys](~peios/registry/access-control).
