---
title: Extension
description: What may be added to this chapter without breaking a conforming marker or indexer, and what may not.
---

## Additive changes

- A new word in §8.2. An indexer built to this version reads it as
  `no-content`. For a word that permits no more than `no-content`, that
  is what it allows at most; for one that permits more, an older indexer
  records less than the word allows, which errs the safe way.
- A new source of preference consulted after the walk of §8.3 finds no
  word, such as a system-wide setting. An indexer built to this version
  indexes such items normally.

## Changes requiring a new version

- A change to what an existing word permits.
- A change to the walk of §8.3, such as stopping at a mount point.

## Reserved

The `pgss.indexing` name in the `user` extended-attribute namespace is
this chapter's.
