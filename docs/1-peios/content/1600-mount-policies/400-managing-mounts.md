---
title: Managing mounts
type: concept
description: Mount policies are set via kacs_set_mount_policy and read via kacs_get_mount_policy. Changes are lazy — the kernel maintains a generation counter that invalidates in-memory cached state on next access rather than walking the filesystem. This page covers the syscalls, the generation counter, and the privilege rules.
related:
  - peios/mount-policies/overview
  - peios/mount-policies/policy-classes
  - peios/mount-policies/sd-storage-by-filesystem
  - peios/privileges/overview
---

A mount's policy is set via a syscall, read via a syscall, and otherwise sits as kernel-internal state on the filesystem's superblock. Mount-policy changes are administrative — they require `SeTcbPrivilege` — and they take effect lazily, without the kernel walking the filesystem to update anything.

This page covers the two syscalls (`kacs_set_mount_policy`, `kacs_get_mount_policy`), the generation counter that makes lazy invalidation work, and what does and does not happen at a policy change.

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

`SeTcbPrivilege` is the privilege gating this call. The privilege is held by peinit and a handful of other TCB components; not by ordinary services or administrators.

The reasoning: changing a mount's policy is an administrative decision that affects the entire filesystem's access semantics. It belongs in the TCB tier, not in the regular-administrator tier. An ordinary administrator who wants to change a mount's policy goes through a tool that itself has the privilege.

In practice this means mount policy is configured at boot (by peinit, applying mount-time configuration) or by a privileged management daemon. Ad-hoc policy changes are rare.

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

## The generation counter

A subtle but important feature: the kernel maintains a **monotonic generation counter** per superblock. Each successful `kacs_set_mount_policy` (or template change) increments it.

The purpose is **lazy invalidation**.

Without the counter, a policy change would either need to immediately propagate to every cached SD on the filesystem (expensive — could be millions of inodes) or accept that cached SDs from before the change remain valid (incorrect — the new policy might say different things).

With the counter, the kernel can do something smarter:

1. Each in-kernel cached SD or synthesised entry records the generation it was derived from.
2. At access time, the kernel compares the cached entry's generation against the superblock's current generation.
3. If they match, the cached entry is current; use it.
4. If they differ, the cached entry is stale; discard it and re-derive.

The kernel does **not** walk the filesystem at the policy change. The walk happens implicitly, one inode at a time, as accesses arrive. An access that arrives 30 seconds after the policy change is the first to invalidate that specific inode's cached state; the access pays a small cost to re-derive, but every subsequent access uses the new cached state.

This is why mount policy changes are cheap to apply. The expensive work (walking inodes) never happens; what happens instead is per-inode re-derivation on first access after the change.

### What the generation counter affects

The counter affects in-kernel **cached** state derived from the mount policy:

- **Missing-SD synthesised entries.** If a file had a missing SD and was synthesised on-the-fly, the synthesised SD is cached. A policy change invalidates this cache; the next access re-synthesises.
- **Ephemeral-synthesis caches for `facs_synthesize_ephemeral` mounts.** Same.
- **Template-derived information** — the kernel's representation of the mount template is regenerated on next access.

The counter does **not** affect:

- **On-disk SDs.** A file that has a stored SD continues to have that SD. The policy change doesn't rewrite stored SDs.
- **Already-open file descriptors.** The cached granted mask on an fd is independent of the mount-policy generation; it's the result of the access check at open time. Policy changes after open don't affect open fds. (This is the standard check-at-open model.)
- **Inodes not currently in cache.** They have nothing to invalidate; the next access just goes through the normal path with the current policy.

### Reading the counter

The generation counter is exposed in the output of `kacs_get_mount_policy`. A management tool can read the counter to know when policy was last changed, or compare against a previously-read value to detect external changes.

The counter is per-superblock; different filesystems have unrelated counter values. The counter starts at some implementation-defined value at mount time and increases monotonically with each policy change.

## What happens at a policy change

To summarise, when `kacs_set_mount_policy` succeeds:

1. The superblock's policy class field is updated.
2. The superblock's template SD is updated.
3. The superblock's generation counter is incremented.
4. Open file descriptors against files on this mount are unaffected (cached granted masks intact).
5. Cached in-memory state derived from the old generation will be invalidated on first access after the change.
6. Files with stored SDs continue to have those SDs.
7. The filesystem itself is not walked, not modified, not reorganised.

The change is essentially a small superblock update plus a lazy invalidation marker. The work happens at future accesses, distributed across actual usage.

## What policy changes do not do

A few clarifications:

- **They don't rewrite SDs on disk.** A change from `facs_synthesize_ephemeral` to `facs_synthesize_persistent` doesn't go back and write synthesised SDs to disk. Files that were synthesised under the old policy continue to have no on-disk SD; the next access re-synthesises (now writes back, per the new persistent policy).
- **They don't close open files.** Processes with handles to files on the mount continue to have those handles. The cached granted masks are unchanged.
- **They don't propagate across mounts.** A policy change on one mount doesn't affect any other mount, even if they reference the same underlying device (per the per-superblock rule).
- **They don't change the FACS handle model.** The new policy applies to future access checks; existing handles use their cached masks per usual.

## Use patterns

A handful of common patterns for managing mount policy:

**Boot-time policy.** peinit applies the policy class and template for each mounted filesystem at boot. The configuration source is typically registry-based; peinit reads the configuration and calls `kacs_set_mount_policy` for each mount.

**Migration from a non-Peios filesystem.** Mount with `facs_synthesize_persistent` initially. Let usage gradually adopt files into having stored SDs. Once enough have been adopted, switch to `facs_deny_missing` (or leave it as `synthesize_persistent` if you want the synthesis-on-missing safety net).

**Removable media insertion.** When a removable filesystem is mounted (a USB drive, an optical disc), the mount setup chooses `facs_synthesize_ephemeral`. The volume's contents become reachable without modifying the on-disk metadata; ejection cleanly leaves the media untouched.

**Policy uplift on a hardened deployment.** A deployment starting with `facs_synthesize_ephemeral` everywhere (permissive) can migrate to `facs_synthesize_persistent` (filling in stored SDs) and then to `facs_deny_missing` (strict mode). Each transition is one `kacs_set_mount_policy` call per mount.

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
