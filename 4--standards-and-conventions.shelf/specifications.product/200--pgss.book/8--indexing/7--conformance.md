---
title: Conformance
description: The obligations of each role, gathered in one place.
---

## A conforming indexer

- Finds each item's preference by the nearest `user.pgss.indexing` among
  the item and the directories above it, up to the root, and takes `all`
  where there is none (§8.3).
- Reads a value that is not one of the words as `no-content` (§8.2).
- Applies the preference before reading an item's data, and records no
  more than it permits (§8.4).
- Removes what a narrowed preference no longer permits, and notices
  changes or documents how long it may lag (§8.3, §8.4).

## A conforming marker

- Writes only `all`, `no-content` or `none`, without a trailing NUL
  (§8.2).
- Acting on a person's direct request, tells them when the preference
  could not be kept (§8.2).
- Translating Windows' attribute, follows §8.5.

## What conformance does not require

Conformance does not require a system to run an indexer, an indexer to
cover any particular location, or a marker to offer every word.
