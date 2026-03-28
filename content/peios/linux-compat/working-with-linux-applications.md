---
title: Working with Linux Applications
type: how-to
order: 110
description: Running unmodified Linux applications on Peios, handling root-refusing software, and diagnosing UID-related differences.
---

Most Linux applications run on Peios without modification. This page covers the common situations where Linux applications behave differently and how to handle them.

## Running root-refusing software

Some applications (Chrome, Elasticsearch, PostgreSQL) refuse to run as UID 0. On Peios, no process runs as UID 0 unless it holds the SYSTEM token — which these applications never will. This means root-refusing software works without modification.

```bash
$ idn sid
S-1-5-21-...-1013 (alice)

$ id -u
1013
```

The application sees a non-zero UID and starts normally.

## Applications that require root

Some applications expect to run as UID 0, typically because they need to perform privileged operations (binding low ports, loading kernel modules, etc.).

On Peios, the correct approach is to grant the service the specific **Peios privileges** it needs. A DNS server that needs to bind port 53 does not need root — it needs `SeBindPrivilegedPortPrivilege`. A monitoring agent that needs to trace processes does not need root — it needs `SeDebugPrivilege`.

Configure these in the service definition. The service starts with the required privileges and a non-zero UID.

For applications that hard-check `getuid() == 0` and refuse to start otherwise, use the `uid0` utility:

```bash
$ uid0 legacy-daemon --config /etc/legacy.conf
```

`uid0` sets the process's projected UID to 0 without changing the token. The application sees `getuid() == 0` and starts, but its actual authority is still determined entirely by its token. This is a cosmetic change — UID 0 grants no additional access on Peios.

## Understanding why an application behaves differently

If a Linux application behaves unexpectedly, check these common causes:

### The application inspects its own capabilities

Some software calls `capget()` or reads `/proc/self/status` to check its capabilities. On Peios, all processes appear to have a full capability set in their Linux credentials. An application that branches on capability presence will take the "capable" path — but the underlying operation may still be denied by the Peios privilege check.

**Symptom:** The application attempts an operation (believing it has the capability) and receives a permission error.

**Fix:** Grant the corresponding Peios privilege in the service definition. Check the privilege reference for the mapping.

### The application uses setuid() for privilege dropping

A common Linux pattern: start as root, bind a privileged port, then call `setuid(nobody)` to drop privileges. On Peios, the `setuid()` call is a no-op. The application continues with the same token.

**Symptom:** Usually none — the application works fine because the token's authority was unchanged regardless. If the application checks `getuid()` after `setuid()` and expects the value to have changed, it may log a warning.

**Fix:** Generally no fix needed. The Peios-native pattern is to start the service with the correct token and privileges from the beginning — no privilege dropping required.

### The application relies on file ownership by UID

Some applications check `stat()` to verify file ownership matches the running UID. Because Peios projects UIDs from tokens, this usually works — the UID in `stat()` reflects the file owner's projected UID, and `getuid()` reflects the process's projected UID.

If the file was created by a different mechanism or the UID mapping is unexpected:

```bash
$ sd show /srv/data/app-data
Owner:  S-1-5-21-...-1013 (alice)

$ stat /srv/data/app-data
  Uid: ( 1013/   alice)
```

The UID in `stat()` matches the owner SID's projected UID. If they don't match, check the UID mapping in the directory.
