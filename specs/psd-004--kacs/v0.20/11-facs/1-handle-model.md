---
title: The Handle Model
---

FACS — the File Access Control Shim — is the file-specific enforcement surface of KACS. It replaces Linux DAC (UID/GID/mode-bit checks) with SD-based evaluation on files.

The enforcement model follows the handle pattern: AccessCheck runs once at open time, the granted access mask is cached on the file descriptor, and subsequent operations check the cached mask. Limited exceptions exist where a live AccessCheck is used instead (e.g., v0.20 `execveat(AT_EMPTY_PATH)` — see use-time semantics).

Every open file description on a local FACS-managed filesystem carries a single **granted access mask** in its LSM security blob. This mask is set once — at open time — and never modified. The primary authorization check for subsequent operations is:

```
(fd.granted & required) == required ? allow : deny
```

The granted mask is immutable for the fd's entire lifetime, regardless of subsequent SD changes. Open handles survive SD modifications — if a file's DACL is modified after a process has it open, the existing fd retains its cached grants.

## Mount policy

For kernel purposes, every mounted filesystem exposes exactly one FACS mount-policy class:

- `unmanaged` — the mount is outside the ordinary FACS handle model. KACS MUST NOT stamp granted access masks onto ordinary file descriptions from this mount. `/proc` and `/sys` use this class in `v0.20`.
- `facs_deny_missing` — the mount is FACS-managed. Missing SDs deny access per [sd-storage](./sd-storage). Peios system mounts (root, `/home`, `/var`, tmpfs, devtmpfs) use this class by default.
- `facs_synthesize_ephemeral` — the mount is FACS-managed. Missing SDs are synthesized per [sd-storage](./sd-storage) and cached only in memory. Removable foreign media and NFS client mounts use this class in `v0.20`.
- `facs_synthesize_persistent` — the mount is FACS-managed. Missing SDs are synthesized per [sd-storage](./sd-storage) and written back immediately. Adopted foreign media uses this class.

The three `facs_*` classes are the only FACS-managed mount classes. `unmanaged` mounts stay outside open-time granted-mask stamping.

Mount policy is scoped to the kernel superblock policy object, not to an
individual pathname or bind mount. If several paths or bind mounts refer to the
same superblock, they observe the same FACS mount-policy class.

The kernel default classifier is conservative:

- hardcoded pseudo filesystems such as `/proc` and `/sys` are `unmanaged`;
- known foreign or non-persistent client filesystems that cannot reliably store
  the canonical KACS SD xattr, such as FAT, exFAT, and NFS client mounts, are
  `facs_synthesize_ephemeral`;
- every other filesystem defaults to `facs_deny_missing` unless a trusted
  policy agent adopts it through `kacs_set_mount_policy`.

Userspace MUST NOT be able to set a superblock to `unmanaged` through the public
KACS ABI. `unmanaged` is reserved for the kernel classifier and hardcoded
pseudo-filesystem rules.

## Scope

The sole-authority claim applies to local FACS-managed filesystems (root, `/home`, `/var`, tmpfs, devtmpfs, and adopted foreign media). It does not apply to:

- `O_PATH` fds (not FACS-managed)
- NFS client mounts (`facs_synthesize_ephemeral`, but dual authority with server)
- `/proc` (`unmanaged`, PIP-protected)
- `/sys` (`unmanaged`, hardcoded rule: writes require Administrators or SYSTEM)

## Handle acquisition

An fd carries its granted mask through all acquisition paths. fd transfer is an intentional capability-delegation mechanism:

- **dup/dup3** — same file description, same rights.
- **fork/clone** — child inherits fds, same rights.
- **SCM_RIGHTS** — the fd is a capability token; possession is authorization. The receiver's identity is not re-checked.
- **pidfd_getfd()** — gated by AccessCheck against the target process's SD for PROCESS_DUP_HANDLE. If the SD allows it, the caller gets the fd with its full granted mask.
- **exec** — fds without FD_CLOEXEC survive, same rights.

The security boundary is at open time. All subsequent transfers carry the granted mask unchanged.

> [!INFORMATIVE]
> This means mandatory subject policy (MIC, PIP) is evaluated once, at open time, against the opener's identity. A high-integrity process that opens a file and passes the fd to a low-integrity process has effectively delegated its access. This is the handle model: authority is on the handle, not the holder.
