---
title: Mount-policy syscall notes
description: The documented mount-policy argument fields, validation sequence and errors, retained alongside the kernel descriptor-storage contract for comparison.
---

These syscall notes preserve the argument and error descriptions from the
operator guide. For the kernel contract, use [File Descriptor
Storage](~peios/advanced-peios/peios-kernel/kacs/facs/descriptor-storage).

> [!WARNING]
> The privilege gate has been source-verified below, but other descriptions
> retained from the operator guide still differ. The kernel contract allows
> templates only with synthesising classes,
> caps them at 65,535 bytes, and rejects non-empty templates for deny-missing.
> The [SDK wrapper](~peios/developing-for-peios/sdk-reference/sdk-files/mount-policy)
> documents different small-buffer handling from the raw
> syscall error table below. These differences need implementation verification;
> do not use these notes to infer a broader grant of access or a safe retry.

## kacs_set_mount_policy

The write syscall:

```
result = kacs_set_mount_policy(fd, args)
```

Where `fd` is a file descriptor referring to any object on the target superblock (the kernel uses the fd to identify which superblock — the file itself does not need to be the root of the mount). `args` is a `kacs_mount_policy_args` struct:

| Field | Meaning |
|---|---|
| `policy` | The new policy class (one of `KACS_MOUNT_POLICY_DENY_MISSING`, `KACS_MOUNT_POLICY_SYNTHESIZE_EPHEMERAL`, `KACS_MOUNT_POLICY_SYNTHESIZE_PERSISTENT`). |
| `flags` | Reserved; must be zero. |
| `generation` | (Output) The new generation counter value after the change. |
| `template_sd_ptr`, `template_sd_len` | Optional mount-level SD template. Max 64 KiB. |

The kernel:

1. Validates the fd and identifies the superblock.
2. Validates the policy value. Attempts to set `KACS_MOUNT_POLICY_UNMANAGED` (which is not settable via this ABI) are rejected with `-EINVAL`.
3. Validates the template SD if provided — must parse, must be within size limits.
4. Checks the caller's privileges. Enabled `SeManageVolumePrivilege` or `SeTcbPrivilege` is required, and marking the privilege as used must succeed.
5. Atomically updates the superblock's policy class, the template SD, and increments the generation counter.
6. Writes the new generation to `args.generation`.
7. Returns 0.

The change is **atomic at the superblock level** — every future access against any inode on this superblock sees the new policy. There is no transitional state where some inodes are under the old policy and others under the new.

### Privilege requirement

> [!IMPORTANT]
> In kernel source `8e0e22de3a59cad506bbbf8873de456e16ad272d`, both policy reads and writes use the [volume-management gate](https://github.com/peios/pkm/blob/8e0e22de3a59cad506bbbf8873de456e16ad272d/kacs/capability.c#L613-L637): enabled `SeManageVolumePrivilege` or `SeTcbPrivilege`, with successful privilege-use marking. Administrator membership alone is insufficient. The [write gate](https://github.com/peios/pkm/blob/8e0e22de3a59cad506bbbf8873de456e16ad272d/kacs/mount_policy.c#L369-L380) and [read gate](https://github.com/peios/pkm/blob/8e0e22de3a59cad506bbbf8873de456e16ad272d/kacs/mount_policy.c#L479-L496) establish this for the pinned source, not a deployed build or a historical release boundary.

Changing a mount's policy affects the entire filesystem's access semantics.
`SeManageVolumePrivilege` can author synthesised policy and shadow existing
paths; see its [authority warning](~peios/privileges/categories#what-semanagevolumeprivilege-is-actually-worth).
The [SDK wrappers](https://github.com/peios/libpeios/blob/de0018bdcaed14abb796aeccec9c8387fd30e452/src/file.rs#L451-L575) at libpeios
`de0018bdcaed14abb796aeccec9c8387fd30e452` add no TCB-only gate despite their
comments. The [command diagnostic](~peios/mount-policies/mount#kacs-mount-policy)
also retains a TCB-only hint. Do not automatically grant TCB or globally remap
`CAP_SYS_ADMIN`. A ready-to-use operator interface for changing an existing
policy is [not established here](~peios/mount-policies/managing-mounts#before-changing-an-already-mounted-policy).

The generated [KACS ABI trace table](~peios/advanced-peios/peios-kernel/kacs/kacs-abi)
retains the `KACS_MP_TCB_DENIED` name and TCB-only descriptions. Those labels
do not override the source-verified gate; this clarification leaves the
generated table unchanged.

### The template SD

The optional template SD is the default SD used during synthesis when the parent's inheritance does not yield one. The kernel stores the template on the superblock; subsequent synthesis-on-missing calls use it.

The template is a complete self-relative SD — owner, primary group, DACL, optional SACL. The kernel validates the template at policy-set time:

- Must be in self-relative format.
- Must include an owner (an SD without one is malformed and rejected).
- Must fit within 65,535 bytes total; the template specifically is capped at 64 KiB.
- ACLs and ACEs must parse.

A bad template at policy-set time is rejected with `-EINVAL`; the current policy and template are unchanged.

The template can be omitted entirely (zero pointers) for mounts that don't need one. The synthesis chain then falls through to the hardcoded fallback for any file whose parent doesn't yield an SD.

## kacs_get_mount_policy

The read syscall:

```
result = kacs_get_mount_policy(fd, args)
```

Same `fd` and `args` semantics, returning the current policy class, current template (if buffer provided), and current generation counter.

The kernel:

1. Validates the fd, identifies the superblock.
2. Checks the caller's privileges. Enabled `SeManageVolumePrivilege` or `SeTcbPrivilege` is required, with successful privilege-use marking.
3. Writes the policy class, generation, and template to `args` (template only if a buffer was provided).
4. Returns 0.

Like the write syscall, this uses the pinned-source [volume-management gate](#privilege-requirement). A successful policy query does not grant authority to bypass any other mount or file-access checks.

This is the kernel's read-back-the-current-policy interface. A management tool reads the policy, perhaps applies a transformation, and writes the new value back. The read-modify-write pattern is what most policy management code uses.

### Reading the generation

Compare the value from `kacs_get_mount_policy` with your earlier read to detect
a change. Initial values are implementation-defined, and values from different
superblocks are unrelated. The counter identifies changes, not a wall-clock
change time. See the [kernel administration
contract](~peios/advanced-peios/peios-kernel/kacs/facs/descriptor-storage#administration)
for generation increments and cache invalidation.

## Errors

Possible failures from `kacs_set_mount_policy`:

| Error | Cause |
|---|---|
| `-EBADF` | The fd is invalid. |
| `-EPERM` | Neither accepted privilege is enabled, or privilege-use marking failed. |
| `-EINVAL` | Setting an `unmanaged` policy via the public ABI; setting an unknown policy value; non-zero reserved flags; malformed template SD; template size exceeded. |

Possible failures from `kacs_get_mount_policy`:

| Error | Cause |
|---|---|
| `-EBADF` | The fd is invalid. |
| `-EPERM` | Neither accepted privilege is enabled, or privilege-use marking failed. |
| `-ERANGE` | A template buffer was provided but is smaller than the template. The required size is written to the output. |

In normal operation both calls succeed. Failures are typically privilege issues or malformed inputs.
