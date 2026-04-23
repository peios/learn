---
title: The Check-at-Open Model
type: concept
description: Access is evaluated once at file open and the granted rights are cached on the handle for its lifetime.
---

Peios evaluates file access at **open time**, not on every individual read or write. When a process opens a file, AccessCheck runs once, and the resulting granted rights are stored on the open file handle. Subsequent operations on that handle check the handle's granted mask — they do not re-evaluate the security descriptor.

## How it works

1. A process requests to open a file with specific access rights (for example, `FILE_READ_DATA | FILE_WRITE_DATA`)
2. The kernel reads the file's security descriptor and runs AccessCheck against the calling thread's token
3. If AccessCheck grants the requested rights, the open succeeds and the handle carries the granted access mask
4. Every subsequent read or write on that handle is checked against the handle's mask — not the file's SD
5. When the handle is closed, the granted mask is discarded

## Why check at open

Evaluating AccessCheck on every read and write would be expensive — the DACL walk, privilege checks, integrity evaluation, and all other pipeline stages would run on every I/O operation. The check-at-open model runs this evaluation once and caches the result.

This is also a **correctness property**, not just a performance optimization. The handle represents a grant of access at a specific moment. If the file's SD changes after the handle is opened — for example, an administrator removes the process's access — the existing handle continues to work with the rights it was originally granted. The process opened the file when it had access, and the handle honors that grant.

New opens after the SD change will be evaluated against the new SD. Only existing handles are unaffected.

## Handles survive permission changes

> [!NOTE]
> Changing an object's security descriptor does not affect existing open handles. Only new opens are evaluated against the updated SD.

If a process opens a file for read and write, and then an administrator removes the process's write access:

- The **existing handle** still permits writes — it was granted write access at open time
- A **new open** for write access will fail — the current SD no longer grants it

This matches the principle that the handle is a granted-rights token for the file. The process acquired the handle legitimately, and the system honors that acquisition for the lifetime of the handle.

## Requesting the right access

Because rights are fixed at open time, a process must request the rights it will need at open time. A handle opened with only `FILE_READ_DATA` cannot later be used for writes — even if the SD would allow it. The process must open a new handle requesting write access.

This is also why `MAXIMUM_ALLOWED` exists — a process that does not know in advance which operations it will perform can request the maximum rights the SD grants, and then use whatever subset it needs.

## What is checked per-operation

The per-operation check is lightweight. The kernel compares the requested operation (read, write, etc.) against the handle's granted mask — a simple bitmask comparison. There is no SD lookup, no DACL walk, no privilege evaluation. The expensive work happened once at open time.

Continuous auditing (if configured) is the one per-operation addition. If the handle carries a continuous audit mask, each matching operation generates an audit event. But even continuous auditing does not re-evaluate AccessCheck — it reads the pre-computed audit mask stored on the handle.
