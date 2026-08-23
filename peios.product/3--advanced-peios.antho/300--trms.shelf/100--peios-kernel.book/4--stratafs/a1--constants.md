---
title: Constants
description: Every stratafs constant — filesystem identity, stratum flags, extended attributes, copy-up and staging markers — generated from the source.
---

Every value below is generated from the source by
`pkm/tools/gen-stratafs-constants.py`. Nothing here is transcribed by
hand, and the generator's `--check` mode fails if the two drift apart.

## Filesystem identity

| Constant              | Value        | Meaning                                         |
|-----------------------|--------------|-------------------------------------------------|
| `STRATAFS_MAGIC`      | `0x53545241` | Superblock magic, reported by `statfs` (§4.2.2) |
| `STRATAFS_NAME`       | `"stratafs"` | The name the filesystem registers under         |
| `STRATAFS_MAX_STRATA` | `16`         | Longest stratum stack accepted (§4.2.1)         |

`STRATAFS_MAGIC` is an alias for `STRATAFS_SUPER_MAGIC`, which is
declared in the header stratafs shares with KACS so that the mount
policy class keyed on it cannot drift (§4.6.4).

## Stratum flags

| Constant            | Value | Meaning                    |
|---------------------|-------|----------------------------|
| `STRATAFS_F_CREATE` | `0x1` | The `create` flag (§4.2.1) |
| `STRATAFS_F_RO`     | `0x2` | The `ro` flag              |
| `STRATAFS_F_AM`     | `0x4` | The `am` flag              |

## Extended attributes

| Constant                 | Value                               | Meaning                                                  |
|--------------------------|-------------------------------------|----------------------------------------------------------|
| `STRATAFS_XATTR_PREFIX`  | `"system.stratafs."`                | Reserved namespace; never forwarded to a provider (§4.7) |
| `STRATAFS_XATTR_ORIGIN`  | `"system.stratafs.origin"`          | Synthetic, read-only, hidden from listings (§4.7)        |
| `STRATAFS_XATTR_STAGING` | `"security.peios.stratafs_staging"` | Copy-up staging marker; also reserved (§4.5.2)           |

`STRATAFS_XATTR_STAGING` is an alias for `STRATAFS_STAGING_XATTR`,
declared in the shared header. Note the name it resolves to lies
outside the reserved `system.stratafs.` namespace, yet receives the
same treatment (§4.7).

The canonical security-descriptor attribute is KACS's, not
stratafs's; stratafs only detects it in order to exclude it from
copy-up replication (§4.6.3).

## Copy-up and staging

| Constant                        | Value                | Meaning                                     |
|---------------------------------|----------------------|---------------------------------------------|
| `STRATAFS_STAGE_MARKER_MAGIC`   | `0x53544731`         | Marker magic                                |
| `STRATAFS_STAGE_MARKER_VERSION` | `1`                  | Marker version                              |
| `STRATAFS_COPY_BUFFER_SIZE`     | `65536`              | Copy-up read/write chunk, in bytes (§4.5.2) |
| `STRATAFS_STAGE_PREFIX`         | `".stratafs-stage-"` | Staged-name prefix                          |
| `STRATAFS_RECOVERY_BATCH`       | `128`                | Names scanned per staging-recovery pass     |

### The staging marker

`struct stratafs_stage_marker` is packed and 24 bytes, all fields
little-endian. It is the value of the staging attribute above.

| Offset | Size | Field          | Type     |
|--------|------|----------------|----------|
| 0      | 4    | `magic`        | `__le32` |
| 4      | 2    | `version`      | `__le16` |
| 6      | 2    | `size`         | `__le16` |
| 8      | 8    | `boot_cookie`  | `__le64` |
| 16     | 8    | `mount_cookie` | `__le64` |

## Routing

The value `route_existing` returns (§4.5.1), as the Rust decision
core names it and as the C glue mirrors it. The discriminants match.

| C enumerator               | Value | Rust       |
|----------------------------|-------|------------|
| `STRATAFS_ROUTE_IN_PLACE`  | `0`   | `InPlace`  |
| `STRATAFS_ROUTE_COPY_UP`   | `1`   | `CopyUp`   |
| `STRATAFS_ROUTE_READ_ONLY` | `2`   | `ReadOnly` |

## The decision core

`stratafs-core` holds the stack-wide flag rules, provider selection,
and routing. Its flag bits match the C ones above exactly.

| Constant          | Value |
|-------------------|-------|
| `MAX_STRATA`      | `16`  |
| `FLAG_CREATE`     | `0x1` |
| `FLAG_READ_ONLY`  | `0x2` |
| `FLAG_ABSENT_MAY` | `0x4` |
| `FLAG_MASK`       | `0x7` |

The crate distinguishes these configuration errors. The C boundary
collapses all of them to `EINVAL`, so the distinction is not
observable to a caller (§4.2.1).

| Error            | Discriminant |
|------------------|--------------|
| `Empty`          | `1`          |
| `TooMany`        | `2`          |
| `UnknownFlag`    | `3`          |
| `RepeatedCreate` | `4`          |
| `CreateReadOnly` | `5`          |

## Build configuration

stratafs is built by `CONFIG_STRATAFS_FS`, a boolean option, so what it
builds is linked into `vmlinux` rather than loaded. It depends on
`CONFIG_SECURITY_PKM` and selects `FS_STACK`. Its sources are staged
into the kernel tree as `fs/stratafs`, separate from PKM's own
`security/pkm`. `CONFIG_STRATAFS_KUNIT_TEST` builds the in-kernel unit tests.

The translation units are:

- `super.o`
- `lookup.o`
- `inode.o`
- `file.o`
- `dir.o`
- `xattr.o`
- `copy_up.o`
