---
title: The Attribute
description: The user.pgss.indexing extended attribute, the three words it may hold, and how a value that is not one of them is read.
---

A file or directory MAY carry the extended attribute
`user.pgss.indexing`, whose value is one of these words:

| Word | Meaning |
|---|---|
| `all` | Index normally: names, properties and contents. |
| `no-content` | Record the item's name and properties, not its contents. |
| `none` | Record nothing of the item. |

An item without the attribute has no preference of its own, and takes
its preference from the directories above it (§8.3).

A word is compared byte for byte. A marker MUST write one of the words
above, without a trailing NUL byte. An indexer MAY treat a value ending
in a NUL byte as though the NUL were absent.

## A value that is not a word

An indexer MUST treat any other value, including an empty one, as
`no-content`. A value an indexer does not recognise is most likely a
word from a later version of this chapter or a mistake, and the person
who set it almost certainly wanted less indexing, not more. Reading it
as `no-content` keeps the item findable by name and keeps its contents
out of the index.

An indexer SHOULD make such values visible to whoever administers it, so
that a mistake can be found.

## Where the attribute cannot be kept

Because the attribute is in the `user` namespace, whoever may write the
item's extended attributes can set it, and it can be set on regular files
and directories only. An item on a file system that cannot keep `user`
extended attributes has no preference of its own.

A marker acting on a person's direct request SHOULD tell them when it
could not keep the preference, rather than appear to succeed.
