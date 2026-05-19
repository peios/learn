---
title: The handle model
type: concept
description: Every FACS-managed file descriptor carries a granted access mask, stamped at open by AccessCheck and immutable for the fd's lifetime. Every operation through the fd checks the operation's required mask against this cached value. This page covers what the cache contains, what operations consult it, and the implications of immutability.
related:
  - peios/file-access/overview
  - peios/file-access/opening-files
  - peios/file-access/managing-file-security
  - peios/file-access/special-cases
  - peios/access-decisions/overview
---

The handle model is the rule that an open file descriptor carries a fixed snapshot of access permissions, taken at the moment of open. Every operation through the fd consults this snapshot — not the file's current SD, not the calling token's current state, not anything else. The snapshot is the granted access mask, an immutable 32-bit value attached to the fd.

This page covers what the snapshot contains, which operations consult it, why immutability is the right choice, and the implications for handle transfer between processes.

## What is on the fd

When `open` succeeds, the kernel attaches several things to the resulting fd. The KACS-relevant pieces:

| Field | Set at | Mutable after open? |
|---|---|---|
| Granted access mask | AccessCheck at open | **No** |
| Continuous audit mask | AccessCheck at open (if alarm ACEs matched) | No |
| FACS-managed flag | Open path | No |
| (Filesystem state: position, mode, etc.) | open | Mutable per operation |

The granted access mask is the central object. It is whatever AccessCheck decided the caller's effective token was entitled to on this file at this moment. The bits set are the rights the fd holder has; the bits not set are rights they do not have.

The continuous audit mask is the union of all alarm ACEs that matched at open time. Every subsequent operation through the fd will check against this mask and emit a continuous-audit event if the operation's required mask overlaps it. See [The SACL](~peios/security-descriptors/the-sacl) and [Audit ACEs](~peios/auditing/audit-aces).

The FACS-managed flag distinguishes fds that go through the handle model from those that don't. O_PATH fds, for example, are not FACS-managed (covered in [Special cases](~peios/file-access/special-cases)).

## What operations consult the cache

Almost every operation on a FACS-managed fd checks the cached mask. The rule: the operation has a *required access mask* (what it needs the caller to have been granted at open) and succeeds only if `required & ~granted == 0` — every required bit is in the granted mask.

| Operation | Required access |
|---|---|
| `read` | `FILE_READ_DATA` |
| `pread`, `readv`, `process_vm_readv` (when reading from the fd as target) | Same |
| `write` | `FILE_WRITE_DATA` |
| `pwrite`, `writev` | Same |
| Append-only write (RWF_APPEND, O_APPEND) | `FILE_APPEND_DATA` (without requiring `FILE_WRITE_DATA`) |
| `ftruncate` | `FILE_WRITE_DATA` |
| `fchmod` | `FILE_WRITE_ATTRIBUTES` |
| `fchown` | `WRITE_OWNER` (technically: the fchown is rejected entirely on FACS-managed fds; see Special cases) |
| `mmap(PROT_READ)` | `FILE_READ_DATA` |
| `mmap(PROT_WRITE)` | `FILE_WRITE_DATA` |
| `mmap(PROT_EXEC)` | `FILE_EXECUTE` |
| `fstat` | `FILE_READ_ATTRIBUTES` |
| `fgetxattr` | `FILE_READ_EA` (for ordinary xattrs; the security namespace is unconditionally denied) |
| `fsetxattr` | `FILE_WRITE_EA` (same exception) |
| `fdatasync`, `fsync` | None — these are control operations, not data operations |
| `flock`, `fcntl(F_SETLK)` | None |

Each operation knows what it requires; the kernel compares against the cached mask and decides.

A subtle case: **the operation's required mask comes from the operation's semantics, not from POSIX flags**. A `read()` on a fd opened O_RDONLY needs `FILE_READ_DATA` because read needs FILE_READ_DATA, not because the fd was opened with O_RDONLY. The two coincide because `open(O_RDONLY)` requested and got FILE_READ_DATA, but the per-operation check is on what the operation needs, not on what the open requested.

## Immutability and why

The cached granted mask **cannot change** after open. The kernel does not provide a syscall to refresh it. Modifying the file's DACL does not propagate to existing fds. Adjusting the calling token's privileges does not retroactively re-grant rights on previously-opened fds.

The reasoning is two-fold:

**Atomic policy.** A long-running operation should not change behaviour partway through. A backup tool that opens a file at time T should be able to complete the read at time T+1 even if the DACL was modified between. Either the right to read was granted at open (in which case the read should succeed) or it wasn't (in which case the open should have failed).

**Performance.** Caching is the whole point. If the kernel re-evaluated AccessCheck on every read, the handle model would not give any of the performance benefit. The cache is what makes the model work.

The implication: a DACL update is **observable only to new opens**. Existing handles continue with the rights they had. To force a policy change to take effect, the operator must either close existing handles (or kill the processes holding them) or wait for the handles to be released naturally.

## fd transfer preserves the mask

A file descriptor can be transferred between processes — via `dup`, fork, SCM_RIGHTS, exec, pidfd_getfd. In every case, the transfer preserves the granted access mask exactly.

A fd passed via SCM_RIGHTS to another process gives that process the same access the originating process had through the fd. The recipient's token is not re-checked at transfer; the granted mask is what counts.

This is intentional. Capabilities are passable. A process that opened a file with broad rights can hand the fd to a helper process; the helper inherits the rights even if the helper's own token would not have granted them.

The model is: *opening a file produces a capability (the fd + the cached mask), and capabilities are transferable*. The transfer is the way the model expects rights to be delegated.

The corollary: a process should be careful about which fds it shares. Passing a fd to a less-trusted helper grants that helper the rights the fd carries. There is no narrowing-at-transfer mechanism.

A more restrictive variant — handing off only some of the access rights — requires opening a fresh fd with the narrower set. The original fd holder, who presumably has the broader set, can open the file again with a narrower mask and pass that fd.

## fork and exec

`fork` copies the file table; all fds are inherited by the child along with their cached masks. The child has the same rights on the same files as the parent at the moment of fork.

`exec` (with no special flags) preserves the file table; fds carry over to the new program with their cached masks intact.

`exec` with `FD_CLOEXEC` set on a fd causes that fd to be closed at exec; the child program does not inherit it. This is the standard "close on exec" mechanism, used widely. A handle that should not survive exec gets `FD_CLOEXEC` either at open (via `O_CLOEXEC`) or later (via `fcntl(F_SETFD, FD_CLOEXEC)`).

Within the same process, threads share the file table; a fd opened in one thread is usable from any thread in the same process.

The cached mask follows the fd everywhere the fd goes.

## When the cache can be wrong

The cached mask is a snapshot at open time. There are a small number of cases where the cache may be wrong relative to the world at large:

- **The DACL was changed after open.** The cache reflects the DACL at open; the on-disk DACL may now grant different rights. New opens would get the new rights; this fd still has the old. Not a bug — the model is check-at-open.
- **The calling token's state changed.** The token's privileges may have been adjusted, the integrity level may have changed (via NEW_PROCESS_MIN at exec, say). The cached mask reflects the token at open. Operations through this fd use the cached value, not the current token state.
- **The file was deleted and replaced.** An `unlink` of the path the fd was opened against does not affect the fd; the inode remains alive as long as the fd is open. The cache still reflects what was true of the now-unlinked inode. A new file created at the same path is a different inode; the cache is unaffected.
- **Mount policy changed.** Changing the mount policy on a superblock does not retroactively affect the cached masks of fds open against files on that superblock. The cache is the snapshot; mount policy is the input to future opens.

In each case, the model's answer is the same: the cache is the truth for this fd's purposes. If you need a fresh view, close and reopen.

## Operations not subject to the cache

A handful of operations bypass the cache or use a different check:

- **`execveat(AT_EMPTY_PATH)`** is the **one exception** in v0.20. Exec re-evaluates AccessCheck rather than using the cache. The reasoning is that exec changes the calling process's identity and PSB in ways that the cached open-time decision did not account for; running a fresh check makes the exec decision honest. This is the only v0.20 use-time access check.
- **O_PATH fds** are not FACS-managed and have no cached mask. Operations against them either work unconditionally (`fstat`) or use a fresh AccessCheck (operations that need real access).
- **fchown, fchmod-equivalent operations** are denied entirely on FACS-managed fds. SD modifications go through `kacs_set_sd`, not these legacy syscalls. See [Special cases](~peios/file-access/special-cases) and [Managing file security](~peios/file-access/managing-file-security).
- **Mapping a file's data into kernel space directly** (e.g. via `splice` between two fds) involves both fds' cached masks; neither is bypassed.

The exception list is short. For the overwhelming majority of operations, the cached mask is the gate.

## Implications for processes

Knowing the handle model has practical implications for code that handles files:

**Don't expect tightening to revoke open handles.** A security incident response that revokes a permission needs to also close fds. The kernel does not.

**Open with exactly the rights you need.** A fd opened with broader rights than needed is a broader capability than needed. If something might pass the fd elsewhere, the something gets the broader rights too. Minimum-rights opens are good hygiene.

**Pass fds carefully.** A fd shared via SCM_RIGHTS is a capability transfer. Audit who you pass to and what they could do with it.

**Use FD_CLOEXEC for fds you don't want exec to inherit.** This is also a defence-in-depth measure against accidental capability leakage to child processes.

**Refreshing access requires reopening.** A program that wants to see DACL changes needs to close and reopen, not poll for changes.
