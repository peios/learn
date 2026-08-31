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

An untouched file keeps its inode: nothing is staged for it and no
rename runs. It still gets an ownership row under the new version, so
the upgrade's file set is complete and a later uninstall removes it.

Two conditions narrow the category, both of them cases where a file's
content is not the only thing being installed at that path:

- The file must actually be present. One the operator deleted is not
  untouched, and an upgrade is the right moment to put it back.
- A path carrying a signature sidecar or a §3.3.5 descriptor override
  is always rewritten. Both are applied to the staged inode, so the path
  needs one even when its content has not moved.

## Ordering at commit

Added files are renamed into place. Replaced files have their original
renamed aside first, then the staged file renamed in. Removed files are
renamed aside.

Directories left empty by an upgrade are not removed.
