---
title: From an Item to Its Preference
description: How an indexer finds an item's preference, the nearest word among the item and the directories above it, and how a directory loosens its parent's.
---

An item's preference is the word of the nearest of these that carries
`user.pgss.indexing`: the item itself, then its parent directory, then
each directory above that, up to the root of the namespace. If none
carries it, the preference is `all`.

A directory's word therefore holds for everything beneath it, files and
directories alike, until a nearer word says otherwise. `all` on a
subdirectory loosens a parent's `no-content` or `none` for the subtree
it heads.

```
Private/            user.pgss.indexing = none
  diary.txt         (none)           -> none: nothing recorded
  Shared/           user.pgss.indexing = all
    notes.txt       (none)           -> all: indexed normally
Projects/           user.pgss.indexing = no-content
  plan.odt          (none)           -> no-content: name only
```

An indexer MUST find the preference this way, and MUST NOT stop at the
item, or at the first directory it began indexing from.

## Which path

An item may be reachable by more than one path: through hard links, bind
mounts, or symbolic links to a directory above it. An indexer applies
this section to the path by which it reached the item, and treats the
item as a separate entry under each path it records it by.

The walk crosses mount points: a mounted file system's root takes its
preference from the directory it is mounted on, as any other directory
does.

## Change

A change to an item's attribute changes the preference of every item
beneath it that has no nearer word. An indexer SHOULD notice a change to
the attribute on a directory it indexes and apply it to the subtree. An
indexer that cannot notice changes MUST document how long it may go on
recording what a changed preference no longer allows, and MUST remove
what it recorded once it learns of the change.
