---
title: mke2fs
type: reference
description: "The Peios additions to mke2fs: the root_sddl and root_sd_file extended options, security-descriptor-aware population, and the compiled-in Peios defaults."
related:
  - peios/disks-and-filesystems/overview
  - peios/disks-and-filesystems/installing-to-disk
  - peios/disks-and-filesystems/formatting-with-security-descriptors
  - peios/mount-policies/sd-storage-by-filesystem
  - peios/security-descriptors/overview
  - peios/security-descriptors/inheritance
  - peios/security-descriptors/sd-command
---

`mke2fs` creates an ext2, ext3 or ext4 filesystem. Peios packages it from upstream e2fsprogs, so the generic surface — `-t`, `-b`, `-L`, `-O`, `-i`, `-m`, the full extended-option list — is exactly the upstream one and its canonical documentation is the `mke2fs(8)` man page shipped with the package.

This page documents only what Peios adds, which is security descriptors and a changed set of defaults.

```
mke2fs [-t ext4] [-E root_sddl=SDDL | root_sd_file=PATH] [-d DIRECTORY] DEVICE
```

## Extended options

Peios adds two options to `-E`. Both set the security descriptor written to the new filesystem's root directory and to `lost+found`, in the `security.peios.sd` extended attribute.

| Option | Meaning |
|---|---|
| `root_sddl=SDDL` | The descriptor as an inline SDDL string. |
| `root_sd_file=PATH` | The descriptor as SDDL read from `PATH`. |

`root_sd_file` exists because `-E` takes a comma-separated list and SDDL contains commas. Any descriptor with more than one ACE, or with a conditional expression, is easier to pass in a file than to quote on a command line.

The file holds **SDDL text, not binary** — it is the same string `root_sddl` would take, in a file. Trailing newlines are stripped, so an ordinary one-line text file works. Anything else in the file is part of the descriptor: there is no comment syntax and no blank-line handling.

Both options are parsed in the order they appear. If you give both, or the same one twice, the last one wins.

If the SDDL does not parse, `mke2fs` prints `Invalid root SDDL:` followed by the string it was given, and exits without creating a filesystem.

Neither option has a default. Omit both and the filesystem is created with no security descriptor on its root, which is upstream behaviour — mount it under a synthesising policy or it will be unreachable.

### Example

```
mke2fs -q -t ext4 -E root_sddl="O:SYG:SYD:(A;OICI;GA;;;SY)(A;OICI;GA;;;BA)" /dev/vda2
```

Confirm the result without mounting the filesystem:

```
debugfs -R "ea_list <2>" /dev/vda2
```

```
Extended attributes:
  security.peios.sd (96)
```

Inode 2 is the root directory. To read the descriptor back as bytes rather than just confirm its presence, use `debugfs -R "ea_get -V <2> security.peios.sd"`.

## Security-descriptor-aware population

`-d DIRECTORY` populates the new filesystem from an existing directory. On Peios this pass also computes a security descriptor for each node it creates.

The source node's explicit descriptor is read from its **`user.peios.sd`** extended attribute — not `security.peios.sd`, which is sealed on a live Peios filesystem and requires `CAP_SYS_ADMIN` on a Linux build host. Both names are excluded from the generic extended-attribute copy, so neither is propagated verbatim.

For each node:

| Source node | Parent in the new filesystem | Result |
|---|---|---|
| Has `user.peios.sd` | Has a descriptor | Explicit and inherited ACEs merged, written to `security.peios.sd`. |
| Has `user.peios.sd` | Has none | The explicit descriptor written verbatim. |
| Has no `user.peios.sd` | Either | Nothing written. The node inherits on first access instead. |

Directories are stamped before their contents are visited, so a child always reinherits against a parent whose descriptor is already on disk.

The merge follows the same rules as [inheritance](~peios/security-descriptors/inheritance) on a live system, and runs entirely in userspace — no kernel and no KACS are involved, so a populated Peios filesystem can be built on a host that is not running Peios.

## Peios defaults

`mke2fs` reads its defaults from a profile. Peios changes three of them, and the changed profile is **compiled into the binary**, so it applies whether or not a configuration file exists.

| Setting | Upstream | Peios | Reason |
|---|---|---|---|
| `inode_size` | 256 | **512** | Keeps a typical security descriptor in the inode's inline extended-attribute space, where reading it costs no extra I/O. |
| `default_mntopts` | `acl,user_xattr` | **`user_xattr`** | Peios uses security descriptors, not POSIX ACLs. |
| ext4 features | — | **+ `ea_inode`** | Lets an oversized descriptor spill into its own inode rather than failing to fit. |

`base_features`, `blocksize`, `inode_ratio` and `enable_periodic_fsck` are unchanged from upstream.

The ext4 **`quota`** feature is deliberately *not* enabled. The Peios kernel is built with `CONFIG_QUOTA` and `CONFIG_QUOTACTL` but without `CONFIG_QFMT_V2`, and ext4 refuses to mount a filesystem carrying the quota feature unless the vfsv1 on-disk format is compiled in. Enabling it in the profile therefore produced filesystems the kernel would not mount. Turning it on again is a pair of changes that have to land together — the kernel option, then the feature.

Resolution order for the profile, highest first:

1. The file named by the `MKE2FS_CONFIG` environment variable, if set.
2. `/etc/mke2fs.conf`, if present.
3. The compiled-in Peios profile.

Peios ships no `/etc/mke2fs.conf`, so the compiled-in profile is what you get unless you deliberately supply a file. Supplying one replaces the profile wholesale — the compiled-in values are a fallback, not a layer underneath — so a partial configuration file silently reverts every setting it does not mention to the upstream default.

## Exit status

| Code | Meaning |
|---|---|
| `0` | Success. |
| `1` | Failure. Includes an unparseable `root_sddl`/`root_sd_file` value, an unreadable `root_sd_file`, and a failure to write the descriptor to the new filesystem. |

`mke2fs` distinguishes no further; unlike `e2fsck`, it has no bitwise-summed status. When the security-descriptor options fail they report the offending value on standard error before exiting, and no filesystem is created.

## See also

For the model behind the two options — why stamping beats mount-time synthesis, and what one inheritable ACE on the root does and does not express — read [Formatting with security descriptors](~peios/disks-and-filesystems/formatting-with-security-descriptors).

For reading and rewriting descriptors on a mounted filesystem, read [The sd command](~peios/security-descriptors/sd-command).

For how the descriptor is stored, and when `ea_inode` becomes load-bearing, read [SD storage by filesystem](~peios/mount-policies/sd-storage-by-filesystem).
