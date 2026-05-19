---
title: Special cases
type: concept
description: O_PATH fds skip the handle model. exec needs two gates. Append-only handles enforce intent. The sticky bit and POSIX ACLs don't work. NFS clients are authorised locally but enforced remotely. This page covers the edges of FACS — the cases that the standard model doesn't cover by itself.
related:
  - peios/file-access/overview
  - peios/file-access/the-handle-model
  - peios/file-access/opening-files
  - peios/file-access/managing-file-security
  - peios/mount-policies/overview
---

The handle model handles most of file access cleanly. But files have edges — operations that bypass the model, semantics that don't fit, filesystems whose behaviour FACS cannot fully control. This page covers those edges.

Each of the special cases below is something that someone debugging FACS behaviour will eventually hit. Knowing the rules ahead of time keeps the gotchas from being surprises.

## O_PATH — fds without a cached mask

`O_PATH` is a Linux flag for opening a file in a "path-only" mode. The fd that comes back can be used to refer to the file (for `openat(dirfd, ..., 0, fd)`, for `fstatat`, for path manipulation) but cannot be used for actual data operations.

Under FACS, an O_PATH open does **not** run a full AccessCheck. The fd is not FACS-managed; it has no cached granted mask. Operations that would normally consult the cache either work unconditionally (because they don't need any access) or use a fresh live AccessCheck (because they do):

| Operation on O_PATH fd | Behaviour |
|---|---|
| `fstat`, `fstatat` | Works without access check. The fd is a path reference; getting stat info is allowed. |
| `openat` using the fd as dirfd | Normal — runs AccessCheck for the new open. The dirfd's O_PATH status doesn't affect the new fd. |
| `kacs_get_sd` with AT_EMPTY_PATH | Runs a live AccessCheck (the fd has no cached mask to consult). |
| `kacs_set_sd` with AT_EMPTY_PATH | Same — live AccessCheck. |
| `read`, `write`, `mmap` | **Denied** with `EBADF`. The fd cannot be used for data operations. |
| `fchmod`, `fchown`, `fgetxattr`, `fsetxattr`, `ioctl` | **Denied** with `EBADF`. |

O_PATH is useful for path manipulation — keeping a reference to a directory while traversing the tree, or referring to a file by fd rather than by path. For these uses, the lack of a cached mask is irrelevant.

The catch: a process that wants to do *anything* with an O_PATH fd beyond path navigation needs to reopen it. The reopen is a fresh access check that decides what the resulting fd can actually do.

## The exec dual gate

Exec is the only operation in v0.20 that performs a **use-time** access check rather than relying on the cached mask. The reasoning: exec changes the process's identity (via the new binary's PIP) and effectively replaces it; the open-time decision is no longer the right one to use.

Specifically, `execveat(AT_EMPTY_PATH)` on an open fd:

1. Runs a fresh AccessCheck against the file's current DACL using the caller's current effective token.
2. Requires both the **`+x` mode bit** on the file and **`FILE_EXECUTE`** on the caller's access to be present.

The two checks answer two different questions:

- **`+x` on the file** means *this file is intended to be run as a program*. It is a property of the file itself, set by whoever owns it — the file's author saying "this is an executable, not data". A file without `+x` is data; trying to exec it fails regardless of who is asking, because exec on data is meaningless.
- **`FILE_EXECUTE` on the access** means *this caller is allowed to execute this program*. It is an access decision against the DACL — the question of whether this principal, on this token, is authorised to run this binary.

Both have to be true for exec to proceed. A data file (no `+x`) is not runnable by anyone; an executable file the caller is not authorised for is runnable in principle but not by this caller.

The dual gate is the v0.20 exception to the handle model. The reason for live evaluation here is that exec's consequences are large enough — the binary that runs is what the kernel will then trust at the verified PIP level — that running on a stale cache is the wrong default.

`mmap(PROT_EXEC)` is **different** from exec. It uses the cached mask (`FILE_EXECUTE` from the open), and additionally runs the LSV mitigation if enabled. mmap is not the same as exec; the dual-gate-with-live-check applies only to exec specifically.

## Append-only handles

A handle opened with `FILE_APPEND_DATA` granted but **not** `FILE_WRITE_DATA` is an append-only handle. The kernel enforces this strictly:

- `write()` at the current offset is allowed only if the current offset is at end-of-file. Otherwise denied.
- `pwrite()` at any offset other than end-of-file is denied (RWF_APPEND-style).
- Mapping the file shared writable (`mmap(MAP_SHARED, PROT_WRITE)`) is denied.
- `ftruncate` to extend the file is denied (cannot rewind via truncate).
- `fallocate` modes that would mutate (FALLOC_FL_PUNCH_HOLE, FALLOC_FL_COLLAPSE_RANGE, FALLOC_FL_ZERO_RANGE) are denied.

Operations that legitimately only append — POSIX `write` with O_APPEND, `RWF_APPEND` writes — work normally. The kernel makes the data lands at end-of-file.

The use case: log files that should be append-only. A logger holds a handle with `FILE_APPEND_DATA` but not `FILE_WRITE_DATA`; it can write log lines but cannot rewrite earlier ones. Even if the logger is compromised, the existing log entries are safe from modification through this handle.

Append-only is the FACS expression of the "secure log" pattern. It exists at the right-mask level, not as a separate file attribute.

## sticky bit — no effect under FACS

The traditional Unix sticky bit on a directory restricts file deletion within: only the owner of a file (or the owner of the directory) may unlink files in a sticky-bit directory. This is what makes `/tmp` work.

Under FACS, **the sticky bit has no effect**. Deletion is gated by `FILE_DELETE_CHILD` on the parent directory's SD, period. The sticky bit's semantics are not encoded.

The reason: FACS's access model is comprehensive enough that the sticky bit is unnecessary. A `/tmp` directory's DACL grants the directory's `FILE_DELETE_CHILD` to the appropriate principals (typically just the owner or the file owner, mediated through OWNER RIGHTS); this is the same effect the sticky bit had, expressed in the DACL.

For `/tmp` specifically, the Peios-default DACL provides equivalent semantics: each user can create files in `/tmp` (FILE_ADD_FILE granted to Authenticated Users), each file's owner can delete their own (FILE_DELETE_CHILD inherited per-file from OWNER RIGHTS ACEs), but a user cannot delete another user's files.

A directory whose mode includes the sticky bit (visible to `ls -l` as a `t`) is informational; the mode is derived from the SD by FACS. The bit can be set but has no enforcement consequence.

## POSIX ACLs — replaced by KACS

The Linux POSIX ACLs (set via `setfacl` and stored as `system.posix_acl_access` and `system.posix_acl_default` xattrs) are **not honoured by FACS**. They are replaced by KACS DACLs.

Specifically:

- Writes to `system.posix_acl_access` and `system.posix_acl_default` xattrs are unconditionally denied.
- Existing POSIX ACL xattrs on files (carried over from a pre-Peios system, say) are ignored. FACS uses the KACS DACL exclusively.

The kernel will not silently translate POSIX ACLs to KACS DACLs. Migrating from a Linux system with POSIX ACLs requires re-writing the SDs in KACS form. Tools that can do this conversion exist in the migration tooling; the kernel does not do it on the fly.

## fchown — denied on FACS-managed fds

The legacy `fchown` syscall changes a file's owner UID/GID. Under FACS, this is denied entirely:

- `fchown()` on a FACS-managed fd returns `-EACCES`.
- `chown()` and `lchown()` are similarly redirected through the SD path.

Changing ownership goes through `kacs_set_sd` with `OWNER_SECURITY_INFORMATION`. The KACS semantics for ownership (covered in [Managing file security](~peios/file-access/managing-file-security)) replace the legacy mode-and-owner duo.

The kernel surfaces the file's owner SID's projected UID as the result of `stat`-style queries, so `ls -l` shows a UID. But the UID is derived from the owner SID; setting it via `fchown` is not the way.

## NFS — dual authority

NFS client mounts are a special case. The underlying filesystem is on a remote server; the server enforces its own access control independent of what the client thinks. FACS on the client side cannot reach into the server's authorisation; it can only express its local view.

The pattern Peios uses: NFS client mounts are configured with the `synthesize_ephemeral` [mount policy](~peios/mount-policies/overview). The client synthesises a local SD for each file accessed (per the mount template), runs AccessCheck locally, and either authorises the operation or denies it. If authorised, the operation is forwarded to the server, which may then deny it for its own reasons.

The consequence: a locally-authorised open can still produce I/O errors when the server refuses. A caller may successfully `open(O_RDONLY)` against an NFS file (FACS's local synthesis decided to grant) but the `read()` returns `-EACCES` from the server.

This is "dual authority": the client and the server both have a say, and both have to permit. The client's denial is final on the client side; the server's denial is final on the server side. There is no single source of truth for what is allowed.

Implications:

- **Don't trust FACS results on NFS for security purposes.** The local FACS decision is "the client will let this go forward"; the server may still refuse. If you need a security guarantee, the server's access control is what matters.
- **Expect I/O errors from server-side denial.** A successful open does not guarantee a successful read. Handle `EACCES` (or `EIO`) from the operation, not just from the open.
- **The synthesised SD is local.** Changes to the file's actual SD on the server are not visible to FACS's local synthesis. Tools that want to inspect the real SD need to query the server.

NFS server mounts (where Peios is the server) work the other direction: FACS enforces the SD on the local files; the protocol exposes it. The remote client's view of what is allowed is whatever the protocol negotiates, which may be limited by NFS-protocol-level restrictions but is ultimately decided by FACS.

## `/proc` and `/sys`

`/proc` and `/sys` are kernel-managed pseudo-filesystems. They are not FACS-managed in the standard sense — their mount policy is **unmanaged**, which means the FACS handle model does not apply.

What does happen:

- File operations under `/proc/<pid>/*` route through the process's PSB / process SD checks (the two-check rule from PIP). Access is decided per-operation against the target process.
- `/sys/kernel/security/kacs/*` files have explicit SDs on them (set up by the kernel) and are accessed via the kernel's own check logic.
- General `/proc` files (`/proc/uptime`, `/proc/cpuinfo`) are world-readable by convention.
- `/sys` writes are restricted to `BUILTIN\Administrators` and `SYSTEM` by hardcoded rule.

The result: operations on `/proc` and `/sys` work, but they don't go through the FACS handle model. The cached mask on the fd from opening one of these files is meaningless; the per-operation check is what gates access.

This is why `cat /proc/self/status` produces output without any apparent FACS involvement — the access is granted by the kernel's `/proc`-specific rules, and the kernel just makes data available.

The mount-policy classes are covered in [Mount policies](~peios/mount-policies/overview). `unmanaged` is the special class for kernel-managed filesystems; it cannot be set via the public ABI.

## Whiteouts in renameat2

`renameat2(RENAME_WHITEOUT)` — the Linux-specific flag for creating a "whiteout" entry as part of a rename (used by overlay filesystems) — is **unsupported** on FACS-managed filesystems in v0.20. Calls with this flag fail with `-EOPNOTSUPP`.

The whiteout semantics are complex enough that FACS in v0.20 chooses not to support them rather than partially support them. Overlay-style filesystems can still work, but they do so through different mechanisms; the RENAME_WHITEOUT flag is not the path on FACS-managed mounts.

For most administrators this is invisible — overlayfs and union-style filesystems are uncommon in server deployments. The flag's absence is worth knowing if you are building such a system.

## Summary table

The special cases at a glance:

| Case | What is different |
|---|---|
| O_PATH | No cached mask; data operations denied; live check for SD ops |
| exec via execveat | Live AccessCheck plus Linux `+x` mode bit |
| Append-only handles | Write-at-end only; mmap-shared-writable and truncate denied |
| Sticky bit | No effect — the DACL is the gate |
| POSIX ACLs | Replaced by KACS; xattr writes denied |
| fchown | Denied on FACS-managed fds; use kacs_set_sd |
| NFS client | Dual authority; local FACS plus remote enforcement |
| `/proc` and `/sys` | Unmanaged mount policy; per-operation check by kernel-specific rules |
| renameat2 RENAME_WHITEOUT | Unsupported (`-EOPNOTSUPP`) |

Each is a deliberate decision. Some reflect Linux compatibility (POSIX ACLs replaced); some reflect security policy (exec dual gate, append-only enforcement); some reflect the model's limits (NFS dual authority). Knowing them keeps the surprises from being surprises.
