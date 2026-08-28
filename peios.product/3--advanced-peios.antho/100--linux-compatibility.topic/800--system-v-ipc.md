---
title: System V IPC
type: concept
description: SysV message queues, shared memory and semaphores carry security descriptors like every other Peios object; the nine-bit ipc_perm mode is informational, and the key namespace is first-come.
related:
  - peios/linux-compatibility/overview
  - peios/linux-compatibility/dac-neutralization-and-capabilities
  - peios/security-descriptors/overview
---

System V IPC — `msgget`, `shmget`, `semget` and the operations on the objects they create — keeps working on Peios exactly as Linux software expects, with one change to who is allowed to do what: **every SysV object carries a security descriptor**, and that descriptor, not the object's nine-bit mode, decides access.

## What you get by default

When a process creates a queue, segment or semaphore array, KACS stamps it with a descriptor built from the creator's token: the creator's user, `Administrators` and `SYSTEM` get full control; nobody else gets anything. Two consequences fall out that Linux does not give you:

- A **sandboxed** process (a restricted token) cannot reach segments its parent created, even though the projected UID is the same — the restricted-SID pass fails, as it would for a file.
- A different user is denied outright, with no way to loosen it through `chmod`-style mode bits. To share, edit the descriptor.

## Mode bits are informational

`IPC_SET` still updates the object's `uid`, `gid` and `mode`, and `ipcs` and `IPC_STAT` still show them — but nothing consults them for access, exactly as file mode bits work under FACS. `IPC_SET` itself needs `WRITE_DAC` and `WRITE_OWNER` on the descriptor (one command changes all three fields), on top of Linux's own rule that the caller be the creator or owner or hold `SeTcbPrivilege`.

## Reading and changing the descriptor

A SysV object has no path and no descriptor number, so the SD calls address it by kind and id: pass `KACS_SD_AT_SYSV_SHM`, `KACS_SD_AT_SYSV_MSG` or `KACS_SD_AT_SYSV_SEM` in the flags of `kacs_get_sd` / `kacs_set_sd` (`peios_file_get_sd` / `peios_file_set_sd` in libpeios), the object id where a directory fd would go, and no path. The rights are in Peios Kernel TRM §3.11; the descriptor format is the ordinary one.

## The key is not protected

The descriptor protects the object once it exists. It cannot protect the *name*: keys are first-come, and a process that creates key `0x5432` before your service does owns whatever your service then finds there. This is the same trap as the abstract socket namespace and `/dev/shm`. Create with `IPC_EXCL` and treat failure as a signal — and if what you actually need is to know who sent a message, use a Unix socket, which carries the sender's identity; a message queue carries only bytes.

## Where to go next

For how DAC is switched off so that descriptors always decide, read [DAC neutralisation and capabilities](~peios/linux-compatibility/dac-neutralization-and-capabilities).

For the descriptor format and how to write one, read [Security descriptors](~peios/security-descriptors/overview).
