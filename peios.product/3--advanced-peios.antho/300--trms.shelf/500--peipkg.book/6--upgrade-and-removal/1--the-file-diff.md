---
title: The File Diff
description: An upgrade is one atomic operation combining an install and a removal — the four file categories, and their ordering at commit.
---

An upgrade replaces one installed version of a package with another. It
is conceptually a single atomic operation combining an install of the
new version with an uninstall of the old, arranged so that no moment
leaves the system without the package's content.

The same procedure handles a downgrade. The two differ only in which
version comparison applies; the format treats them identically.

## The four categories

An upgrade is computed as a diff between the old version's file set,
read from the package database, and the new version's, read from the new
package's files manifest.

| Category | Meaning | At commit |
|---|---|---|
| **Added** | In the new set, not the old | Staged and renamed in |
| **Replaced** | In both, with different content | Old renamed aside, staged renamed in |
| **Untouched** | In both, with identical content hash | Left alone |
| **Removed** | In the old set, not the new | Renamed aside |

peipkg does not compute the untouched category. Every payload entry of
the new version is staged and renamed into place, whether or not its
content differs from what is already there.

The effects are an upgrade that rewrites and backs up its whole payload
rather than the changed part of it, inode and timestamp churn on files
that did not change, and the configuration-file consequence described in
§6.2.

## Ordering at commit

Added files are renamed into place. Replaced files have their original
renamed aside first, then the staged file renamed in. Removed files are
renamed aside.

Directories left empty by an upgrade are not removed.
