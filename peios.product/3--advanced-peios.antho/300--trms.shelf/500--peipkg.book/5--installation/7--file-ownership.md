---
title: Pre-Existing Files
description: How peipkg handles a path that already exists without belonging to any package.
---

A path may already exist on the filesystem without belonging to any
installed package — left by a manual copy, inherited from a non-Peios
installation, or written by something outside the package manager.

## The unowned-file policy

Before replacing a destination, peipkg checks its recorded owners. A
path owned by the package being changed follows ordinary replacement;
a path owned by another package is handled by collision checking. For
an existing path with no recorded owner, `unownedPolicy` selects one of
three outcomes:

- **Adopt** matching content. A regular file must have the payload's
  content hash; a symlink must have the same target. A different entry
  kind never matches. The operation may proceed and record ownership.
- **Refuse** differing content unless overwriting was explicitly
  authorised. The `unowned` error names the package and conflicting
  path. The existing content is preserved.
- **Displace** differing content when overwriting was authorised. The
  existing entry is renamed aside, and its backup survives transaction
  commit. A warning reports the displaced file and backup name.

These behaviours are implemented for payload installation and role
claims. The comparison is about entry kind and content, not equality of
all metadata. Matching content permits the normal file operation; it
does not promise that the existing inode is retained.

## Recovering from a refusal

Move the conflicting file aside and retry the operation. `install` also
accepts `--overwrite-unowned`, which authorises displacement while
keeping the previous content. Upgrade, downgrade, undo, remove and
claim have no equivalent command-line flag; a driven client cannot
retry those commands by adding it.

Ordinary replacement backups are discarded on commit (§8.2). A backup
kept because an unowned file was displaced is the exception and remains
available to the operator.
