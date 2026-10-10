---
title: Find why a filesystem is full
type: how-to
description: Distinguish block and inode pressure on the affected filesystem, find visible consumers without changing data, and verify a separately chosen remedy.
related:
  - peios/disks-and-filesystems/overview
  - peios/files-and-directories/df
  - peios/files-and-directories/du
  - peios/logs-and-events/find-missing-records
---

Start with the operation that failed, not with a directory to delete. Keep its
exact error, path and time. A permission denial, read-only filesystem or I/O
failure is not established as a space problem merely because a write failed.

This procedure inspects capacity and a selected directory tree. It does not
delete data, repair or resize a filesystem, change mounts, or stop services.
Use your current authorized access; incomplete visibility is a finding, not a
reason to broaden privileges automatically.

## 1. Identify the affected filesystem

Replace the example path below with a verified **existing** path involved in
the failure. If the attempted new file does not exist, use its existing parent.
Quote paths containing spaces.

```sh
df -hT /affected/existing/path
df -i /affected/existing/path
```

After each command, retain its exit status and any diagnostics as well as the
report. [`df`](~peios/files-and-directories/df) reports the filesystem containing
the named path; do not substitute the root filesystem's figures without
checking that it is the one involved.

- Record **Filesystem**, **Type** and **Mounted on** so later measurements
  refer to the same filesystem.
- Inspect **Avail** and **Use%** in the block-space report.
- Inspect the inode counts and free-inode figure in the second report. Inode
  exhaustion can prevent creating files even when block space remains.
- If the path or filesystem lookup fails, resolve that diagnostic before
  treating any other printed row as the answer.

These commands use the default no-sync behavior; they do not request a flush.
If the reported capacity does not explain the failure, keep the original error
and investigate that separately rather than starting cleanup by guesswork.

## 2. Look within a narrow, permitted tree

Choose a known directory on that filesystem, such as the affected application's
identified data tree. Substitute that directory for `/known/tree`:

```sh
du -x -h --max-depth=1 /known/tree
```

For suspected inode pressure, count entries instead of allocated space:

```sh
du -x --inodes --max-depth=1 /known/tree
```

Pass the directory itself, not a shell `*` expansion that omits dotfiles. Start
narrowly and drill into one observed large directory at a time.

> [!IMPORTANT]
> `--max-depth=1` limits **printed depth**, not traversal. `du` still walks the
> tree to compute totals and can cause substantial I/O. `-x` skips subdirectories
> on a different device; it does not bound the work or exclude every same-device
> bind/mount alias. Do not begin with a whole-system scan merely to get a short
> report.

Keep stderr and the exit status for every run. A permission or traversal error
can occur alongside printed totals; those totals are incomplete. Record files
that disappeared or changed during the walk too. Missing observations are not
proof that an unreadable directory is empty.

See [`du`](~peios/files-and-directories/du) for the full options and status codes.

## 3. Interpret the measurements together

`df` describes filesystem capacity. `du` measures what its walk can reach and
read in the selected tree. Their figures need not match:

- The tree may cover only part of the filesystem, and `-x` skips other devices.
- Access failures can hide contents from the walk.
- By default, `du` counts allocated blocks, not apparent file length; sparse
  files and block rounding affect that distinction.
- Hard-linked files are counted once by default, and symlinks are not followed.

Do not treat a difference as proof of deleted-open files, quotas, or any other
specific cause without a supported observation. Nor does a large total establish
how many bytes a particular cleanup would make available.

## 4. Choose the component's supported remedy

Identify the owner of the measured data before changing it. Use that component's
documented retention, cleanup or recovery procedure, and check what it destroys.
This guide supplies no generic deletion, database-file removal, WAL removal,
forced-stop or resize recipe.

For event storage, [retention settings](~peios/logs-and-events/find-missing-records#4-check-the-retention-settings)
control which records remain queryable. Deleting records logically does not
prove that the physical database files immediately shrink. Preserve incident
evidence before a separately authorized destructive retention change.

Evidence capture can itself fail under pressure: `evctl` needs writable space
and anonymous-temporary-file support in its temporary filesystem **as well as**
space at the final destination. A destination with free space is not sufficient.
Keep query diagnostics; see [failed-query diagnosis](~peios/logs-and-events/find-missing-records#3-distinguish-a-failed-query-from-an-empty-one)
and the [temporary-spool implementation](https://github.com/peios/eventd/blob/3df88bab845d962e866158896807eac2976b83e3/evctl/src/output.rs#L42-L95).

After applying a separately chosen, supported remedy, rerun the same `df`
measurements and any relevant narrow `du` walk. Then check the original failed
operation separately: more free space alone does not prove the application can
write successfully.

## Source and scope

The command behavior was checked in peiosutils `3344d46`: [named-path filesystem
selection](https://github.com/peios/peiosutils/blob/3344d4690476fd66bfaec99b1ae92190bbcba06f/src/uu/df/src/df.rs#L348-L420),
[`du` traversal boundaries](https://github.com/peios/peiosutils/blob/3344d4690476fd66bfaec99b1ae92190bbcba06f/src/uu/du/src/du.rs#L441-L467),
and [counting versus printed depth](https://github.com/peios/peiosutils/blob/3344d4690476fd66bfaec99b1ae92190bbcba06f/src/uu/du/src/du.rs#L730-L774).
This is a source-backed diagnostic workflow, not a runtime-tested cleanup or
capacity-expansion procedure.
