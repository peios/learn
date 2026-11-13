---
title: The Pointer File
description: The one file of a repository that changes, its lines, its order, its sequence that only goes up, and when it was signed.
---

A repository's **pointer file**, `repository`, says what its catalog, its
indexes and its channels are:

```text
sequence 1042
signed 2026-11-13T11:30:00Z
catalog sha256:…
index 2026.10.0 sha256:…
index leading sha256:…
channel 2026.09 2026.09.3 ended
channel stable 2026.10
```

## Lines

In this order:

1. `sequence` and a decimal number: how many times the repository has been
   published. Each publication MUST be one higher than the last.
2. `signed` and the time it was signed, in UTC, as
   `YYYY-MM-DDTHH:MM:SSZ`.
3. `catalog` and the identity of the catalog's top node, once there is one.
4. A line for each index, sorted by the bytes of its name: `index`, its
   name, and the identity of its top node.
5. A line for each channel, sorted by the bytes of its name: `channel`, its
   name, and the index or channel it follows, then ` ended` if it won't
   move again.

A consumer MUST refuse a pointer file that isn't in this form, that names
something twice, that has a name both an index and a channel, or whose
channels don't each reach an index (§5.30).

## Writing it

The pointer file is written whole and renamed into place, after its
signature (§5.33). A reader that finds the two don't match has read between
them, and SHOULD read both again.
