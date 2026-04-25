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

## Scope

The sole-authority claim applies to local FACS-managed filesystems (root, `/home`, `/var`, tmpfs, devtmpfs, and adopted foreign media). It does not apply to:

- `O_PATH` fds (not FACS-managed)
- NFS client mounts (dual authority with server)
- `/proc` (PIP-protected)
- `/sys` (hardcoded rule: writes require Administrators or SYSTEM)

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
