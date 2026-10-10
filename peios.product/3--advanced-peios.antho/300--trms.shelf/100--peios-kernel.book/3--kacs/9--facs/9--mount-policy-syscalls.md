---
title: Mount-policy syscall notes
description: The documented mount-policy argument fields, validation sequence and errors, retained alongside the kernel descriptor-storage contract for comparison.
---

These syscall notes preserve the argument and error descriptions from the
operator guide. For the kernel contract, use [File Descriptor
Storage](~peios/advanced-peios/peios-kernel/kacs/facs/descriptor-storage).

> [!WARNING]
> The sources disagree. These notes say `SeTcbPrivilege` is required; the
> kernel contract permits enabled `SeManageVolumePrivilege` or `SeTcbPrivilege`.
> The kernel contract also allows templates only with synthesising classes,
> caps them at 65,535 bytes, and rejects non-empty templates for deny-missing.
> The SDK wrapper documents different small-buffer handling from the raw
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
4. Checks the caller's privileges. `SeTcbPrivilege` is required.
5. Atomically updates the superblock's policy class, the template SD, and increments the generation counter.
6. Writes the new generation to `args.generation`.
7. Returns 0.

The change is **atomic at the superblock level** — every future access against any inode on this superblock sees the new policy. There is no transitional state where some inodes are under the old policy and others under the new.

### Privilege requirement

> [!IMPORTANT]
> `SeTcbPrivilege` is the privilege gating this call. The privilege is held by peinit and a handful of other TCB components; not by ordinary services or administrators. In practice this means mount policy is configured at boot (by peinit, applying mount-time configuration) or by a privileged management daemon. Ad-hoc policy changes are rare.

The reasoning: changing a mount's policy is an administrative decision that affects the entire filesystem's access semantics. It belongs in the TCB tier, not in the regular-administrator tier. An ordinary administrator who wants to change a mount's policy goes through a tool that itself has the privilege.

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
2. Checks the caller's privileges. `SeTcbPrivilege` is required to read.
3. Writes the policy class, generation, and template to `args` (template only if a buffer was provided).
4. Returns 0.

Like the write syscall, this is `SeTcbPrivilege`-gated. The mount policy is system-level state, exposed only to TCB-tier callers.

This is the kernel's read-back-the-current-policy interface. A management tool reads the policy, perhaps applies a transformation, and writes the new value back. The read-modify-write pattern is what most policy management code uses.

## Errors

Possible failures from `kacs_set_mount_policy`:

| Error | Cause |
|---|---|
| `-EBADF` | The fd is invalid. |
| `-EPERM` | The caller does not hold `SeTcbPrivilege`. |
| `-EINVAL` | Setting an `unmanaged` policy via the public ABI; setting an unknown policy value; non-zero reserved flags; malformed template SD; template size exceeded. |

Possible failures from `kacs_get_mount_policy`:

| Error | Cause |
|---|---|
| `-EBADF` | The fd is invalid. |
| `-EPERM` | The caller does not hold `SeTcbPrivilege`. |
| `-ERANGE` | A template buffer was provided but is smaller than the template. The required size is written to the output. |

In normal operation both calls succeed. Failures are typically privilege issues or malformed inputs.
