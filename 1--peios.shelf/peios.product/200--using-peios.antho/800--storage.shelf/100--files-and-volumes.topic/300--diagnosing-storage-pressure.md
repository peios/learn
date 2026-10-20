---
title: Diagnosing Storage Pressure
type: how-to
description: Identify the affected filesystem and distinguish block, inode, and visibility limits before choosing cleanup.
---

Keep the exact failing operation, path, error, and time. A read-only mount,
permission denial, or I/O failure is not automatically a space problem.
Start with an existing path involved in the failure, or its existing parent.

```sh
df -hT /affected/existing/path
df -i /affected/existing/path
```

Record the filesystem, type, mountpoint, available space, inode availability,
and diagnostics. Do not substitute the root filesystem's figures without
checking that the path belongs to it.

Measure a narrow, authorized directory with `du`, retaining its errors and
exit status. A partial walk understates what it could not read. Use the
command's filesystem-boundary option when appropriate and avoid treating
merged views as independent physical copies.

Filesystem usage and directory totals need not agree. Open-but-unlinked files,
metadata, reserved space, snapshots, compression, sparse allocation, hard
links, and stacked filesystems can affect the comparison. A pathname survey
cannot account for every allocated block.

Choose the owner's supported remedy: package cache cleanup, log retention,
service data maintenance, or removal of a known expendable build artifact.
A large file is not proof that deletion is safe. Do not delete package
transaction journals, live databases, or boot files merely to make space.

After the separately chosen remedy, repeat the same measurements and retry
the original operation. Removing a pathname can not release its storage until
an owning process closes it. Record that limitation instead of escalating to
broader deletion.
