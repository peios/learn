---
title: LSM Hook Matrix
---

This is the definitive reference mapping file operations to LSM hooks and required access rights. Each entry specifies: enforcement mode (snapshot = granted mask check, live = AccessCheck against SD), the hook that fires, and the right(s) checked.

## File open and create

| Operation | Hook | Mode | Right(s) |
|---|---|---|---|
| `open()` / `openat()` | `security_file_open` | Live | Core + compat |
| `kacs_open()` with `KACS_CREATE_OPT_DELETE_ON_CLOSE` | `security_file_open` + `security_file_release` | Live at open, final-close lifecycle at release | `DELETE` on file OR `FILE_DELETE_CHILD` on parent; unlink on final close of the same handle lineage |
| `open()` with O_CREAT | `security_inode_create` + `security_inode_init_security` | Live | FILE_ADD_FILE on parent |
| `mkdir()` | `security_inode_mkdir` | Live | FILE_ADD_SUBDIRECTORY on parent |
| `mknod()` special nodes | `security_inode_mknod` | Live | FILE_ADD_FILE on parent |
| `symlink()` | `security_inode_symlink` | Live | FILE_ADD_FILE on parent + SeCreateSymbolicLinkPrivilege |
| `open_by_handle_at()` | Patch + `security_file_open` | Live | SeChangeNotifyPrivilege + open rights |

For legacy namespace creation (`open(O_CREAT)`, `mkdir`, `mknod`, and
`symlink`), the create hook authorizes the parent-directory mutation and
`security_inode_init_security` MUST stamp the new object with an inherited
file SD. Legacy Linux creation APIs carry no caller-supplied KACS SD, so the
creator-SD input is absent and the inheritance algorithm uses the current
effective token plus the parent directory SD. On a FACS-managed mount, failure
to compute or install the new SD fails the creation closed. On unmanaged
mounts, FACS does not stamp an SD.

The `security_inode_mknod` hook is in scope only for explicit special node
types: character device nodes, block device nodes, FIFOs, and pathname
socket nodes. These new objects use file SD inheritance, not directory
inheritance. Regular-file `mknod` is treated as ordinary file creation by the
Linux VFS and reaches `security_inode_create`; directory creation reaches
`security_inode_mkdir`; unsupported or unknown mknod mode types fail closed
on FACS-managed mounts.

## Data operations (snapshot)

| Operation | Hook | Right(s) |
|---|---|---|
| `read()` / `pread64()` / `readv()` | `security_file_permission` | FILE_READ_DATA |
| `write()` / `writev()` | `security_file_permission` | FILE_WRITE_DATA for non-append intent; FILE_WRITE_DATA or FILE_APPEND_DATA for `O_APPEND` |
| `pwrite64()` | Patch + `security_file_permission` | FILE_WRITE_DATA unless `O_APPEND` makes the effective write append-only |
| `pwritev()` / `pwritev2()` | Patch + `security_file_permission` | FILE_WRITE_DATA for explicit offsets or `RWF_NOAPPEND`; FILE_WRITE_DATA or FILE_APPEND_DATA for `O_APPEND` / `RWF_APPEND` |
| `readdir` / `getdents` | `security_file_permission` | FILE_LIST_DIRECTORY |
| `sendfile()` | `security_file_permission` (both fds) | FILE_READ_DATA / FILE_WRITE_DATA |
| `copy_file_range()` | `security_file_permission` (both fds) | FILE_READ_DATA / FILE_WRITE_DATA |
| `splice()` | `security_file_permission` | FILE_READ_DATA or FILE_WRITE_DATA |
| io_uring read | `security_file_permission` | FILE_READ_DATA |
| io_uring write | Patch + `security_file_permission` | FILE_WRITE_DATA for explicit offsets or `RWF_NOAPPEND`; FILE_WRITE_DATA or FILE_APPEND_DATA for `O_APPEND` / `RWF_APPEND` |
| AIO write | Patch + `security_file_permission` | FILE_WRITE_DATA for offsets or `RWF_NOAPPEND`; FILE_WRITE_DATA or FILE_APPEND_DATA for `O_APPEND` / `RWF_APPEND` |

## Truncate and allocate (snapshot)

| Operation | Hook | Right(s) |
|---|---|---|
| `ftruncate()` | `security_file_truncate` | FILE_WRITE_DATA |
| `truncate()` | `security_inode_setattr` | Live: FILE_WRITE_DATA |
| `fallocate()` extend | `security_file_permission` | FILE_WRITE_DATA or FILE_APPEND_DATA |
| `fallocate()` mutation modes (`PUNCH_HOLE`, `ZERO_RANGE`, `COLLAPSE_RANGE`, `INSERT_RANGE`, `UNSHARE_RANGE`, `WRITE_ZEROES`) | Patch | FILE_WRITE_DATA |

## Memory mapping (snapshot)

| Operation | Hook | Right(s) |
|---|---|---|
| `mmap()` PROT_READ | `security_mmap_file` | FILE_READ_DATA |
| `mmap()` PROT_WRITE + MAP_SHARED | `security_mmap_file` | FILE_WRITE_DATA |
| `mmap()` PROT_WRITE + MAP_PRIVATE | `security_mmap_file` | FILE_READ_DATA |
| `mmap()` PROT_EXEC | `security_mmap_file` | FILE_EXECUTE |
| `mprotect()` | `security_file_mprotect` | Same as mmap for new flags |

## Metadata fd-based (snapshot, kernel patches)

| Operation | Hook | Right(s) |
|---|---|---|
| `fstat()` / fd `statx()` | Patch: fd metadata helper before `vfs_getattr` | FILE_READ_ATTRIBUTES |
| `fstatfs()` / `fstatfs64()` | Patch: fd metadata helper before `vfs_statfs` | FILE_READ_ATTRIBUTES |
| fd `file_getattr` | Patch: fd metadata helper before `vfs_fileattr_get` | FILE_READ_ATTRIBUTES |
| fd `file_setattr` | Patch: fd metadata helper before `vfs_fileattr_set` | FILE_WRITE_ATTRIBUTES |
| `fchmod()` | Patch: `security_file_setattr` | WRITE_DAC |
| `fchown()` | Patch: `security_file_setattr` | WRITE_OWNER |
| `futimens()` | Patch: `security_file_setattr` | FILE_WRITE_ATTRIBUTES |
| `fgetxattr()` | Patch: `security_file_getxattr` | FILE_READ_EA (SD xattr: deny) |
| `fsetxattr()` / `fremovexattr()` | Patch: `security_file_setxattr` | FILE_WRITE_EA (SD/POSIX ACL xattr: deny) |
| `flistxattr()` | `security_inode_listxattr` | Unconditional |

## Metadata path-based (live)

| Operation | Hook | Right(s) |
|---|---|---|
| `stat()` / `lstat()` | `security_inode_getattr` | FILE_READ_ATTRIBUTES |
| path `file_getattr` | `security_inode_file_getattr` | FILE_READ_ATTRIBUTES |
| path `file_setattr` | `security_inode_file_setattr` | FILE_WRITE_ATTRIBUTES |
| `chmod()` / `fchmodat()` | `security_inode_setattr` | WRITE_DAC |
| `chown()` / `lchown()` | `security_inode_setattr` | WRITE_OWNER |
| `utimensat()` / `utimes()` | `security_inode_setattr` | FILE_WRITE_ATTRIBUTES |
| `getxattr()` / `lgetxattr()` | `security_inode_getxattr` | FILE_READ_EA (SD xattr: deny) |
| `setxattr()` / `lsetxattr()` | `security_inode_setxattr` | FILE_WRITE_EA (SD/POSIX ACL: deny) |
| `removexattr()` | `security_inode_removexattr` | FILE_WRITE_EA (SD: deny) |
| `listxattr()` / `llistxattr()` | `security_inode_listxattr` | Unconditional |
| `access()` / `faccessat()` | Patch + `security_inode_permission` | Live AccessCheck: R_OK → FILE_READ_DATA, W_OK → FILE_WRITE_DATA, X_OK → FILE_EXECUTE. F_OK (existence) → FILE_READ_ATTRIBUTES. Uses the effective token (not real credential). |

## Link operations (live)

| Operation | Hook | Right(s) |
|---|---|---|
| `link()` / `linkat()` | `security_inode_link` | FILE_ADD_FILE on dest parent + FILE_WRITE_ATTRIBUTES on source file |
| `unlink()` | `security_inode_unlink` | DELETE on file OR FILE_DELETE_CHILD on parent |
| `rmdir()` | `security_inode_rmdir` | DELETE on dir OR FILE_DELETE_CHILD on parent |
| `rename()` plain | `security_inode_rename` | (DELETE on source OR FILE_DELETE_CHILD on source parent) + (FILE_ADD_FILE or FILE_ADD_SUBDIRECTORY) on dest parent |
| `rename()` overwrite | `security_inode_rename` | Same as plain + (DELETE on existing dest OR FILE_DELETE_CHILD on dest parent) |
| `renameat2(NOREPLACE)` | `security_inode_rename` | Same as plain when the target is absent. If the target exists, Linux rejects the operation before KACS needs to authorize destination deletion. |
| `renameat2(EXCHANGE)` | `security_inode_rename` | (DELETE on each file OR FILE_DELETE_CHILD on its parent) + (FILE_ADD_FILE or FILE_ADD_SUBDIRECTORY) on each parent |
| `renameat2(WHITEOUT)` | Patch before `security_inode_rename` | Unsupported for FACS-managed namespaces in v0.20; fail closed with `-EOPNOTSUPP`. Unmanaged mounts remain outside FACS. |
| `readlink()` | `security_inode_readlink` | FILE_READ_DATA on symlink |

### Link operation semantics

**DELETE / FILE_DELETE_CHILD duality.** For `unlink()`, `rmdir()`, and the source side of `rename()`, the required right can be satisfied two ways: DELETE on the target's own SD, or FILE_DELETE_CHILD on the parent directory's SD. These are alternative gates checked against different SDs. The implementation checks the target file's SD for DELETE first; if denied, it checks the parent directory's SD for FILE_DELETE_CHILD. If neither grants the right, the operation is denied.

**SD preservation on rename.** A renamed file retains its existing SD. The inheritance algorithm does not re-execute when a file moves to a new directory. This matches Windows: moving a file does not change its DACL unless an administrator explicitly re-propagates inheritance.

**Sticky bit.** The Linux sticky bit (restricted deletion flag) is a DAC concept. Under KACS, DAC is neutralized. FILE_DELETE_CHILD on the parent directory's SD is the sole gate for child deletion. The sticky bit has no effect under FACS.

**link() FILE_WRITE_ATTRIBUTES.** Creating a hardlink modifies the source inode's metadata (link count increments, ctime updates). FILE_WRITE_ATTRIBUTES on the source file's SD authorizes this mutation. This also prevents unauthorized hardlink creation to files the caller cannot modify -- a defense against hardlink-based attacks where an attacker creates a link to a privileged file in a directory they control.

**Cross-mount rename.** Linux returns `-EXDEV` for rename across mount boundaries. The VFS rejects the operation before the LSM hook fires. Not a KACS concern.

## Execution

| Operation | Hook | Right(s) |
|---|---|---|
| `execve()` | `security_bprm_check` | Live: FILE_EXECUTE |
| `execveat(AT_EMPTY_PATH)` | `security_bprm_check` | Live AccessCheck for FILE_EXECUTE on the re-opened file. Future versions will check the fd's granted mask directly (snapshot mode). |
| `fexecve()` | `security_bprm_check` | Same as execveat. |

## Directory traversal

| Operation | Hook | Right(s) |
|---|---|---|
| Path resolution | `security_inode_permission` | FILE_TRAVERSE on intermediate directory components (skipped if SeChangeNotifyPrivilege held) |
| `chdir()` / `chroot()` final directory | `security_inode_permission` | Live: FILE_TRAVERSE |
| `fchdir()` normal fd | `security_file_permission` | Snapshot: FILE_TRAVERSE |
| `fchdir()` O_PATH fd | `security_inode_permission` | Live: FILE_TRAVERSE |

## Locking (snapshot)

| Operation | Hook | Right(s) |
|---|---|---|
| `flock(LOCK_SH)` / `F_RDLCK` | `security_file_lock` | FILE_READ_DATA |
| `flock(LOCK_EX)` / `F_WRLCK` | `security_file_lock` | FILE_WRITE_DATA or FILE_APPEND_DATA |

## Unix sockets (live)

Pathname sockets are protected via the socket file's inode SD (handled by FACS through the normal file open path). Abstract sockets store their SD on the socket's LSM security blob, stamped at `bind()` time from the binding thread's effective token.

| Operation | Hook | Right(s) |
|---|---|---|
| `bind()` abstract socket | `security_socket_bind` | Stamps SD on socket blob from caller's token. |
| `connect()` Unix stream | `security_unix_stream_connect` | AccessCheck: FILE_WRITE_DATA on socket SD. |
| `sendto()` / `sendmsg()` Unix dgram | `security_unix_may_send` | AccessCheck: FILE_WRITE_DATA on socket SD. |

The datagram hook authorizes sends to abstract sockets only; it does not
capture a persistent KACS peer token. Datagram sockets, socketpair-created
sockets, and ancillary credential messages (`SCM_CREDENTIALS` /
`SCM_SECURITY`) are not KACS peer-token authorities in `v0.20`.
`kacs_open_peer_token` and `kacs_impersonate_peer` fail closed unless the
socket already carries a KACS peer token from the stream/seqpacket connect
path.

`socketpair()` creates unnamed connected sockets. Access to those sockets is
fd possession, and no socket SD or KACS peer token is installed by
`socketpair()` in `v0.20`.

## IPC (live)

| Operation | Hook | Right(s) |
|---|---|---|
| `ioctl()` / compat `ioctl()` | `security_file_ioctl` / `security_file_ioctl_compat` | Enforce classified ioctl rights and unclassified data-right fallback on FACS-managed fds; unmanaged fds stay outside FACS. |
| `fcntl()` | `security_file_fcntl` | Enforce classified fcntl command rights against cached grants on FACS-managed fds; fd-local commands require no extra right; lock/lease/delegation acquisition reaches `security_file_lock`; unknown managed commands fail closed. |
| fd transfer via `SCM_RIGHTS` | `security_file_receive` | Unconditional allow (possession is authorization). |

`SCM_CREDENTIALS` and `SCM_SECURITY` remain Linux compatibility metadata in
`v0.20`; they do not carry a KACS token handle, do not install a socket
`peer_token`, and do not authorize impersonation.

## Miscellaneous

| Hook | Purpose |
|---|---|
| `security_inode_follow_link` | Unconditional allow. Registered for auditability. |
| `security_inode_set_acl` | Deny POSIX ACL creation. KACS replaces POSIX ACLs. |
| `security_inode_remove_acl` | Deny POSIX ACL removal. KACS replaces POSIX ACLs. |
| `security_inode_xattr_skipcap` | Skip native security-xattr capability prechecks so KACS/FACS metadata hooks are authoritative. Non-empty `security.capability` installation remains denied by the dead `CAP_SETFCAP` policy. |
| `security_inode_getsecurity` | Return SD bytes via the inode security interface. |

## Process mitigation enforcement

Mitigation setting is also an enforcement point. `kacs_set_psb` MUST perform the activation-backed transaction defined by §5.2 before committing newly requested mitigation bits.

| Mitigation | Hook | Enforcement |
|---|---|---|
| WXP | `kacs_set_psb`, `security_mmap_file`, `security_file_mprotect` | At set time, verify existing mappings do not violate WXP. After commitment, reject W+X mappings and W↔X transitions. Applies to ALL mappings including anonymous (not just file-backed). `security_file_mprotect` fires for anonymous mprotect with `file=NULL`. |
| TLP | `kacs_set_psb`, `security_mmap_file`, `security_file_mprotect` | At set time, verify existing file-backed executable mappings are inside approved directory prefixes. After commitment, reject PROT_EXEC on files outside approved directory prefixes. Enforced at both mmap and mprotect (prevents mmap-without-exec then mprotect-to-exec bypass). Checked before LSV. |
| LSV | `kacs_set_psb`, `security_mmap_file`, `security_file_mprotect` | At set time, verify existing file-backed executable mappings have acceptable signatures. After commitment, verify binary signature and reject if unsigned or insufficiently trusted. Checked after TLP (TLP is a fast path rejection). |
| PIE | `security_bprm_check` | Reject ET_EXEC (non-PIE) ELF binaries at exec time. |
| CFIF | `kacs_set_psb`, `security_task_prctl` | At set time, enable and lock hardware indirect-branch tracking where supported. After commitment, block disabling of hardware indirect-branch tracking (Intel IBT). |
| CFIB | `kacs_set_psb`, `security_task_prctl` | At set time, enable and lock hardware shadow stack where supported. After commitment, block disabling of hardware shadow stack (Intel CET). |
| SML | `kacs_set_psb`, `security_task_prctl` | At set time, enable the strictest supported speculation mitigations. After commitment, block process requests that would disable those mitigations. |
| `no_child_process` | `security_task_alloc` | Reject fork (but not CLONE_THREAD) when flag is set. |

## Credential management

| Hook | Purpose |
|---|---|
| `security_prepare_creds` | Assert mandatory ALLOW/DAC-bypass capabilities on new credentials, including prepared exec credentials created before binary-specific hooks run. |
| `security_transfer_creds` | Transfer token reference on credential transfer. |
| `security_cred_alloc_blank` | Allocate blank credential blob. |
| `security_cred_free` | Free token reference on credential destruction. |
| `security_bprm_creds_for_exec` | No distinct KACS transition is required when `security_prepare_creds` has already asserted the mandatory capability substrate on `bprm->cred`; implementations MAY register this hook only to defensively reassert that invariant. |
| `security_bprm_creds_from_file` | Suppress file capabilities and reinterpret setuid/setgid-bit handling under the KACS compatibility rules: cosmetic Linux-credential mutation without `SeAssignPrimaryTokenPrivilege`, full identity swap with it. |
| `security_capget` | Report mandatory ALLOW capability substrate and enforce `PROCESS_QUERY_INFORMATION` plus PIP dominance for cross-process `capget(pid)`. This MAY be implemented by a KACS hook or by patching the active capability LSM provider's `capget` implementation, provided every `security_capget` call reaches the KACS capget decision before results are returned. |
| `security_capset` | Deny any credential-set mutation that would clear DAC-bypass capabilities. Non-ALLOW mutations remain compatibility-only state. |
| `security_capable` | Authoritative capability answer: map Linux capabilities to KACS privileges or DAC bypass. |
| `security_task_prctl` | Deny ambient-capability or bounding-set mutations that would clear DAC-bypass capabilities. |
| `security_task_fix_setuid` | Suppress or intercept setuid-family calls. |
| `security_task_fix_setgid` | Suppress or intercept setgid-family calls. |

## Process lifecycle

| Hook | Purpose |
|---|---|
| `security_task_alloc` | Allocate PSB, inherit PIP/mitigations, create process SD. |
| `security_task_free` | Free PSB and process SD. |
| `security_task_kill` | Enforce process SD + PIP dominance on signal delivery. |
| `security_ptrace_access_check` | Enforce process SD + PIP dominance on ptrace, and on patched `pidfd_getfd()` / `pidfd_open()` mode distinctions. |
| `security_ptrace_traceme` | Enforce process SD `PROCESS_VM_WRITE` + PIP dominance when another process is nominated as tracer by `PTRACE_TRACEME`. |
| `security_task_setnice` | Enforce process SD (`PROCESS_SET_INFORMATION`) + PIP for changes targeting another process. Self-targeted changes are not process-boundary operations and bypass this gate. |
| `security_task_setscheduler` | Same as `task_setnice`. |
| `security_task_setioprio` | Same as `task_setnice`. |
| `security_task_setpgid` | Enforce process SD (`PROCESS_SET_INFORMATION`) + PIP for process-group changes targeting another process security state. |
| `security_task_getpgid` | Enforce process SD (`PROCESS_QUERY_LIMITED`) + PIP for process-group queries targeting another process security state. |
| `security_task_getsid` | Enforce process SD (`PROCESS_QUERY_LIMITED`) + PIP for session queries targeting another process security state. |
| `security_task_getscheduler` | Enforce process SD (`PROCESS_QUERY_INFORMATION`) + PIP for scheduler, affinity, and timer-slack queries targeting another process security state. |
| `security_task_getioprio` | Enforce process SD (`PROCESS_QUERY_INFORMATION`) + PIP for I/O-priority queries targeting another process security state. |
| `security_task_movememory` | Enforce process SD (`PROCESS_SET_INFORMATION`) + PIP for target memory-placement mutations. |
| patched `sched_setaffinity()` path | Enforce `SeIncreaseBasePriorityPrivilege` plus process SD (`PROCESS_SET_INFORMATION`) + PIP for affinity changes targeting another process. Same-process thread changes bypass the process-boundary gate; kernel affinity-validity rules remain in force. |
| `security_task_prlimit` | Enforce process SD + PIP on `prlimit` targeting another process: read-only operations require `PROCESS_QUERY_INFORMATION`; limit-changing operations require `PROCESS_SET_INFORMATION`. Self-targeted operations are not process-boundary operations and bypass this gate. |
| patched target-resolved `perf_event_open()` path | Enforce `SeProfileSingleProcessPrivilege` for target-specific perf. For perf events targeting another process, also enforce process SD (`PROCESS_QUERY_INFORMATION`) + PIP. Same-process thread targets bypass only the process-boundary gate; CPU-wide and cgroup perf modes remain governed by Linux's native perf permission model in `v0.20`. |
| patched `/proc/<pid>` metadata read paths | Enforce process SD + PIP on non-ptrace-gated procfs metadata reads. Basic metadata uses `PROCESS_QUERY_LIMITED`; detailed scheduler, namespace, timer, OOM, fault-injection, dumpability, and mitigation metadata uses `PROCESS_QUERY_INFORMATION`. |
| patched `/proc/<pid>` mutation paths | Enforce process SD (`PROCESS_SET_INFORMATION`) + PIP on procfs writes that mutate target process state, and enforce both read/write intent on coupled procfs seq-file opens. |

## Socket lifecycle

| Hook | Purpose |
|---|---|
| `security_sk_alloc` | Allocate socket security blob. |
| `security_sk_free` | Free socket security blob. |
| `security_socket_bind` | Stamp abstract socket SD at bind time. |
