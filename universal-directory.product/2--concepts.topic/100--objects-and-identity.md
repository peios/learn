---
title: Objects and identity
type: concept
description: How UD models directory objects — GUID identity, the inode-shaped flat store, derived DNs and native paths, caseless type-blind sibling uniqueness, and the rules for rename, move, and delete.
related:
  - universal-directory/concepts/the-schema-model
  - universal-directory/concepts/replication
  - universal-directory/reference/naming-rules
  - universal-directory/reference/json-api
---

Every entry in the directory — an OU, a user, a schema definition — is an **object**. UD's object model rests on one distinction it never blurs: **identity versus address**.

## Identity: the GUID

An object's identity is a **GUID**, assigned at creation and immutable for the object's entire life.

Everything that needs to point at an object stores that GUID, never a name or a path: a group's `member` values, a facet's attribute list, a class's composition. Renames and moves therefore never break references. Deleting an object leaves any remaining references visibly **dangling** at the dead GUID, rather than silently rebinding to whatever later takes the name.

## Address: derived, never stored

Internally the store is *inode-shaped*: a flat table of objects keyed by GUID, where each object records only its **parent's GUID** and its own **bare name** (`Sales`, `Jack`). The tree is an index over that table.

Both address forms are computed on demand:

- the **distinguished name** — leaf-first with typed components, `CN=Jack,OU=Sales`, where each prefix comes from the object's class (`dnPrefix`) and values are escaped per RFC 4514;
- the **native path** — root-first and untyped, `/Sales/Jack`, used by the console, the [JSON API](~universal-directory/reference/json-api)'s path resolution, and anywhere a human types an address. Path lookup is case-insensitive.

Because addresses are derived, renaming an OU is a single-object change. Every descendant's DN and path change *logically*, with zero writes, and nothing that references those descendants notices at all.

The tree has a single **root object** — empty name, class `domainRoot` — which never appears in DNs and cannot be renamed, moved, or deleted.

## Names and sibling uniqueness

Within one parent, names are unique under two deliberately strict rules.

**Caseless, case-preserving.** Names compare under Unicode canonical caseless matching, so `Jack`, `jack`, and a decomposed `Jack` are all the same name. The spelling you create is the spelling you see; the folding governs comparison and conflict only. See [naming rules](~universal-directory/reference/naming-rules) for the exact function.

**Type-blind.** Uniqueness ignores class entirely. An OU named `Sales` and a group named `sales` cannot be siblings. One container, one meaning per name.

Name validity is strict too — non-empty, no `/`, no control characters, no leading or trailing whitespace. Strict rules can be safely loosened later; a loose rule can never be tightened without breaking existing data.

## Rename and move

Rename and reparent are one operation, in the shape of LDAP's ModifyDN: change the name, the parent, or both, atomically.

The engine refuses:

- moves that would create a **cycle**, placing an object under itself or its own descendant;
- a destination where the caseless, type-blind name is already taken;
- any rename or move of the root, of **system objects**, or of [schema objects](~universal-directory/concepts/modifying-the-schema) — definitions are add and delete only — and any move *into* the schema subtree.

A case-only rename, `jack` → `Jack`, is always legal. It is the same caseless name, so it conflicts with nothing.

## Delete: the three-stage lifecycle

Deletion is **soft and subtree-wide**. Deleting an object tombstones it *and every descendant* in place, each with its own stamped existence transition.

A tombstone leaves the effective tree immediately — its name is free at once — but the full record survives, and every tombstoned object is individually **restorable**. Restoring is top-down: the parent must be alive and the name must still be free. It is an ordinary write, and a restore into a conflict simply refuses.

Beyond `Deleted` sit two harder states.

**Shredded** is security erasure, reachable directly from alive or as an escalation of a soft delete. The payload and even the *name* are destroyed; only a skeleton — GUID, parent GUID, stamps — remains. Every reference to the shredded GUID is physically **scrubbed out of every holder**, because erasure that leaves the object's GUID lingering in group member lists would fail its own purpose. The destruction [reaches the node's files](~universal-directory/concepts/persistence) within a guaranteed window. There is no way back.

**Purged** means the tombstone is gone entirely. This is never manual: purge happens automatically once a tombstone's age passes `maxTimeApart`.

### Aging is computed, not written

Two domain-wide knobs, stored as attributes on `/Configuration` with defaults of 30 and 180 days, drive the automatic transitions. Past **`timeUntilShred`** a soft-deleted record hardens: the restore window closes and the flesh is scrubbed to a skeleton. Past **`maxTimeApart`** the skeleton purges.

Aging is a pure function of the object's existence stamp, the config windows, and the clock. Every node evaluates a tombstone's *effective* stage the same way, so nodes never race stamps about it. Local garbage collection merely catches physical storage up with what the aging function already answers.

The root and system objects are permanently protected, and schema definitions add their own [unused-delete rules](~universal-directory/concepts/modifying-the-schema). Because references store GUIDs, deleting a referenced object never edits the referrers: their values dangle visibly at the tombstone until the target is shredded, at which point they are scrubbed.

## System objects

Objects created at domain creation carry a **system** flag: the root, `/Configuration`, `/Configuration/Schema`, `/LostAndFound`, `/Domain Controllers`, and every base schema definition.

System objects refuse renames, moves, and deletion — they are the fixed points the rest of the directory is built around — but their **attributes are writable**. The replication knobs live as attributes on `/Configuration`, and a description on the root is legal. Schema definitions are the exception, fully immutable via the [schema-subtree rule](~universal-directory/concepts/modifying-the-schema).

## Structural repairs are derived, never written

Replication will merge writes that were each legal at their origin but collide when combined. UD repairs these **as a view**: the stored records stay exactly as written, and every node *derives* the same effective tree from the same atoms. No repair writes, no repair replication traffic.

Three rules, all favouring the **earliest claim** — the first legal write stands, because the later write is the one that caused the violation:

- **Name conflicts.** Two live siblings whose names fold equal: the earliest placement claim keeps the name, and the later one *displays* as `name CNF:<guid>`. It remains resolvable and renameable, and its stored name is untouched.
- **Orphans.** A live object whose stored parent is dead or missing derives into **`/LostAndFound`**. Restoring the parent snaps it back automatically.
- **Cycles.** Concurrent moves that form a loop break at the *newest* placement: the latest mover derives into `/LostAndFound`, and the earlier move survives intact.

Admin operations target the **effective view** — rename the CNF loser, move the orphan out, as ordinary writes — and the repair dissolves the moment the underlying violation is gone.

Objects whose *class definition* has not arrived yet are **ghosts**: visible in the debugger, holding their sibling name, but refusing every originating write until the schema converges.

## Replication stamps

Every replicated fact about an object decomposes into **merge atoms**:

- its **existence** — creation, with class and the system flag riding along;
- its **placement** — `(parent, name)` as one atom, so rename and move contend as a unit;
- each **attribute value**.

Every atom carries a **stamp**: a version, an originating time, and an originating invocation id. Together these decide conflicts deterministically — higher version wins, then later timestamp, then origin — and a transfer certificate drives change enumeration. Removing a value leaves a stamped **absence atom** rather than a hole, so the removal itself can win merges.

For how those atoms travel and merge, read [Replication](~universal-directory/concepts/replication).
